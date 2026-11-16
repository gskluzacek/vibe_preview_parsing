"""Download COF files from the Internet Archive, one per distinct content version, and verify them.

    python3 -I tools/acquire/fetch.py --pilot                       # the pilot set from config.py
    python3 -I tools/acquire/fetch.py --months JAN13,AUG10 --kinds txt
    python3 -I tools/acquire/fetch.py --all [--kinds txt]           # every distinct version in the manifest
    python3 -I tools/acquire/fetch.py --pilot --dry-run             # show what would be fetched

Reads data/acquire/manifest.csv (run lister.py first). For each month and kind it takes the plausible
captures, groups them by the archive's content digest, and downloads the earliest capture of each
digest. Files are stored exactly as fetched, never edited:

    data/originals/<kind>/<MMMYY>/<digest>_<timestamp>.<ext>
    data/originals/downloads.csv        one row per file: where it came from, sizes, checks

Each file is checked against the archive's digest (base32 SHA-1 of the bytes). A file that fails is kept
and flagged in the log, not silently dropped. Existing verified files are skipped, so reruns are safe.
"""
import argparse
import base64
import csv
import datetime
import hashlib
import os
import sys
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # needed under python3 -I
import config      # noqa: E402
import cof_urls    # noqa: E402
import wayback     # noqa: E402

MANIFEST = os.path.join(config.OUT_DIR, 'manifest.csv')
LOG = os.path.join(config.ORIGINALS_DIR, 'downloads.csv')
LOG_COLS = ['month', 'kind', 'era', 'digest', 'timestamp', 'original', 'path', 'bytes', 'sha256',
            'digest_ok', 'content_ok', 'fetched_utc']


def archive_digest(data):
    """The archive's digest: base32 of the SHA-1 of the stored bytes."""
    return base64.b32encode(hashlib.sha1(data).digest()).decode()


def looks_right(kind, data):
    """Cheap sanity check on content: a PDF must start with %PDF and end with %%EOF (archive copies can be
    truncated and still carry a valid digest); text must not be HTML."""
    if kind == 'pdf':
        return data[:5] == b'%PDF-' and b'%%EOF' in data[-1024:]
    head = data[:2000].lstrip().lower()
    return not head.startswith((b'<!doctype', b'<html'))


def select(rows, months, kinds):
    """Earliest plausible capture of each distinct digest, per (month, kind)."""
    chosen = OrderedDict()
    for r in rows:
        if r['plausible'] != '1' or r['month'] not in months or r['kind'] not in kinds:
            continue
        key = (r['month'], r['kind'], r['digest'])
        if key not in chosen or r['timestamp'] < chosen[key]['timestamp']:
            chosen[key] = r
    return list(chosen.values())


def _path(r):
    return os.path.join(config.ORIGINALS_DIR, r['kind'], r['month'], '%s_%s.%s' % (r['digest'], r['timestamp'], r['kind']))


def _read_log():
    rows = list(csv.DictReader(open(LOG))) if os.path.exists(LOG) else []
    for r in rows:   # older logs called this column starts_ok
        r['content_ok'] = r.pop('starts_ok', r.get('content_ok', ''))
    return rows


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--pilot', action='store_true')
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--months', help='comma-separated MMMYY list')
    ap.add_argument('--kinds', default='txt,pdf')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args(argv[1:])
    if not os.path.exists(MANIFEST):
        sys.exit('no manifest; run lister.py first')
    rows = list(csv.DictReader(open(MANIFEST)))
    if a.pilot:
        wanted = config.PILOT
    elif a.all:
        kinds = a.kinds.split(',')
        wanted = sorted({(r['month'], k) for r in rows for k in kinds}, key=lambda t: (cof_urls.month_index(t[0]), t[1]))
    elif a.months:
        wanted = [(m.upper(), k) for m in a.months.split(',') for k in a.kinds.split(',')]
    else:
        sys.exit('give --pilot, --all or --months')
    todo = []
    for month, kind in wanted:
        todo += select(rows, {month}, {kind})
    log = _read_log()
    done = {r['path'] for r in log if r['digest_ok'] == '1'}
    for x in log:   # re-check files already on disk with the current checks
        fp = os.path.join(config.ORIGINALS_DIR, x['path'])
        if os.path.exists(fp):
            x['content_ok'] = str(int(looks_right(x['kind'], open(fp, 'rb').read())))
    failed = []
    for r in todo:
        p = _path(r)
        rel = os.path.relpath(p, config.ORIGINALS_DIR)
        if rel in done and os.path.exists(p):
            print('have   ', rel, '' if [x for x in log if x['path'] == rel][0]['content_ok'] == '1' else 'CONTENT CHECK FAILED')
            continue
        if a.dry_run:
            print('would  ', rel, r['original'])
            continue
        try:
            data = wayback.fetch_capture(r['timestamp'], r['original'])
        except wayback.WaybackError as e:
            failed.append((rel, str(e)))
            print('FAILED ', rel, e)
            continue
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'wb') as f:
            f.write(data)
        ok = archive_digest(data) == r['digest']
        log = [x for x in log if x['path'] != rel]
        log.append({'month': r['month'], 'kind': r['kind'], 'era': r['era'], 'digest': r['digest'],
                    'timestamp': r['timestamp'], 'original': r['original'], 'path': rel, 'bytes': len(data),
                    'sha256': hashlib.sha256(data).hexdigest(), 'digest_ok': int(ok),
                    'content_ok': int(looks_right(r['kind'], data)),
                    'fetched_utc': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')})
        print('fetched' if ok else 'DIGEST MISMATCH', rel, len(data), 'bytes')
        _write_log(log)

    _write_log(log)
    print('%d files considered, %d failed (rerun to retry)' % (len(todo), len(failed)))
    for rel, why in failed:
        print('  ', rel)


def _write_log(log):
    if log:
        os.makedirs(config.ORIGINALS_DIR, exist_ok=True)
        with open(LOG + '.tmp', 'w', newline='') as f:   # write then rename, so a crash cannot truncate the log
            w = csv.DictWriter(f, LOG_COLS)
            w.writeheader()
            w.writerows(sorted(log, key=lambda x: (cof_urls.month_index(x['month']), x['kind'], x['timestamp'])))
        os.replace(LOG + '.tmp', LOG)


if __name__ == '__main__':
    main(sys.argv)
