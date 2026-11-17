# Analysis: `previews_parsing_pandas` repository (2023)

Source: `../previews_parsing_pandas` (https://github.com/gskluzacek/previews_parsing_pandas), commits 2023-06-22 and 2023-07-10.
Analyzed: 2026-11-13. Treated as read-only reference material.

Method: two subagents (structure/docs/data/history, and a full read of the code) reported back; I spot-checked the tracked file list, commit log, line counts, the absence of NLP libraries (grep), and part of `cof_notes.md`. Nothing was executed. See §9 for what is unverified.

> Correction to `previous_repositories.md`: its description says this repo "potentially may use NLP". That is only a **stated intention** in `README.md` line 2. There is **no NLP code, dependency, model or labelled data** anywhere in the repo (confirmed by grep for spaCy / NLTK / scikit-learn / transformers / "NLP": the only hit is the README line).

## 1. Summary

A very small, early-stage snapshot (2 commits, one 743-line script) that re-does the 2020 pipeline with pandas over SQLite. It never gets past line typing and page numbers; the heading-hierarchy stage is unfinished and item-field splitting is not implemented. No description parsing, no results, no data files.

Its real value is **documentation of the data, not code**:

1. **`data/cof_notes/cof_notes.md` (302 lines)** — a catalogue of per-file defects in the COF text files (wrong ident-line months, missing/malformed page lines, an extra tab, a combined May/June 2020 issue) with the exact manual fixes applied. This is the most useful new artifact across the three repos for building a robust parser and a clean corpus.
2. **Newer, broader download scripts** covering JAN10 → AUG23/SEP23 (~164 files) and the PDF versions too.
3. **Encoding survey** of 164 files (charset_normalizer).
4. **README design notes** for a rebuilt system (Postgres, raw vs edited line, case/accent-insensitive search, dated heading hierarchy).
5. **Page-number conventions** (0 and −1 sentinels, `M` prefix for merchandise pages).

Not worth carrying forward: `main.py` itself.

## 2. Repository layout

18 tracked files, ~200 KB; `.git` ≈ 156 KB. No data files, notebooks, tests, `requirements.txt` or `pyproject`.

| Path                                                                                       | Purpose                                                                                                                 | Value                                  |
|--------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------|----------------------------------------|
| `README.md` (212 lines)                                                                    | Goals, COF source notes, line-format description (ported from the PHP), caution/cancellation codes, DB design thoughts  | **High** (domain notes)                |
| `todos.md` (20 lines)                                                                      | Incremental re-encoding; how to track edited vs. original COFs; repeated-heading level problem                          | Medium                                 |
| `design.md`                                                                                | Task-name stub for the pipeline stages                                                                                  | Low                                    |
| `parse_previews/main.py` (743 lines)                                                       | The only application code                                                                                               | Ideas only                             |
| `data/cof_notes/cof_notes.md` (302 lines), `modified_files.txt`                            | Per-file defects and the manual edits applied                                                                           | **High**                               |
| `data/table_notes/preview_hdr.md`, `validations.md`                                        | Header-table schema (`fn_*` from filename, `txt_*` from text); validations that were never coded                        | Medium                                 |
| `data/cof_char_set_encodings/file_encoding_listing_2023_06_23.txt`                         | charset_normalizer output for 164 files                                                                                 | Medium                                 |
| `data/customer_order_form_grep.txt` (14 KB)                                                | One row per month: the `PREVIEWS #nnn <MONTH YEAR> CUSTOMER ORDER FORM` item line (appears APR10 → APR17)               | Medium – ident-line source data        |
| `data/previews_publications_grep.txt` (81 KB)                                              | PREVIEWS PUBLICATIONS section with context, per file                                                                    | Medium – shows heading/ident variation |
| `data/test_sqlite.db`                                                                      | **0 bytes**, committed empty                                                                                            | –                                      |
| `tools_and_utils/gen_download_script*.py`, `download_cof_files.sh`, `download_cof_pdfs.sh` | Generate/hold curl scripts for TXT and PDF COFs                                                                         | Medium                                 |
| `tools_and_utils/log_file_encodings.py`                                                    | charset_normalizer detect → rewrite as UTF-8; **hard-coded to only process names containing "09"** (stale debug filter) | Low                                    |

## 3. Data

- **No COF files are committed.** The code expects `data/original_cof_files/`, `data/utf8_cof_files/` and `data/output/previews_hdr_fn.csv` to exist locally; none do in the repo. Every run presumes a fresh re-download.
- **Coverage implied by scripts:** JAN10 → AUG23 (TXT; stop month SEP23) and PDFs JAN10 → AUG23 — about 164 files, matching the 164-entry encoding listing. README says the current Previews World site lists COFs back to JAN 2017, but direct URLs work back to JAN10; nothing exists for 2009 online (the 2009 files come from the older repos).
- **Download URL pattern:** `previewsworld.com/Catalog/CustomerOrderForm/TXT/MMMYY` (and `/PDF/`), the same pattern as the 2020 repo's script. Whether it still works today is unverified.
- **Missing issue:** MAY20 does not exist — Diamond published a combined May/June 2020 form. The author emailed Diamond support and planned to re-download and diff against existing files.
- **Encodings (counted from the listing, per survey):** 104 cp1250, 56 ascii, 1 utf_16, 1 utf_8, 2 undetected. cp1250 as a *detected* label is likely a charset_normalizer guess for ASCII-compatible Latin text; the 2020 repo's chardet reported mostly ASCII/ISO-8859-1 for older files. Treat encoding labels as hints and test by decoding.
- **Overlap with other repos:** not checked. In combination: 2016 repo has JAN09–AUG14, 2020 repo has JAN09–MAR20, this repo's scripts target JAN10–AUG23. **Together these cover 2009–2023, but no single repo holds the whole corpus**, and later files (APR20–AUG23) are only obtainable via this repo's scripts.

## 4. COF knowledge recorded in this repo

### From `cof_notes.md` (the valuable part)

**General conventions**
- First heading is normally `PREVIEWS PUBLICATIONS`, but for Free Comic Book Day issues it can be `FREE COMIC BOOK DAY`.
- Page numbers: **0** = no page number *and* items come before the first listed page; **−1** = informational/non-catalog line (e.g. ident text lines); later issues prefix merchandise pages with **`M`** (e.g. `PAGE M-12`). Some **heading lines start with the word "page"**, so a naive `startswith('PAGE')` test misclassifies them.

**Per-file defects** (each file was copied to `MMMYY_txt` before editing; the list below is from the notes and survey, with the sections I could confirm in the notes marked †)

| Issue                               | Defect                                                                                            | Fix applied                                                  |
|-------------------------------------|---------------------------------------------------------------------------------------------------|--------------------------------------------------------------|
| FEB09 †                             | extra tab between item code and title (line 5 shown)                                              | removed one tab                                              |
| APR, MAY, JUN, JUL, SEP 2009 †      | basic ident line has wrong month (`PREVIEWS MAR V19 #4` in the APR file) but correct volume/issue | corrected month                                              |
| JAN10, AUG10, JAN12, JAN13, JAN14 † | ident-line month wrong (per survey; sections present in notes)                                    | corrected                                                    |
| DEC12 †                             | missing page number                                                                               | inserted `PAGE 0`                                            |
| JAN13, AUG13 †                      | PAGE line appears after the headings                                                              | moved before headings                                        |
| NOV14 †                             | malformed page line (`GE 24`)                                                                     | repaired                                                     |
| MAY20                               | no issue exists                                                                                   | none; recorded in `modified_files.txt`                       |
| JUN20                               | ident lines are `PREVIEWS MAY/JUNE 2020` / `ISSUE #380/381 (VOL. 30 #5/6)`                        | rewritten to `PREVIEWS JUNE 2020` / `ISSUE 381 (VOL. 30 #6)` |
| MAR21 †                             | section present in the notes; details not reviewed                                                | –                                                            |

† = a section with that heading exists in `cof_notes.md`; I read the first ~60 lines and listed the section headings, but did not read every entry. The table's *Defect* column beyond FEB09/APR/MAY/JUN09/JUN20 is from the survey subagent.

Implication: **a robust parser should handle these in code (or in a separate, versioned "patches" layer) instead of editing source files by hand**, so the raw corpus stays pristine and fixes are auditable. The author's own todo ("decide how to track edited vs original COFs") points the same way.

### From `README.md`

- Item line fields (ported from the PHP, described in prose only): flag/distributor code (`SPOT`, `GEM`, `FI`, `KIDS`) · sol code `MMMYY NNNN` · title · release date `mm/dd/yy` · `SRP: $x.xx` or `MSRP` · ` = $` · blank. `SRP: PI` ⇒ price to be determined. Occasionally a double tab after the sol code.
- Caution codes `C: I-C-S` = international rights (0/1), content changes (0/1), ship-date changes (0–4); cancellation codes 1–10 (same material as the 2016 PHP header comment).
- Ident line: first non-blank line, e.g. `PREVIEWS AUGUST VOL. 24 #8` → month, volume, issue; year = volume + 2000 − 10.
- Heading hierarchy "is not self-evident from the text"; the **repeated-heading problem** (a second `PREVIEWS PUBLICATIONS` heading would be level 2 per PDF font size) has a proposed convention in `todos.md`: *a repeated heading resets to the level at which it first occurred*.
- DB wish-list: Postgres instead of MySQL; case/accent-insensitive search while preserving display text; raw **and** edited line columns; dated heading hierarchy (`valid_from`/`valid_to`).

## 5. The code (`parse_previews/main.py`)

SQLite file `test_sqlite.db` (relative path; a TODO says to move to Postgres), pandas/numpy for row-wise logic, SQLAlchemy to read/write tables, `anytree` for heading paths. Free functions and namedtuples, no classes. Entry point is the `__main__` block (l.733–743) where everything is commented out except `set_pv_lines_type(); set_page_numbers()` — so on a fresh DB it fails. Hard-coded absolute input path (l.18; personal home directory).

| Stage | Function                                                                                      | Notes                                                                                                                                                                         |
|-------|-----------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1     | `load_previews_hdr` / `derive_fn_fields` / `parse_cof_files_for_txt_fields`                   | filename → period (`strptime("%d%b%y")`), volume = year − 1990, issue = (vol−1)·12 + month + 27; scan text for the ident line; cross-check `fn_*` vs `txt_*`                  |
| 2     | `load_lines`                                                                                  | all raw lines → `previews_lines`; drops/recreates the table; opens files with the default encoding (not utf-8)                                                                |
| 3     | `set_pv_lines_type`                                                                           | vectorised classification (below) → `pv_line_type`                                                                                                                            |
| 4     | `set_page_numbers`                                                                            | page number + type (page/merch) → `pv_lines_fnl`; non-equi join of lines × page ranges, acknowledged as slow                                                                  |
| 5     | `create_previews_hdg_hrch_empty_table`, `build_heading_paths`, `resolve_heading_hierarchy`    | **unfinished**: builds `matches` but never returns/stores it; reads a `pv_lines` table nothing creates; the empty table is never seeded, so the lookup data isn't in the repo |
| –     | item splitting (`import_hdg_hrch_lvls_file`, `update_pv_item_lines_with_hhid`, field explode) | **not implemented**; only task names in `README.md`/`design.md`                                                                                                               |

**Line classification** (`set_pv_lines_type`, ~l.523–530, nested `np.where`), precedence:
JUNK (after the last line matching `%\t%\t%`) → BLANK → PAGE (`^PAGE (?:M-)?\d{1,3}\s*$`, with page number and M/S type extracted) → IDENT (`pvl_seq == ident_line`) → ITEM (`[^\t]*\t[^\t]*\t[^\t]*`, i.e. ≥ 3 fields) → NOTE (`^\(NOTE: .*\)$`) → else HDG.

**Ident-line detection** — the same four variants as the 2020 repo (ident_type 10 basic / 20 terse / 30 two-line "advanced" / 40 from the `PREVIEWS #nnn <MONTH YEAR> CUSTOMER ORDER FORM` item line; 2/3/4 = not found/fallback). The new 40 type (scrape the order-form item row) is a useful fallback when no ident line exists at all.

**New relative to 2020:** the `M-` merchandise-page handling, a NOTE line type, ident type 40, `fn_*` vs `txt_*` cross-check kept, vectorised (pandas) classification, plus documented file defects. **Not new:** the dated heading hierarchy (carried over, still unfinished), and the 2020 repo's actual item-field quirk handling (`explode_line_text`) is **not** ported.

## 6. Description parsing and NLP

**None.** No token rules, dictionaries, lookups, labelled data, evaluation or results; `validations.md` lists validations that were never coded; nothing under `data/output/` is committed. The only NLP statement is the README's "potentially may use NLP".

## 7. Bugs, hacks and gaps (from reading, not running)

- NOTE test comes *after* ITEM, so a NOTE line with ≥ 2 tabs becomes ITEM (`main.py:471` comment says notes vs headings is unresolved).
- Page sentinel mismatch: code assigns **−1** to lines before the first PAGE; `cof_notes.md` says **0** is the "before first page" sentinel and −1 is "informational".
- `df.astype({...})` result discarded (l.369–390), so dtype conversion has no effect; `df_joined.update(tmp)` (l.541) is a dtype hack; page numbers are stored as strings then cast.
- `engine.execute(...)` (l.428) was removed in SQLAlchemy 2.x, so the code needs SQLAlchemy < 2.0 *(unverified)*.
- `fh.readline()` mixed into a `for line in fh` loop (l.283, 298, 316) with a magic `i > 10001` guard — fragile, behaviour unverified.
- `pv_hdr_txt` not initialised: a file with no matching ident reuses the prior file's value or raises `NameError`.
- Hard-coded constants (`+27`, `year − 1990`); `PvHdrTxt` defaults list has 8 entries for 11 fields; `PathNode` typo `PatyhNode`; unused `PvLines`/`CofFile`; commented-out older code and `timeit` scaffolding.
- `log_file_encodings.py` only processes names containing `"09"`; `.gitignore` does not ignore `data/`, `*.db` or `.idea`.
- Open TODOs: class refactor, dtypes, parameterise paths, Postgres, incremental loads, split page prefix, faster page join, notes vs. headings, track edited files.

## 8. Things that should not be committed

- **No credentials found** (grep for `password` found nothing).
- A hard-coded personal home-directory path (`main.py:18`) exposes the local username.
- Second commit's author identity (`sklugr02`) differs from the first commit's author name. It looks like a different (possibly work) account — consider rewriting or ignoring if that matters.
- Empty `data/test_sqlite.db` committed (harmless).
- ~95 KB of grep output containing Diamond/publisher catalog text (minor).

## 9. Not verified / open questions

- Nothing was run. All bug claims in §7 are from reading.
- Which defects in the §4 table are described in detail in `cof_notes.md`: I confirmed FEB09, APR/MAY/JUN09, JUN20 and the section headings; the rest rely on the survey subagent.
- Whether `main.py`'s `matches` and unfinished heading stage have any saved output elsewhere (the author's local machine, not the repo).
- Whether COF files in this repo's scripts for APR20 → AUG23 still download, and how they overlap with the 2020 repo's files.
- Whether the "cp1250" encoding labels mean anything beyond a detector guess.
- The `MAR 2021` entry in `cof_notes.md` was not read.

