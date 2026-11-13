# Corpus measurement scripts (exploratory, preserved as produced)

These are the scripts that produced the numbers in `documentation/cof_format_spec.md` (2026-11-13). They were written by four subagents during that analysis and copied here **unchanged** so the figures can be traced and, later, reproduced.

## Status: not yet reproducible as-is

- **Hard-coded absolute paths** to the sibling reference repos, e.g. `/Volumes/U34-Bolt/Personal/development/github/previews_parsing/cof_files/` and `.../previews/old_code/Preview Parsing/previews parsing/` (see `lines/common.py`, `items/a.py`, `tokens/load.py`, `headings/ex.py`, `headings/ld.py`). They only work on this machine with those repos cloned next to this one.
- **Run from inside each subdirectory.** Intermediate files (`*.pkl`, `hdg_lvls.json`) are read and written in the current directory.
- **Pickles are not committed** (25–70 MB each). Regenerate them with the loader script for each folder.
- Scripts are short, single-purpose and unreviewed; filenames are not descriptive. They have not been re-run after being copied. Treat results in the spec as "produced by these scripts once", not as tested.
- Run with `python3 -I` from the script's own directory.

## Layout and dependencies

| Folder | Topic (spec section) | Loader (creates) | Analysis scripts |
|---|---|---|---|
| `lines/` | line endings, encoding, ident, PAGE, other line types, item predicates, backups, old-vs-new repo diff (§1–§3) | none; `common.py` holds the path constants and file lister | `p1.py` … `p21.py`; `p*.out` are the captured outputs from the original run (kept as the record of the numbers) |
| `items/` | item field layouts, flags, sol code, date, price (§4) | `a.py` → `rows.pkl`; `c.py` → `items.pkl`; `e.py` → `items2.pkl`; `f.py` → `P.pkl` | `b.py`, `d.py`, `g.py`–`l.py` (read one of the pickles) |
| `headings/` | heading extraction, 2016 table, hierarchy, drift (§5) | `ex.py` → `rec.pkl`; `ld.py` → `hdg_lvls.json` (parsed from the heading `INSERT` rows only; never touches the dump's `users` table) | `a1.py` … `a7.py`, `t.py` |
| `tokens/` | `sol_text` token classes, order, first-seen months (§6) | `load.py` → `rows.pkl` | `s1.py` … `s12.py`, `cls.py`, `h.py` |

`headings/hdg_lvls.json` is committed (36 KB): the 918 heading rows (id, level, parent, flag, name, timestamp) extracted from the 2016 MySQL dump.

## To make these reproducible (not done)

1. Replace hard-coded paths with one config (env var or CLI argument) for the corpus and the 2016 dump.
2. Give scripts descriptive names and a single entry point per topic that writes its outputs to a gitignored folder.
3. Re-run them and compare with the spec's numbers; note the ±6 differences the spec mentions between item-count predicates.
4. Turn the stable findings into parser tests/fixtures (`cof_format_spec.md` §10).
