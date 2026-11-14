"""List which COF files the Internet Archive holds. Reads the index; downloads only a sample of listing pages.

    python3 -I tools/acquire/lister.py index      # query the CDX index (one request per URL pattern)
    python3 -I tools/acquire/lister.py listing    # sample captures of the CustomerOrderForms page, extract links
    python3 -I tools/acquire/lister.py manifest   # raw index -> manifest.csv (+ listing_links.csv)
    python3 -I tools/acquire/lister.py report     # per-month coverage, written to report.txt
    python3 -I tools/acquire/lister.py all        # index, manifest, report (listing is optional)

Stages are re-runnable. Raw responses are kept under OUT_DIR/raw and never edited; the manifest and
report are rebuilt from them. No COF file is downloaded by this tool.
"""
import csv
import datetime
import html.parser
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # needed under python3 -I
import config           # noqa: E402
import cof_urls         # noqa: E402
import wayback          # noqa: E402

RAW_CDX = os.path.join(config.OUT_DIR, 'raw', 'cdx')
RAW_LISTING = os.path.join(config.OUT_DIR, 'raw', 'listing')
MANIFEST = os.path.join(config.OUT_DIR, 'manifest.csv')
LINKS = os.path.join(config.OUT_DIR, 'listing_links.csv')
REPORT = os.path.join(config.OUT_DIR, 'report.txt')
MANIFEST_COLS = ['month', 'kind', 'era', 'timestamp', 'original', 'status', 'mime', 'length', 'digest', 'plausible']


def _now():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def cmd_index():
    os.makedirs(RAW_CDX, exist_ok=True)
    for name, pattern in config.PATTERNS.items():
        header, rows = wayback.cdx(pattern)
        if len(rows) >= config.CDX_LIMIT:
            print('WARNING: %s hit the row limit (%d); results are incomplete' % (name, config.CDX_LIMIT))
        with open(os.path.join(RAW_CDX, name + '.json'), 'w') as f:
            json.dump({'pattern': pattern, 'fetched_utc': _now(), 'header': header, 'rows': rows}, f)
        print('%-22s %6d captures' % (name, len(rows)))


