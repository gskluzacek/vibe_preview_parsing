"""Run the corpus measurement scripts.

    python3 -I tools/analysis/run.py                 # all topics
    python3 -I tools/analysis/run.py items           # one topic (loaders first)
    python3 -I tools/analysis/run.py tokens s3 rare  # one script, extra args passed on
    python3 -I tools/analysis/run.py --list
    python3 -I tools/analysis/run.py --check         # compare OUT_DIR/*/*.out with expected/

Each script runs with its output directory (OUT_DIR/<topic>/) as the working
directory, so the pickles it reads/writes live there and not in the repo.
Printed output is captured to OUT_DIR/<topic>/<script>.out and echoed to a
summary line. Paths come from config.py (environment variables override).
"""
import os, re, runpy, shutil, sys, io, time, contextlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import config  # noqa: E402

# topic -> (loaders in order, then analysis scripts); modules/scratch not listed are skipped
MANIFEST = {
    'lines':    ([], [f'p{i}' for i in range(1, 22)]),
    'items':    (['a', 'c', 'e', 'f'], ['b', 'd', 'g', 'h', 'i', 'j', 'k', 'l']),
    'headings': (['ex', 'ld'], ['a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7', 't']),
    'tokens':   (['load'], [f's{i}' for i in range(1, 13)]),
}
# inputs each topic needs
NEEDS = {
    'lines': ('COF_DIR', 'OLD_COF_DIR'),
    'items': ('COF_DIR',),
    'headings': ('COF_DIR',),
    'tokens': ('COF_DIR',),
}


def run_script(topic, name, args=()):
    src = os.path.join(HERE, topic, name + '.py')
    out_dir = os.path.join(config.OUT_DIR, topic)
    os.makedirs(out_dir, exist_ok=True)
    cwd = os.getcwd()
    saved_path = list(sys.path)
    sys.path.insert(0, os.path.join(HERE, topic))
    saved_argv = sys.argv
    sys.argv = [src, *args]
    buf = io.StringIO()
    t0 = time.time()
    status = 'ok'
    try:
        os.chdir(out_dir)
        with contextlib.redirect_stdout(buf):
            runpy.run_path(src, run_name='__main__')
    except SystemExit:
        pass
    except Exception as e:  # keep going; report at the end
        status = f'FAILED: {type(e).__name__}: {e}'
    finally:
        os.chdir(cwd)
        sys.argv = saved_argv
        sys.path[:] = saved_path
    with open(os.path.join(out_dir, name + '.out'), 'w', encoding='utf-8') as f:
        f.write(buf.getvalue())
    print(f'  {topic}/{name:<4} {status}  ({time.time()-t0:.1f}s, {len(buf.getvalue())} bytes out)')
    return status == 'ok'


def run_topic(topic):
    problems = config.check(NEEDS[topic])
    if topic == 'headings':
        problems += config.check(('HEADING_EXTRACT',))
    if problems:
        print(f'[{topic}] skipped:\n  ' + '\n  '.join(problems))
        return False
    print(f'[{topic}]')
    out_dir = os.path.join(config.OUT_DIR, topic)
    os.makedirs(out_dir, exist_ok=True)
    if topic == 'headings':
        # committed copy of the 2016 heading table; ld.py regenerates it if the dump is present
        shutil.copy(os.path.join(HERE, 'headings', 'hdg_lvls.json'), os.path.join(out_dir, 'hdg_lvls.json'))
    loaders, rest = MANIFEST[topic]
    ok = True
    for name in loaders + rest:
        if topic == 'headings' and name == 'ld' and config.check(('DUMP_SQL',)):
            print('  headings/ld  skipped (dump not found; using committed hdg_lvls.json)')
            continue
        ok = run_script(topic, name) and ok
    return ok


def check_expected():
    """Compare captured outputs with the committed baseline in expected/."""
    bad = missing = same = 0
    for topic in MANIFEST:
        exp_dir = os.path.join(HERE, 'expected', topic)
        if not os.path.isdir(exp_dir):
            continue
        for name in sorted(os.listdir(exp_dir)):
            got = os.path.join(config.OUT_DIR, topic, name)
            if not os.path.exists(got):
                print(f'  MISSING {topic}/{name} (run the topic first)'); missing += 1; continue
            if open(got, 'rb').read() == open(os.path.join(exp_dir, name), 'rb').read():
                same += 1
            else:
                print(f'  DIFFERS {topic}/{name}'); bad += 1
    print(f'{same} identical, {bad} differ, {missing} missing')
    return 0 if bad == 0 and missing == 0 else 1


def main(argv):
    if argv[:1] == ['--check']:
        return check_expected()
    if argv[:1] == ['--list']:
        for t, (l, r) in MANIFEST.items():
            print(f'{t}: loaders={l} scripts={r}')
        return 0
    if len(argv) >= 2:
        topic, name = argv[0], argv[1]
        if topic not in MANIFEST:
            print('unknown topic', topic); return 2
        bad = config.check(NEEDS[topic])
        if bad:
            print('\n'.join(bad)); return 2
        return 0 if run_script(topic, name, argv[2:]) else 1
    topics = argv or list(MANIFEST)
    ok = True
    for t in topics:
        if t not in MANIFEST:
            print('unknown topic', t); return 2
        ok = run_topic(t) and ok
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
