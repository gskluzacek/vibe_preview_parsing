# `cof.normalize` – stage 2: decode, check, repair and reshape the COF text files

Turns the selected original of each month (Windows-1252, UTF-16 or gzip, CRLF, with the publisher's layout quirks) into a clean table that is easy to load, plus reports of everything that was found and done. Originals are never touched.

## What it does, per month

```
selection.csv ──► decode ──► classify lines ──► detect issues ──► repair ──► patch ──► emit ──► write
(chosen file)    bytes→text   BLANK/PAGE/…       rules F*/L*/I*    fixers    config/    rows,    YYYY_MM.txt
                                                                            patches    side-car, sidecar/YYYY_MM.txt
                                                                            .yaml      ledger    reports (CSV)
```

Outputs in `data/normalized/` (full description in `documentation/normalized_cof_spec.md`):

| File                  | Content                                                                                                                                                      |
|-----------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `YYYY_MM.txt`         | the clean table: `src_line, page, section, merchandise_flag, kind, flag, sol_code, text, release_date, price_designation, price` (tab-separated, header row) |
| `sidecar/YYYY_MM.txt` | lines moved out of the table: notes, annotations, unknown lines, placeholders                                                                                |
| `issues.csv`          | every defect found, its rule, line, and whether it was fixed, open, patched or only informational                                                            |
| `summary.csv`         | one row per file: original encoding, compression, line-ending style, line counts, issue counts                                                               |
| `ledger.csv`          | every source line counted by type and fate (kept, dropped, sidecar, replaced)                                                                                |
| `idents.csv`          | what each file says about its own month, volume, issue and catalog number, compared with the file name                                                       |

Load a month with pandas: `pd.read_csv("data/normalized/2015_03.txt", sep="\t", dtype=str, keep_default_na=False)`.

## Running it

```bash
uv run cof-normalize --help
uv run cof-normalize run                      # all selected months; writes everything above
uv run cof-normalize run --months JAN13,AUG10 # only these months (reports are not rewritten)
uv run cof-normalize run --full-checks        # also run the optional rules (see below)
uv run cof-normalize rules                    # list every rule: required or optional, class, name
uv run cof-normalize detect PATH --month JAN13   # report the issues in one file, change nothing
```

Run `adhoc/select_versions.py` first if `data/originals/selection.csv` is out of date. A full run (no `--months`) also deletes output files of months that are no longer selected.

### Required and optional rules

Every rule in `config/rules.yaml` is **required** (always run) unless it has `optional: true`. Optional rules are ones that have never fired on the selected set (mixed line endings, bare carriage returns, undefined bytes, truncated gzip, empty file, invalid dates, replacement characters, unknown item layouts); `--full-checks` turns them on. To move a rule between the sets, add or remove that one key; nothing else changes. Selection and analysis (`adhoc/`) always use all rules.

### Adding a reviewed fix

For an open issue that needs a human decision (for example restoring a damaged character) add an entry to `config/patches.yaml` (`month`, `line`, `old`, `new`, `reason`). The patch applies only if the line still equals `old`, so a stale patch fails the run instead of going unnoticed.

## How the code works

Entry point: `cli.py`. The `cof-normalize` command is declared in `pyproject.toml` as `cof.normalize.cli:app`; `app` is a **typer** application whose `@app.command()` functions (`run`, `rules`, `detect`) call `pipeline.run_pipeline` and the rule registry.

| Module         | Role                                                                                                                                                                                                                                                                       |
|----------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `decode.py`    | bytes → text: gzip detection and recovery, encoding detection (UTF-16 BOM, UTF-8 BOM, ASCII, strict UTF-8, else Windows-1252), line-ending style; records the facts for `summary.csv`                                                                                      |
| `classify.py`  | gives every line a `LineType`: `BLANK`, `PAGE`, `NOTE`, `IDENT`, `ITEM`, `FOOTER`, `ANNOTATION`, `HEADING`, `UNKNOWN` (first matching rule wins)                                                                                                                           |
| `context.py`   | `FileContext` (decoded + classified file, the input of every detector) and `Issue`                                                                                                                                                                                         |
| `rules.py`     | the **rule registry**: `Rule` (a pydantic model for one entry of `config/rules.yaml`), `load_rules()`, the `@detector("I05")` decorator that registers a function under a rule id, `detect_all()`, and `rule_param()` for tunable numbers (for example `L03`'s `max_jump`) |
| `detectors.py` | one function per rule (importing the module registers them all); `tests/normalize/test_rules.py` keeps YAML and detectors in step                                                                                                                                          |
| `items.py`     | item-line structure: layouts A–D, known flags, regular expressions for sol codes, prices and dates                                                                                                                                                                         |
| `ident.py`     | parse ident lines (variants A, B, C, D), compute the values implied by a file name, build the canonical ident line, compare                                                                                                                                                |
| `fixers.py`    | the automatic structural repairs (one `Change` recorded per repair); the output is the repaired source lines, one per source line                                                                                                                                          |
| `emit.py`      | the final shape: rows with `src_line`, `page`, `section`, `kind`; whitespace, date, price and sol-code transforms; side-car routing; the ledger; rendering to TSV                                                                                                          |
| `normalize.py` | `normalize_file`: runs the stages for one file, applies patches, and **verifies the post-conditions** (nothing repairable left, repair is stable, every source line is in the ledger, the table reads back). A failed check raises `NormalizationError`                    |
| `pipeline.py`  | `run_pipeline`: loops over `selection.csv`, writes the files and CSV reports                                                                                                                                                                                               |

Key ideas for newcomers:

- **Detect, then fix, then check.** Detectors (rules) only report. Fixers repair what a rule's class allows (`auto-lossless`, `auto-derived`). After repair the detectors run again on the result; an automatically repaired rule that still fires is a bug, and the run stops.
- **Standard transforms vs issues.** UTF-8, LF, whitespace collapsing, quote removal, date and price reformatting and the sol-code rewrite are done to every file and are not defects; real publisher defects (a missing field, a wrong ident month, an unknown flag) are issues with a rule id.
- **Page, section, kind.** PAGE lines are dropped; their number is copied to the rows that follow. `section` increases whenever the page number goes backwards (the catalog restarts its numbering several times). `merchandise_flag` is 1 after a `PAGE M-n` line (APR18 onward). `kind` is `D` (ident), `H` (heading) or `I` (item).
- **Derived ident.** The file name is the authority for month, year, volume, issue and catalog number (volume = year − 1990, catalog = (volume − 1) × 12 + month + 27). The first `PREVIEWS #nnn` item names the issue two months ahead and serves as a cross-check.
- **Typer / pydantic / YAML.** typer builds the CLI from type hints; pydantic validates `rules.yaml` entries (`Rule`) so a misspelled key fails loudly; YAML holds the editable rule metadata, Python holds the detectors.
- **Deterministic.** No timestamps in outputs; the same input and rules give identical bytes.

## Tests

`tests/normalize/` mirrors the modules (`test_emit.py` for the table, `test_normalize.py` for post-conditions, `test_detectors.py` for each rule, `test_spec_table.py` for the rule table in the spec). `uv run pytest tests/normalize`.
