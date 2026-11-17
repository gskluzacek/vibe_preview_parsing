# Corpus measurement scripts

> **Legacy.** These scripts produced the numbers in `documentation/cof_format_spec.md` and are kept as they are (standard library only, no type hints). New code lives in `src/cof/` and `adhoc/` and follows the standards in `CLAUDE.md`.

The scripts that produced the numbers in `documentation/cof_format_spec.md`. They are exploratory (short, single-purpose, terse names), but they now run end to end from a config and reproduce their outputs.

## Run

```bash
python3 -I tools/analysis/run.py            # everything (~45 s on the original machine)
python3 -I tools/analysis/run.py items      # one topic: loaders first, then analyses
python3 -I tools/analysis/run.py tokens s3 rare   # one script (extra args are passed through)
python3 -I tools/analysis/run.py --list
python3 -I tools/analysis/run.py --check    # compare captured outputs with expected/
```

Tested with Python 3.13 and the standard library only (no third-party packages). A run is only "ok" in the runner's summary if the script raised no exception; use `--check` to confirm the *numbers*.

## Configuration (`config.py`)

Defaults assume the reference repos are cloned next to this one (see the root `CLAUDE.md`). Override with environment variables:

| Variable          | Default                                                 | Used by                                                                      |
|-------------------|---------------------------------------------------------|------------------------------------------------------------------------------|
| `COF_DIR`         | `../previews_parsing/cof_files`                         | all topics (135 `MMMYY.txt` files)                                           |
| `OLD_COF_DIR`     | `../previews/old_code/Preview Parsing/previews parsing` | `lines` (old-vs-new comparisons) and the default for `DUMP_SQL`              |
| `DUMP_SQL`        | `$OLD_COF_DIR/bipolar_2014_08_16.sql`                   | `headings/ld.py` (reads heading `INSERT` rows only; never the `users` table) |
| `HEADING_EXTRACT` | `../previews_parsing/headings_hrch_extract_2.txt`       | `headings` (hand-levelled JAN09 extract)                                     |
| `OUT_DIR`         | `tools/analysis/out` (gitignored)                       | pickles and captured output                                                  |

If an input is missing, the runner skips that topic and says which path is wrong. If only the dump is missing, `headings` still runs using the committed `headings/hdg_lvls.json`.

## How it works

`run.py` runs each script with `OUT_DIR/<topic>/` as its working directory, so the intermediate pickles (25–70 MB each) are written there, not into the repo, and prints are captured to `OUT_DIR/<topic>/<script>.out`. `python3 -I` is supported: `run.py` puts this directory and the topic directory on `sys.path` itself.

| Topic       | Spec § | Loaders (create)                                                       | Then                                                                                          |
|-------------|--------|------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| `lines/`    | §1–§3  | none (`common.py` has the shared file lister)                          | `p1` … `p21`                                                                                  |
| `items/`    | §4     | `a` → `rows.pkl`; `c` → `items.pkl`; `e` → `items2.pkl`; `f` → `P.pkl` | `b d g h i j k l`                                                                             |
| `headings/` | §5     | `ex` → `rec.pkl`; `ld` → `hdg_lvls.json`                               | `a1` … `a7`, `t`                                                                              |
| `tokens/`   | §6     | `load` → `rows.pkl`                                                    | `s1` … `s12` (`cls.py` is a module imported by `s3`; `h.py` is a scratch dump and is not run) |

`headings/hdg_lvls.json` (918 heading rows from the 2016 dump) is committed; regenerating it with `ld.py` gives a byte-identical file.

## Expected outputs and `--check`

`expected/<topic>/*.out` is the baseline captured from a clean run on 2026-11-13, deliberately limited to outputs ≤ 100 KB (`lines/p2` and `items/e` are large dumps and have no baseline). `--check` reports any output that differs from, or is missing against, the baseline. Two consecutive full runs produced identical output, after `headings/a3.py` was changed to print sorted sets (Python's hash randomization had changed the print order of two sets).

If a script is changed on purpose, re-run it and copy the new `.out` into `expected/`, and update the spec where its numbers change.

## Known limits

- The outputs reproduce; they have **not** been reviewed line by line against the spec. Headline figures were spot-checked (e.g. 328,797 items / 287,319 distinct texts, 2,056 distinct headings, 35,393 heading occurrences, the per-year field-count table), not every number in the spec.
- Scripts differ in quality; some have overlapping logic (`lines/p14` vs `items/*`), and the item-count predicate differs between scripts, which is why the spec quotes slightly different totals (328,795–328,801).
- Seven `lines/*.out` files committed earlier were removed: two (`p5`, `p6`) had been captured from older versions of their scripts and did not match them.
- The scripts read the corpus as bytes or Latin-1 in some places and UTF-8 in others; the spec's encoding conclusion rests on `lines/p12`–`p13` (strict UTF-8 decode of every file).
- Descriptive names, a single entry point per topic, and conversion of stable findings into parser tests (`cof_format_spec.md` §10) are still to do.

> **Legacy.** These scripts produced the numbers in `documentation/cof_format_spec.md` and are kept as they are (standard library only, no type hints). New code lives in `src/cof/` and `adhoc/` and follows the standards in `CLAUDE.md`.