## 10. Cross-repo takeaways so far (all three repos analyzed)

| Question                                       | Answer                                                                                                                                                                                                 |
|------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Where is the description-parsing work?         | **Only** the 2016 `tt.php` prototype (comics with `#`/ONE SHOT; ~24–26k rows; regex token classes). The 2020 and 2023 repos never attempted it.                                                        |
| Where is the best structure-parsing knowledge? | Combine: 2016 `pp.php` (line types, price, headings), 2020 `main.py` (4 ident variants, field quirks, dated hierarchy), 2023 `cof_notes.md` (per-file defects, page conventions, M-pages, NOTE lines). |
| Where is the best data?                        | 2016 repo (JAN09–AUG14 + PDFs + DB dump of parsed output), 2020 repo (JAN09–MAR20), 2023 scripts (JAN10–AUG23). Need to dedupe and decide a canonical, pristine corpus plus a separate patch list.     |
| What keeps recurring unsolved?                 | (1) heading hierarchy needs manual levelling; (2) title/subtitle/variant/artist separation; (3) undocumented flag codes (`SS`, `SPOT`, `OA`, `FI`, `KIDS`, `GEM`); (4) hand-editing source files.      |
| Reuse code?                                    | No. Reuse **knowledge, test cases and data**; rewrite as pure, tested Python with explicit unknowns.                                                                                                   |

Suggested next step: a cross-repo synthesis document (`documentation/cof_format_spec.md`) merging the three sources into one format specification with test fixtures, then a labelled sample set for description parsing.
