# Analysis: `previews_parsing` repository (2020)

Source: `../previews_parsing` (https://github.com/gskluzacek/previews_parsing), active Feb–Mar 2020.
Analyzed: 2026-11-13. Treated as read-only reference material.

Method: two subagents (structure/docs/data/history, and a full read of the code) reported back; I spot-checked the headline facts (file counts, commit count/dates, tracked `.idea` files, regexes in `main.py`). Nothing was executed. See §9 for what is unverified.

## 1. Summary

A Python + MySQL **staging pipeline** for COF files. It is a real step beyond the 2016 PHP version in *process* (re-runnable stages, dated heading hierarchy, ident-line variants, filename cross-checks) but it **stops before the hard problem**: it never parses the solicitation text. `sol_text` is stored whole. No title, subtitle, variant, artist, printing, issue or volume extraction exists, and nothing resembling NLP.

The main value for `vibe_preview_parsing`:

1. **A much bigger and newer data set:** 135 monthly COF files, JAN09 → MAR20 (29 MB), plus a working download script for 2014 onward. This extends the 2016 repo's JAN09–AUG14 corpus by about five and a half years.
2. **Catalogued COF format quirks** (ident-line variants, field-count oddities, price forms) discovered while processing 2014–2020 files.
3. **A line-type taxonomy** (IDENT / BLANK / ITEM / PAGE / JUNK / HDG).
4. **A dated heading hierarchy** (`valid_from`/`valid_to`) with a path-search algorithm, and a hand-curated heading extract.
5. A **target field inventory** for description parsing (same list as the PHP repo's `previews_raw`).

What is not worth carrying forward: the code itself (one 1,439-line `main.py`, MySQL-bound, hard-coded paths and credentials, no tests).

## 2. Repository layout

152 tracked files outside `.git/.idea`; `.git` is 8.6 MB. 16 commits, 2020-02-18 → 2020-03-07.

| Path | Purpose | Value |
|---|---|---|
| `README.md` | 2 lines, no content | – |
| `requirements.txt` | `chardet==3.0.4`, `dnspython==1.16.0`, `mysql-connector-python==8.0.19`, `protobuf==3.6.1`, `six==1.14.0` | Shows the (old) stack; no `setup.py`/`pyproject`, Python version unstated (f-strings ⇒ 3.6+) |
| `previews_parser/main.py` | The whole app (~1,440 lines): SQL strings + Python | Source of the knowledge listed below; rewrite, don't port |
| `test.py` | 41-line scratch script (not a test) prototyping the heading path search on a toy dict | Idea only |
| `hierarchy_resolution.sql` | 216 lines of pseudo-SQL/design notes for the heading-path algorithm | Good design note |
| `database/ddl/crt_previews_tbls.sql` | MySQL 8 DDL | Schema reference |
| `database/useful_queries.sql` | One ad-hoc query + a `LAST_INSERT_ID` sequence-table trick | Low |
| `heading_hrch_extract.xlsx` (1.1 MB) | First-pass heading extract from JAN09 | Low |
| `headings_hrch_extract_2.txt` / `.xlsx` | Refined, tab-separated heading extract with hand-assigned levels (e.g. PREVIEWS PUBLICATIONS = 1, DC COMICS = 2, DC UNIVERSE: BATMAN = 3) | **Useful** as heading seed/labels |
| `cof_files/` (29 MB, 141 files) | 135 × `MMMYY.txt`, 3 `*_original_txt` backups (DEC15, JAN09, JUN17), `download_cof.sh`, `copy_cof_files.sh`, `files_charset_txt` (chardet output) | **High** |
| `.idea/` | IDE config, **tracked** | Should not be committed (see §8) |

No build artifacts or `__pycache__` are tracked.

## 3. Data

- **Coverage:** 135 monthly files, JAN09 → MAR20. Per the survey, 2014–2019 appear complete and JAN20–MAR20 are present; 2009–2013 are described as partial (not verified month by month). Counts of 141 total files and 135 `MMMYY.txt` were confirmed.
- **Size:** typically 200–290 KB per file; JAN09–MAR09 ≈ 410–430 KB; `JUN17_original_txt` is 561 KB.
- **Overlap with the 2016 repo:** the 2016 repo has `*_COF.txt` for JAN09–AUG14. Months for 2009–2013 overlap but names differ (`_COF` suffix). `JAN09.txt` vs `JAN09_COF.txt` differ at byte 2 (probably an encoding/BOM or whitespace cleanup, not investigated). Files for 2014-onward (esp. late 2014–MAR20) are new relative to the 2016 repo. *Partly verified.*
- **Encoding:** chardet output (`files_charset_txt`) says mostly ASCII, some ISO-8859-1 / Windows-1252 (confidence ~0.73). `main.py` re-encodes non-UTF-8 files into `converted/`.
- **Download script:** `cof_files/download_cof.sh` loops `curl` over `https://previewsworld.com/Catalog/CustomerOrderForm/TXT/MMMYY` for 2014 on. This URL pattern differs from the one documented in the 2016 PHP header (`.../support/previews_docs/orderforms/MMMYY_COF.txt`), indicating Diamond changed their site between 2014 and 2020. Whether it still works today is unverified.
- **No parsed output is committed.** The database lives only on the author's machine; the only artifacts are the heading extracts.

## 4. The pipeline (what the code does)

All in `previews_parser/main.py`; there is no CLI. Steps are run by uncommenting calls in the `__main__` block (only `explode_line_text()` is active at the last commit). MySQL 8 at localhost; progress tracked per file in `previews_hdr.proc_sts`.

| Stage | Function | What it does |
|---|---|---|
| 1 | `convert_files_encoding` | chardet-detect each file, rewrite non-UTF-8 to `converted/` (uses `codecs.open(..., 'rU')`, invalid on modern Python) |
| 2 | `log_cof_files` | scan dir, derive period from the filename, find/parse the IDENT line, insert `previews_hdr` (status LOGGED). Truncates `previews_hdr` first |
| 3 | `load_line` | insert every raw line into `previews_lines` (status LOADED). Truncates `previews_lines` first |
| 4 | `set_pv_type` | one large SQL `CASE` classifies each line (status TYPED) |
| 5 | `set_page_nbr` | SQL window ranges assign page numbers (PAGED) |
| 6 | `resolve_heading_hierarchy(pvh_id)` | match HDG lines to `previews_hdg_hrch`; export unmatched headings as TSV for manual levelling |
| 7 | `import_hdg_hrch_lvls_file` | re-import the hand-edited TSV |
| 8 | `update_pv_item_lines_with_hhid` | attach each ITEM line's heading id |
| 9 | `explode_line_text` | split ITEM lines into `previews_basic_dtl` |

Output is DB tables only (plus `hdg_hrch_export_*.txt`). `previews_basic_dtl` columns: `promo_cd, sol_code, sol_text, release_dt, price_type, unit_price, price_ind`.

## 5. COF structure knowledge encoded in the code

### Line classification (simplified vs. PHP)

Done in SQL, in this priority order: **IDENT** (line matches the header's ident line) → **BLANK** (empty after trimming tabs) → **ITEM** (≥ 2 tabs) → **PAGE** (starts `PAGE`) → **JUNK** (after the last tab-bearing line in the file) → **HDG** (everything else).

So a heading is *"anything that is not item, page, blank, ident or trailing junk"*, with no heading regex. The PHP's H1/H2/H3 typing is replaced by the separate hierarchy table. Risk: any malformed heading line containing tabs is classed as an ITEM; and a heading with trailing tab padding only survives because blank-trim happens first (the 2013 files in the older repo have such padding).

### Ident line variants (new knowledge vs. the PHP repo)

`log_cof_files` recognizes four formats, stored as `ident_typ`:

- **10** – basic: `PREVIEWS <MONTH> VOL(.) nn #n` (`regex1`)
- **20** – terse: line after `PREVIEWS ORDER FORM` is `<MONTH> VOL nn #n` (`regex3`)
- **30** – two lines: `PREVIEWS <MONTH> yyyy` (`regex4`) then `ISSUE #nnn (VOL. nn #n)` (`regex5`)
- **4** – no ident line (first heading `PREVIEWS PUBLICATIONS` came first)
- **2/3** – ident found but regex failed

It also computes an **expected ident from the filename** (volume = year − 1990; issue = (vol−1)×12 + month + 27) and stores `txt_*` and `fn_*` columns so mismatches can be queried (`list_txt_fn_inconsistencies`). This is the one systematic mechanism for tracking drift, and it is a good idea to keep.

### Item field quirks

From `explode_line_text` (tab-split):

- More than 7 fields → drop the extra blank field at index 2 (a known Diamond quirk; same as the PHP `$off_set` hack for FEB09).
- Exactly 6 fields and field 3 contains `$` or `PI` → release date missing; insert a blank date.
- Solicitation code: remove the space at char 6 (`MAR13 0008` → `MAR130008`).
- Dates `m/d/yy` or `m/d/yyyy` → ISO, 2-digit years assumed 20xx.
- Price type: `MSRP`, `SRP`, bare `$` (NONE) or UNKNOWN; unit price = text after `$`; indicator `PI` or `FREE`. (`FREE` is new compared with the PHP code.)
- Lines with < 4 fields are printed as "malformed" and **dropped**.

### Heading hierarchy (the best idea here)

- Table `previews_hdg_hrch`: heading name, level, parent, `detail_items_ind` (whether the heading holds items worth parsing), `valid_from`/`valid_to`.
- Schema notes say hierarchy runs ~4 levels (publisher, imprint, category, backlist) and that the *same heading name can appear under different parents*, hence path-based matching.
- Algorithm (`resolve_heading_hierarchy`, 757+): walk HDG lines in order, keep `curr_path`/`curr_lvl`; for each heading build candidate paths from the longest prefix of the current path down to the heading alone; a recursive CTE finds the deepest valid path for the file's period; update the current path. Prototype in `test.py`, design in `hierarchy_resolution.sql`.
- Unmatched headings still need a **human** to assign levels in Excel (the `indent` column is an Excel formula) and re-import; this is repeated for each new month or format change.
- Replaces the PHP's `override_pvhl_id` reverse lookup.

## 6. Solicitation-text parsing: not implemented

- `sol_text` is stored raw (`main.py:1302`).
- The schema comments (`main.py:151–170`) list the planned columns, identical in intent to the PHP's unfilled `previews_raw` columns: `title, sub_title, title_vol, title_type, title_status, title_designations, book_type, book_vol, book_designations, issue_num, total_issues, printing, cover_variant, cover_type, advisory_code, caution_code, sol_info_codes, prev_sol_code, edition, other_designations`.
- Comments at the top of `main.py` point to the 2016 repo's `directory_contents.md` and `pp.php` for caution/cancellation code meanings.
- No dictionaries, lookup tables or NLP. The token rules live only in the 2016 repo's `tt.php` (see `analysis_previews.md` §5), and possibly `previews_parsing_pandas`.
- The code comment says the intended schema covers only **comic-book** ITEM lines (`detail_items_ind`), but the code loads all items.

**Conclusion:** across two repos and ~4 years, the description-parsing problem has been prototyped only once (`tt.php`, 2016, `#`-numbered comics only) and the 2020 repo did not advance it.

## 7. Bugs, hacks and risks (relevant as "lessons")

From the code-reading subagent; I did not reproduce these by running the code.

- **Brittle `explode_line_text`:**
  - `fields[4].strip().upper() or None` (~l.1314) then `.startswith` ⇒ `AttributeError` on an empty price; the `is None` check (l.1322) is unreachable. One blank price aborts the run.
  - `sol_code[6]` (l.1300) can raise `IndexError`; the date split (l.1306) raises on non-`m/d/y` values such as `TBD`.
  - `'PI' in fields[3]` is a substring test.
- **Header cross-join risks:** the `last_item` CTE is an inner join (a file with zero items drops out); the heading export has `between valid_to and valid_from` (reversed); `lead(...) over (order by ...)` lacks `partition by` in `update_pv_item_lines_with_hhid`.
- **Manual dependency:** `curs.fetchone()[0]` crashes if a parent lookup misses.
- **Destructive defaults:** `truncate table` on `previews_hdr` and `previews_lines` with no guard.
- **File-name handling:** `'.txt' in entry.name`; bad names raise.
- **ITEM test is crude** (≥ 2 tabs).
- **Dead code:** a first `main()`, unused variables, commented-out pipeline, unclosed cursors.
- **Environment coupling:** hard-coded home-directory paths; local MySQL required; `codecs.open(..., 'rU')` removed in recent Python.
- **Unfinished:** last commit (2020-03-07) is mid-way through `explode_line_text`; the commit before the hierarchy work says "need to test". No tests, no README.

## 8. Things that should not have been committed

- **Hard-coded database credentials** in `previews_parser/main.py` (`get_db_conn`, ~l.1373): a root password for a local MySQL. Not reproduced here. If this repo is public, treat that password as exposed and do not reuse it anywhere.
- **`.idea/` is tracked**, including `dataSources.xml` (local JDBC URL, a data-source id, and a note containing the password). Confirmed: `.idea/dataSources.xml`, `misc.xml`, `modules.xml`, etc. are in `git ls-files`.
- Personal paths/username in `main.py`.
- Bulk data duplicates (`*_original_txt` backups, 1.1 MB xlsx). The COF text itself is public catalog data, so probably fine.

For the new project: keep config/secrets in env vars or an untracked file, and make `.idea/` ignored from the start (the new repo currently shows `?? .idea/` untracked).

## 9. Reuse assessment

| Area | Reuse | Notes |
|---|---|---|
| COF data (135 files) | **Copy/reference** | Primary corpus; dedupe against the 2016 repo's files; compare `JAN09.txt` vs `JAN09_COF.txt` first to decide which is canonical |
| `download_cof.sh` | Adapt | Re-verify URL pattern; add rate-limiting/politeness; rewrite in Python if desired |
| Ident-line variants + filename cross-check | **Port the ideas** | Good source of test cases; formulas for volume/issue from year/month are the author's derivation, so verify |
| Line-type taxonomy | **Port** | Add explicit rules for headings and keep UNKNOWN separate from HDG |
| Item field quirks list | **Port** | Turn each into a fixture + test |
| Dated heading hierarchy + path search | **Port the algorithm** | Pure Python over a curated heading table (start from `headings_hrch_extract_2.txt`) |
| Heading extract (`headings_hrch_extract_2.*`) | Reuse as seed/labels | Hand-levelled; check coverage for 2014–2020 |
| `main.py` and DDL | Do not port | DB-bound, one big file, bugs listed above |
| Description parsing | **Nothing to port from this repo** | Use `tt.php` rules (previews repo), check `previews_parsing_pandas` |

## 10. Comparison with the 2016 repo (`previews`)

| Aspect | 2016 PHP (`previews`) | 2020 Python (`previews_parsing`) |
|---|---|---|
| Data | JAN09–AUG14 (53 files) + PDFs + DB dump | JAN09–MAR20 (135 files) |
| Line types | IDENT, BLANK, PAGE, H1/H2/H3, NOTFOUND, ITEM | IDENT, BLANK, ITEM, PAGE, JUNK, HDG |
| Heading logic | text lookup in a manual 3-level table; unknown ⇒ NOTFOUND; `override_pvhl_id` hack | path match in a dated hierarchy table (≈4 levels); unknown ⇒ manual TSV round trip |
| Ident line | 1 format | 4 formats + filename cross-check |
| Item fields | flag code kept in `pv_value`; price SRP/MSRP/PI/E | `promo_cd` (the flag) kept; price adds FREE and NONE |
| Description tokens | prototyped (`tt.php`, comics only) | **not attempted** |
| Process | 3 scripts, hand-run | status machine, hand-run |
| Tests/docs | notes in markdown | none |
| Secrets in repo | local credentials in PHP | root password in code and `.idea/` |

Both repos name the same column in the same places (flag code at index 0), but neither documents what the flag values mean. `previews_parsing` calls the column `promo_cd` (promotion code), which is a hint but not a definition.

## 11. Implications for `vibe_preview_parsing`

1. **Scope the corpus first.** Decide which of the 135 files form the test/training set, and dedupe against the 2016 files.
2. **Structure parsing is mostly solved in concept.** Combine the line taxonomy, the ident variants and the item quirks into a small, pure, tested parser with explicit "unknown" outcomes; no database required for parsing.
3. **Headings are the persistent manual cost** in both repos. Try to infer heading candidates automatically (single-column, all-caps, no sol-code) and use the dated hierarchy only for resolving ambiguity, not for discovery.
4. **Description parsing is where the project's value is**, and has no reusable code from this repo. Start from the 2016 token classes and build a labelled evaluation set before picking rules vs. NLP.
5. **Check the third repo** (`previews_parsing_pandas`) before designing, since it may contain the NLP experiments mentioned in `previous_repositories.md`.

## 12. Not verified / open questions

- Month-by-month completeness of 2009–2013 in `cof_files/` and whether the files differ in content from the 2016 repo's (only the byte-2 difference on JAN09 was noted).
- What `copy_cof_files.sh` does (not read), and the contents of the `*_original_txt` backups vs. converted files.
- Whether the download URL works today.
- Bugs in §7 come from reading, not running; the SQL pieces in particular were not executed.
- The `heading_hrch_extract.xlsx` / `headings_hrch_extract_2.xlsx` workbooks were not opened (the `.txt` extract's column list is from the survey).
- Meaning of `promo_cd` values.
- Whether the git history contains other deleted files or credentials (history was only summarised from commit messages, not searched).