class _Links(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for k, v in attrs:
                if k == 'href' and v:
                    self.hrefs.append(v)


def cmd_listing():
    """Sample one capture of the listing page per LISTING_EVERY_DAYS and keep the HTML as stored."""
    os.makedirs(RAW_LISTING, exist_ok=True)
    header, rows = wayback.cdx(config.LISTING_URL)
    ix = {k: i for i, k in enumerate(header)}
    good = sorted((r[ix['timestamp']], r[ix['original']]) for r in rows
                  if r[ix['statuscode']] == '200' and r[ix['mimetype']] == 'text/html')
    chosen, last = [], None
    for ts, orig in good:
        d = datetime.datetime.strptime(ts[:8], '%Y%m%d')
        if last is None or (d - last).days >= config.LISTING_EVERY_DAYS:
            chosen.append((ts, orig))
            last = d
    print('%d usable captures, sampling %d' % (len(good), len(chosen)))
    out = []
    for ts, orig in chosen:
        path = os.path.join(RAW_LISTING, ts + '.html')
        if not os.path.exists(path):
            with open(path, 'wb') as f:
                f.write(wayback.fetch_capture(ts, orig))
        parser = _Links()
        parser.feed(open(path, 'rb').read().decode('utf-8', 'replace'))
        found = {(cof_urls.classify(h), h) for h in parser.hrefs}
        n = 0
        for c, h in sorted((x for x in found if x[0]), key=lambda x: (cof_urls.month_index(x[0].month), x[0].kind)):
            out.append({'capture': ts, 'month': c.month, 'kind': c.kind, 'href': h})
            n += 1
        print(ts, '%3d COF links' % n)
    with open(LINKS, 'w', newline='') as f:
        w = csv.DictWriter(f, ['capture', 'month', 'kind', 'href'])
        w.writeheader()
        w.writerows(out)


def _load_rows():
    rows, skipped = [], 0
    for name in config.PATTERNS:
        path = os.path.join(RAW_CDX, name + '.json')
        if not os.path.exists(path):
            print('missing %s (run: index)' % path)
            continue
        data = json.load(open(path))
        ix = {k: i for i, k in enumerate(data['header'])}
        for r in data['rows']:
            c = cof_urls.classify(r[ix['original']])
            if not c:
                skipped += 1
                continue
            mime, minlen = config.PLAUSIBLE[c.kind]
            length = int(r[ix['length']]) if r[ix['length']].isdigit() else 0
            ok = r[ix['statuscode']] == '200' and r[ix['mimetype']] == mime and length >= minlen
            rows.append({'month': c.month, 'kind': c.kind, 'era': c.era, 'timestamp': r[ix['timestamp']],
                         'original': r[ix['original']], 'status': r[ix['statuscode']], 'mime': r[ix['mimetype']],
                         'length': length, 'digest': r[ix['digest']], 'plausible': int(ok)})
    rows.sort(key=lambda r: (cof_urls.month_index(r['month']), r['kind'], r['timestamp'], r['original']))
    return rows, skipped


def cmd_manifest():
    rows, skipped = _load_rows()
    os.makedirs(config.OUT_DIR, exist_ok=True)
    with open(MANIFEST, 'w', newline='') as f:
        w = csv.DictWriter(f, MANIFEST_COLS)
        w.writeheader()
        w.writerows(rows)
    print('%d captures in manifest (%d plausible); %d index rows were not single COF files'
          % (len(rows), sum(r['plausible'] for r in rows), skipped))


def cmd_report():
    if not os.path.exists(MANIFEST):
        sys.exit('no manifest; run: manifest')
    rows = list(csv.DictReader(open(MANIFEST)))
    by = defaultdict(list)
    for r in rows:
        if r['plausible'] == '1':
            by[(r['month'], r['kind'])].append(r)
    linked = defaultdict(set)
    if os.path.exists(LINKS):
        for r in csv.DictReader(open(LINKS)):
            linked[(r['month'], r['kind'])].add(r['capture'][:4])
    months = cof_urls.months_between(config.EXPECT_FROM, config.EXPECT_TO)
    lines = ['COF coverage %s-%s (plausible = status 200, expected MIME type and size)' % (config.EXPECT_FROM, config.EXPECT_TO), '']
    for kind in ('txt', 'pdf'):
        missing = [m for m in months if not by[(m, kind)]]
        multi = [m for m in months if len({r['digest'] for r in by[(m, kind)]}) > 1]
        eras = defaultdict(int)
        for m in months:
            for e in {r['era'] for r in by[(m, kind)]}:
                eras['era' + e] += 1
        lines += ['%s: %d of %d months have a plausible capture' % (kind.upper(), len(months) - len(missing), len(months)),
                  '  months seen per URL era: %s' % dict(sorted(eras.items())),
                  '  missing: %s' % (' '.join(missing) or 'none'),
                  '  months with more than one distinct file (compare these): %d' % len(multi),
                  '    %s' % (' '.join(multi) or 'none'), '']
    lines.append('Per month (captures / distinct files / eras), blank = none')
    lines.append('month   txt          pdf          listed-on-page-years')
    for m in months:
        cells = []
        for kind in ('txt', 'pdf'):
            c = by[(m, kind)]
            cells.append('%d/%d/%s' % (len(c), len({r['digest'] for r in c}), ''.join(sorted({r['era'] for r in c}))) if c else '')
        lis = ','.join(sorted(linked[(m, 'txt')] | linked[(m, 'pdf')]))
        lines.append('%-7s %-12s %-12s %s' % (m, cells[0], cells[1], lis))
    text = '\n'.join(lines)
    with open(REPORT, 'w') as f:
        f.write(text + '\n')
    print('\n'.join(lines[:lines.index('Per month (captures / distinct files / eras), blank = none')]))
    print('full table: %s' % REPORT)


COMMANDS = {'index': cmd_index, 'listing': cmd_listing, 'manifest': cmd_manifest, 'report': cmd_report}


def main(argv):
    if len(argv) != 2 or argv[1] not in list(COMMANDS) + ['all']:
        sys.exit(__doc__)
    if argv[1] == 'all':
        for c in ('index', 'manifest', 'report'):
            COMMANDS[c]()
    else:
        COMMANDS[argv[1]]()


if __name__ == '__main__':
    main(sys.argv)
