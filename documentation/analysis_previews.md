# Analysis: `previews` repository (2016)

Source: `../previews` (https://github.com/gskluzacek/previews), active Sep 2016 – Oct 2016.
Analyzed: 2026-11-13. The repo was treated as read-only reference material.

## 1. Summary

This is the **archive of the original PHP implementation** plus the raw data it worked on. It is mostly valuable as a **domain-knowledge and test-data source**, not as code to port.

What is worth carrying forward into `vibe_preview_parsing`:

1. **~53 months of real COF text files** (JAN09 – AUG14, with gaps) – ready-made test/training corpus (~105k item lines).
2. **The line grammar of the COF** and the heading hierarchy (3 levels, ~900 headings) – fully reverse-engineered in `pp.php`.
3. **A catalogue of tokens inside the solicitation text** (issue number, `(OF n)`, printing, caution code, advisory, variant cover, packaged sets…) – prototyped in `tt.php` with regexes, and the exact area the project hopes NLP will improve.
4. **A MySQL dump** of the parsed output (`previews_raw`, ~100k ITEM rows) – a ready-made *expected-output / gold-ish dataset* for comparing a new parser.
5. A side project (cover-date lookup against comicbookdb.com) that is **out of scope** for the parser but documents the downstream use case.

What is not worth carrying forward: the Django bi-temporal experiment, the empty Python scaffolding, and the PHP code structure itself.

## 2. Repository layout

| Path | What it is | Value for new project |
|---|---|---|
| `README.md` | Hand-written file catalog of the whole repo (despite the name, not a project README) | High – good orientation |
| `TODOs.md` | Two items; first: separate data files from old code into a common data dir | Low, but the idea is right (see §8) |
| `old_code/Preview Parsing/` | **The core.** PHP parser, COF files, SQL dump, notes, spreadsheets | **High** |
| `old_code/Preview Parsing/analysis.md`, `analysis meat.md` | Analysis of `get_cvr_dt.php` (belongs to the *Get Cover Date* project – misfiled) | Low |
| `old_code/Preview Parsing/directory_contents.md` | Detailed notes on the parsing dir incl. table definitions and `pv_type` counts | High |
| `old_code/Preview Parsing/sample.html` | Saved comicbookdb.com series page (sample for `title_index.py`) | Low |
| `old_code/Get Cover Date/` | PHP + SQLite tool to fetch cover dates from comicbookdb.com for Collectorz exports | Low (different problem) |
| `other/get title index/` | Python/lxml rewrite of the HTML parsing from the cover-date tool | Low |
| `slowly_changing_demensions/BiTemporal/` | Django exploration of bi-temporal tables (Windows artifacts, `.pyc`, egg cache) | None |
| `parse_previews/`, `tests/`, `docs/`, `setup.py`, `requirements.txt` | Empty/boilerplate Python packaging scaffolding (e.g. `parse_previews.py` is 5 bytes) | None |

The repo is ~506 MB / 249 tracked files, dominated by `pp_out.txt` (20 MB), `tt_out.txt` (1.6 MB), the SQL dump (59 MB), PDFs and zip archives. It already ships build artifacts that should never have been committed (`*.pyc`, `egg_cache/*.pyd`, `db.sqlite3`).

## 3. The data: Customer Order Form (COF) text files

Location: `old_code/Preview Parsing/previews parsing/MMMYY_COF.txt`

### Coverage

- 53 text files, JAN09 → AUG14, ~143k lines total.
- Full: 2009–2012. Partial: 2013 (Jan–Apr in the main dir, per the notes also Aug) and AUG14. No 2014 files other than AUG14.
- Duplicates exist: `Archive.zip`, `originals/Archive 2/`, `originals/Archive 2.zip` all hold copies of the same files; only `AUG14_COF.txt` is in `originals/` standalone. → Dedupe before importing.
- 39 PDF versions in `pdf/` (missing most of 2011 and Nov–Dec 2012). The PDFs are the *rendered catalog order form*; useful only to verify what the text version is missing.
- The source URLs are documented in the `pp.php` header comment (e.g. `.../support/previews_docs/orderforms/MAR13_COF.txt`, archive paths per year). The site layout may have changed since 2014 – unverified.

### File format (as observed)

- ASCII, **CRLF** (`\r\n`) line endings, **tab-delimited**.
- Line 1 is an identification line, e.g. `PREVIEWS MAR VOL 23 #03` (AUG14 variant: `PREVIEWS AUGUST VOL. 24 #8`).
- Month in the file name = *order period*; the Previews volume/issue relates to the catalog issue (e.g. `MAR13` file ↔ `PREVIEWS #296 MAY 2013` items – the file name month is the order-form month, the catalog month is two months later).
- A file mixes 1-column and 6/7-column lines (roughly 25–30% single-column).

Line types (derived from `pp.php`, matching the observed data):

| Type | Detection | Example |
|---|---|---|
| IDENT | no sol code, matches `^PREVIEWS (JAN\|…).* V(OL)?\.? ?\d\d #\d{1,2}$` | `PREVIEWS MAR VOL 23 #03` |
| BLANK | no sol code and empty column 0 | |
| PAGE | no sol code, col 0 starts with `PAGE` | `PAGE 40` |
| H1 / H2 / H3 | no sol code; text matches a known heading at the right level in the current context | `COMICS` / `DARK HORSE` / … |
| NOTFOUND | none of the above – an unknown heading or malformed line | |
| ITEM | col 1 (solicitation code) non-empty | see below |

ITEM line columns (tab-separated):

| Idx | Content | Example |
|---|---|---|
| 0 | **Flag code** (often empty) | `SPOT`, `SS`, `OA`, `FI`, `KIDS`, `GEM`, or combos like `OA SS` |
| 1 | Solicitation code `MMMYY NNNN` | `MAR13 0008` |
| 2 | Solicitation text (title + all the tokens) | `X #1 (OF 4) (MR)` |
| 3 | Release date | `05/08/13` (2013 files: `4/10/2013`) |
| 4 | Price | `SRP: $2.99`, `MSRP: $4.50`, `SRP: PI` |
| 5 | Order-qty placeholder | ` = $` |
| 6 | Trailing empty field (absent in the 2013 files) | |

Flag-code frequencies across all 53 files (105,450 item lines): none 62,756 · `SS` 19,085 · `SPOT` 10,846 · `OA` 5,137 · `FI` 4,871 · `KIDS` 2,053 · `GEM` 505 · `OA SS` 103 · `OA SPOT` 38 · `SS KIDS` 35. The meaning of these codes is **not documented anywhere in the repo** (`SS` appears to be "previously solicited"; `OA` presumably "offered again"; `FI` appears on Previews-publications rows; `SPOT` presumably "spotlight") – these are guesses to verify against Diamond documentation, **not** facts from the repo. The old parser stores column 0 in `pv_value` for ITEM rows, so the flag is preserved but unnamed.

### Format drift between files (affects parser robustness)

Found by sampling every ~6th file plus a full flag scan:

- **2013 files (JAN13+) have 6 columns, not 7** (no trailing empty field) and use `m/d/yyyy` dates instead of `mm/dd/yy`. `pp.php` copes only because it reads indices 0–4 and relies on `strtotime`.
- **FEB09 has a double tab** between solicitation code and text (handled with an `$off_set` hack in `pp.php`).
- Heading lines in JAN13 carry trailing tab padding (`PREVIEWS PUBLICATIONS\t\t\t\t\t`).
- JUL11 contains 2 six-column lines (outliers).
- The identification line format changed (`VOL 23 #03` → `VOL. 24 #8`; full month name in AUG14).
- Blank release dates exist (the old code had a bug here fixed 2014-08-24: `strtotime('')` → `false`).
- The sol-code in the DB is stored with the space removed: `MAR13 0008` → `MAR130008` (`substr(0,5).substr(6)`).

## 4. The old parsing pipeline (PHP + MySQL)

Environment: MySQL database named `bipolar`, local, with hard-coded credentials and hard-coded macOS paths in the scripts. (Local dev credentials only; do not copy.)

Three stages, run by hand:

1. **`lf.php` – load files.** Globs `*_COF.txt`, sorts chronologically, parses the identification line into `ident_str`, derives `period_dt` from the file name, inserts one `previews_hdr` row per file and one `previews_lines` row per physical line (unaltered text).
   - Known/fixed bug: `strtotime('AUG14')` misparsed the file name (fixed 2014-08-16 with explicit `01-MMM-20YY`).
   - Minor bug: error messages use single-quoted `'$file'` (no interpolation).
2. **`pp.php` – parse lines into `previews_raw`.** For each header with `proc_status IN ('NEW','REPROCESS')` it walks lines in order, splits on tab, and classifies each line (table above). It keeps a **stateful heading context** (`hdg_1/2/3` and ids), assigns it to every following ITEM, and builds `pv_source` = `H1 / H2 / H3`.
   - Heading lookup is **driven by a manually maintained table `previews_hdg_lvls`** (level, parent, name; unique on parent+name). Any unknown heading becomes `NOTFOUND` and has to be added by hand (the file ends with the SQL/Excel recipe the author used to generate the INSERTs).
   - `previews_lines.override_pvhl_id` lets the author force a line to a specific heading when text alone is ambiguous (0 = skip line). The exact use is under-documented ("What is override_pvhl_id and how is it used?" in the notes).
   - Price parsing: `SRP: $x` / `MSRP: $x` → `unit_price`; `…PI` → `pi_ind='Y'` (please inquire); anything else → `pi_ind='E'` (unknown price type).
   - Note a stateful bug risk: `$h1_id/$h2_id/$h3_id` (as opposed to the `h*_pvhl_id` copies) are not reset between files, so a first ITEM before any heading would inherit the previous file's heading. Likely harmless in practice, since each file starts with a heading.
3. **`tt.php` – prototype tokenizer for the solicitation text.** Reads `sol_text` of ITEM rows under COMICS / PREMIER PUBLISHERS, skips non-comic items by regex (T-shirts, statues, figures, TPB/GN/HC/SC…), splits title from `#issue` / `ONE SHOT`, then tokenizes the remaining text on parenthesised groups and classifies tokens with regexes. Prints one tab-delimited row per item (`tt_out.txt`, also the basis of the `titles and token parsing.xlsx` / `test1.xlsx` / `Workbook2.xlsx` analysis sheets).

Helper/scratch files: `db_common.inc.php` (`crtsql()` printf-style SQL builder with escaping), `str2dt.php`, `dates.php`/`dates.txt`, `t.php` (mysqli experiments) – not useful.

### Output schema (`previews_raw`, the interesting table)

Populated by `pp.php`: `pvh_id, pv_seq, pvl_id, pv_type, pv_value, h1/h2/h3_pvhl_id, pv_source, sol_page, sol_code, sol_text, release_dt, unit_price, pi_ind`.

Reserved but **never populated by the code in this repo** (planned parse targets): `title, sub_title, title_vol, title_type, title_status, title_designations, book_type, book_vol, book_designations, issue_num, total_issues, printing, cover_variant, cover_type, advisory_code, caution_code, sol_info_codes, prev_sol_code, edition, other_designations`. This column list is effectively the author's **target data model** for the description-parsing problem and is a good starting point for the new schema.

Recorded `pv_type` counts in the notes (full dataset): ITEM 102,774 · PAGE 23,017 · H2 8,864 · NOTFOUND 2,094 · H3 1,135 · BLANK 799 · H1 702 · IDENT 52.

Note: 2,094 NOTFOUND rows means the heading list was never fully completed, and `IDENT` = 52 versus 53 files on disk suggests one file was loaded under a different state or after the snapshot (unverified – probably AUG14, which was added after the dump's heading logic).

### Heading hierarchy

`previews_hdg_lvls` in the dump holds ~900 headings (approximate: ~19 level-1, ~800 level-2, ~100 level-3; counted from the INSERT blocks). Level-1 headings: APPAREL, BOOKS & MAGAZINES, COLLECTIBLES & NOVELTIES, **COMICS**, DVDS & DIGITAL MEDIA, GAMES, IMPORT TOYS & MODELS, **PREMIER PUBLISHERS**, **PREVIEWS PUBLICATIONS**, STATUES & MODELS, TOYS, TRADING CARDS (plus a few others that appear to be level-1 under different sections: OTHER APPAREL, BOOKS, DESIGNER TOYS, INTERNATIONAL, MAGAZINES, OTHER IMPORT TOYS & MODELS, CALENDARS – these look like they are level-2 or level-3 in practice; my rough extraction is not reliable on this point).

- Under COMICS, level 2 = publishers (some with level-3 sub-sections).
- PREMIER PUBLISHERS: 1–2 level-2 headings per publisher (e.g. `DARK HORSE`), most with level-3 sub-sections.
- `pull_list_ind = 'Y'` marks which headings (e.g. COMICS) hold items relevant to a pull list; its exact use is undocumented.
- `headings.xlsx` is a hierarchical export of the same table.

## 5. Solicitation-text tokens (the NLP-relevant part)

Sources: `tt.php` regexes, `solicitations text codes.txt` (the author's notes + ~100 real examples), and `titles and token parsing.xlsx` (26k rows of token-split output).

### Grammar (informal)

```
<TITLE words> [#<issue> | ONE SHOT [#n] | <book-type> [VOL nn] ] [<subtitle>] <tokens…>
```

Tokens are mostly space-separated words or parenthesised groups at the end, in no fixed order:

| Token class | Examples | Notes |
|---|---|---|
| Issue number | `#1`, `#0-6`, `#4.1`, `#1 & #2`, `#80` | Regex `#([\w.#\-]+)`; also `ONE SHOT` ⇒ issue 1 |
| Limited series `(OF n)` | `(OF 4)`, `PT 4 (OF 5)`, `( OF 5)` (stray space) | `tt.php` flags this as a known failure case |
| Printing | `2ND PTG`, `3RD PTG`, `NEW PTG`, `(NEW PTG)`, `CURR PTG`, `2ND PRINTING` | |
| Caution code | `(C: 0-1-2)` | Three flags: I-Rights / Content changes / Ship-date changes (defined in the `pp.php` header: 0/1, 0/1, 0–4) |
| Advisory | `(MR)` mature, `(A)` adult | |
| Solicitation info | `(RES)` resolicited, `(O/A)` offered again | |
| Other designations | `(Net)`, `(NOTE PRICE)`, `(PD)`, `(OSW)`, `NOW`, `(ONGOING)` | `(ONGOING)` becomes `title_type` ONGOING |
| Previous solicitation code | `(MAY120825)`, `(STAR12345)`, or `MAY 2010` | Pattern `(MMMYY######)` |
| Cover variant | `CVR A XXXX`, `XXXX VAR CVR`, `REG CVR`, `GATEFOLD CVR`, `SUB VAR`, `SGN`, `C2E2`, `AUXILIARY`, `NEWSSTAND`, `CGC`, `W/ SKETCH` | Most ambiguous class: artist names are free text |
| Packaged sets | `COMPLETE BAG SET`, `BOX SET`, `COMBO PACK`, `#0-6 COMPLETE BAG SET` | |
| Collected-edition type | `GN`, `TP`, `TPB`, `HC`, `SC`, `OMNIBUS TP`, `COLL ED`, `HC W/ DUST JACKET`, with optional `VOL nn` | GN/TP/etc. *not* handled by `tt.php` (it skips them) – only described in the notes |
| Edition qualifiers | `SGN`, `LTD ED`, `SP ED`, `PX ED`, `GOLD ED`, `NYCC 2009 EX`, `SDCC ED`, `US ED`, `UK ED`, `SPANISH ED`, `FIRST LOOK ED`, `EXPANDED REG ED`, `30TH ANNIV` | |
| Special-issue words | `ANNUAL`, `CHRISTMAS SP`, `HOLIDAYS SPECIAL`, `SERIES SPECIAL`, `DIRECTORS CUT`, `DOUBLE-SIZED`, `DOUBLE DIGEST`, `NUDE` | |
| Subtitle | `OLYMPIANS GN VOL 01 ZEUS KING OF THE GODS`, `FILLER BUNNY #2 REVENGE OF THE FILLER BUNNY`, `ARCHIE #627 (ARCHIE MEETS KISS PT 1)` | Free text; hard to separate from title without a title dictionary |

### Why this is hard (and where NLP / a dictionary helps)

- **Title/subtitle boundary** is not marked. Only a known-title list or a statistical model can split `TERRY MOORE HOW TO DRAW #2 EXPRESSIONS` or `LAST ZOMBIE BEFORE THE AFTER #1 CVR A PERRY`.
- **Variant-cover artist names** appear after or before `CVR`/`VAR`, interleaved with title words, e.g. `VAMPIRELLA SECOND COMING #1 GONZALEZ CVR`, `COVER A RANDOLPH`.
- **Creator-in-title**: `DREW HAYES POISON ELVES`, `TERRY MOORE HOW TO DRAW`, `BUDD ROOT SP ED` – the same person appears as a creator credit in the title and as a cover artist.
- **Volume vs issue** is overloaded: `STRAWBERRY SHORTCAKE VOL 2 #1` (series volume), `TP VOL 01` (collected volume), `MEATHAUS TP #8 HEADGAMES` (collected edition numbered with `#`).
- **Token order is not fixed** and parenthesised groups sometimes contain more than one concept.
- **Punctuation has been stripped** from titles in the source (e.g. `X #1`, `MICHAEL AVON OEMINGS VICTORIES`, `BETTY & VERONICA`). The notes say: *"take out any punctuation from the title text"* – so normalised keys are already assumed.
- **Everything is upper case**, so capitalisation cannot be used as a signal.
- `tt.php` only handled **comics with `#` or ONE SHOT** (≈ 24–26k rows in the analysis sheets out of ~100k items); collected editions, statues, apparel, magazines, etc. were not tokenized. The old approach therefore leaves the large majority of ITEM rows unparsed.

Known bugs/limitations in `tt.php` worth remembering:
- `(OF n)` handling is order dependent (only recognised as limited-series marker when it is the *first* token).
- Several regexes use `\b…$` forms that match substrings (`ED`, `SE`, `EX` as cover-variant markers can false-positive on real words).
- `prev_sol_code` also stores month-name dates (`MAY 2010`), mixing two concepts.
- Tokens that don't match anything go to `other_tokens` (tab separated) – the old author's review queue.

## 6. Other projects in the repo (for completeness)

### Get Cover Date (`old_code/Get Cover Date/`)

PHP CLI + SQLite (`comics_invoicing.db`). Reads a semicolon-delimited export from the *Collectorz Comic* app, looks up each series' issue index on comicbookdb.com, parses cover dates, and writes `invoice_ouput.csv` for an Excel "invoice" template. Notable logic: issue-number normalization (`7` + `.1A` → `7.1`), variant handling (`Std Variant`, multiple story arcs), partial-date forms (`early/late MMM YYYY`, year-only, `ANNUAL`), and a large SQL view `fnl_rpt_1` that classifies matches as *Single Date*, *Single Distinct Date* or *Multiple Dates* or *Not Matched*. The "reprocess" mode described in the design doc is **not implemented**. The source website (comicbookdb.com) is reported by the author to be no longer operational. `other/get title index/title_index.py` is a later lxml rewrite of the same HTML parsing, with strict child-node-count validation and exceptions.

Relevance: shows the downstream use (collection tracking / invoicing) and the author's naming/matching conventions; not a parser dependency.

### Bi-temporal Django experiment (`slowly_changing_demensions/`)

Exploration of valid-time/transaction-time tables (comments in `temporal.py`, publisher model comments in `models.py`). Not related to parsing. Contains `db.sqlite3` (Django internal state only), Windows `.pyc`/egg artifacts. Possibly useful *if* the new project ever wants history tracking of series/publisher attributes – otherwise ignore.

## 7. Database dump (`bipolar_2014_08_16.sql`)

- 59 MB MySQL dump, dated 2014-08-16, 11 tables: `code_hdr`, `code_values`, `code_attribs` (empty), `users`, `pull_lists`, `pl_series`, `pl_publishers`, `previews_hdg_lvls`, `previews_hdr`, `previews_lines`, `previews_raw` (858 INSERT statements).
- Every table has `crt_dt, crt_id, updt_dt, updt_id` audit columns.
- The **pull-list side** (`users`, `pull_lists`, `pl_series`, `pl_publishers`) shows the intended product: a multi-user web app where users maintain pull lists (series, start issue, variant indicator/quantity) and the parsed Previews data drives ordering. The `users` table has contact/address/security-question columns – a web-app design, not used by the parser.
- **Privacy note:** the dump's `users` table contains real rows (the author's own account with personal email and a password column). Do not publish or copy these values; if the dump is imported for analysis, exclude `users`.
- Large enough that it should be imported into a local DB (MySQL/MariaDB, or converted to Parquet/SQLite) rather than read directly. **Not done yet** – everything in this analysis is from schema/source reading and spot checks, not from querying the data.

## 8. Reusable assets for `vibe_preview_parsing`

| Asset | Where | Suggested use |
|---|---|---|
| COF text files (dedupe first) | `old_code/Preview Parsing/previews parsing/*_COF.txt` | Test corpus; copy (not link) into the new repo's `data/` or reference by path. Respect TODO #1 from the old repo (data separate from code). |
| `previews_raw` rows | SQL dump | Baseline for regression comparison (`pv_type`, `pv_source`, `sol_code`, `sol_text`, price, date) |
| Heading table (`previews_hdg_lvls`) / `headings.xlsx` | SQL dump, xlsx | Seed for a heading dictionary; export to CSV/JSON |
| Token regexes | `tt.php` | Starting rule-set / features for a hybrid rules + NLP parser |
| Token catalogue and examples | `solicitations text codes.txt` | Seed test cases / labelled examples |
| Analysis spreadsheets | `titles and token parsing.xlsx` (26k rows), `test1.xlsx` (24k), `Workbook2.xlsx` (24k), `Workbook6.xlsx` (400 `pv_source`/`sol_text` samples) | Candidate silver labels – they show the old parser output *and* the author's manual review; quality unknown |
| Caution-code and cancellation-code definitions | `pp.php` header comment | Reference data (caution = 3 flags; cancellation codes 1–10) |
| Previews site URL patterns | `pp.php` header comment | Download automation (needs re-verification) |

## 9. Observations and recommendations

1. **Treat the old parsers as specification, not code.** Behavior to preserve: heading-context tracking, item/sol-code detection, price/PI parsing, page tracking, flag-code retention. Behavior to fix: manual heading list, tab-fragile parsing, state leaks, hard-coded config.
2. **Parse structure with a small deterministic grammar** (IDENT / PAGE / heading / ITEM), tolerate the observed drift (6 vs 7 columns, double tabs, date formats, trailing tab padding, CRLF) and **fail loudly** on unexpected line shapes instead of silently emitting `NOTFOUND`.
3. **Headings:** keep a dictionary but learn candidates automatically – an all-caps single-column line without a sol-code that is not PAGE/IDENT is a heading; level can be inferred from position, repetition across months and the known parent. This removes most of the 2,094 `NOTFOUND` rows and the manual SQL-via-Excel loop.
4. **Description parsing is the real work.** Use the old token classes as the target schema; use rules for the closed-vocabulary tokens (caution code, advisory, `(OF n)`, printings, sol codes, dates, editions) and reserve NLP/ML for the open-vocabulary parts: title vs subtitle, creator names, variant-cover artist, volume-vs-issue disambiguation. Build a labelled evaluation set before choosing a model.
5. **Cover the other 75%.** The old tokenizer only handled `#`-numbered comics; GN/TP/HC, merchandise and magazines were left raw. Decide early whether those are in scope.
6. **Document the flag codes** (`SS`, `SPOT`, `OA`, `FI`, `KIDS`, `GEM`) from authoritative Diamond sources before relying on them; the repo never defines them.
7. **Use the existing data as an oracle carefully:** the dump reflects a 2014 snapshot of the logic (including its known bugs and NOTFOUNDs). Differences from a new parser are a *review list*, not automatic regressions.
8. **Check date/period semantics:** file month (order-form month) differs from the catalog month in the `PREVIEWS #nnn MONTH` items, and item release dates are 1–3+ months later. Model them separately (`order_period`, `catalog_issue`, `release_date`).

## 10. Open questions / not verified

- Meaning of flag codes, `pull_list_ind`, and `override_pvhl_id` (authored notes ask the same questions).
- Whether the COF URL patterns (and archive layout) in `pp.php` still work today.
- Exact heading counts and per-file coverage of the dump (counted heuristically from INSERT text; the dump was not loaded into a database).
- Whether `IDENT = 52` vs 53 files points to a missing/duplicated file in the dump.
- Quality of the manual-review spreadsheets (`titles and token parsing.xlsx`, etc.) – not opened; sizes and column names are from the author's own notes in `directory_contents.md`.
- The Excel files, PDFs, zip archives and `sample.html` were not opened.

## 11. Method

Read: `README.md`, `TODOs.md`, `directory_contents.md`, both analysis docs, `pp.php`, `lf.php`, `tt.php`, `title_index.py`, `design.txt`, `solicitations text codes.txt`. Sampled COF files (head/mid) and surveyed all 53 for column counts and flag-code frequency; sampled `pp_out.txt`/`tt_out.txt`; extracted the heading inserts from the SQL dump. Did **not** read `get_cvr_dt.php` (27 KB) line by line – its description relies on the author's analysis docs and `design.txt`. No data was modified in the source repo.
