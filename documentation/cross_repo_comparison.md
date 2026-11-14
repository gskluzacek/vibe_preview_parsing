# Cross-repo comparison: `previews` · `previews_parsing` · `previews_parsing_pandas`

Written 2026-11-13 from the existing written analyses (`analysis_previews.md`, `analysis_previews_parsing.md`, `analysis_previews_parsing_pandas.md`) and the measured spec (`cof_format_spec.md`). No new reading of the repos was done for this document; where a claim rests on a subagent's reading rather than my own check, the underlying analysis says so. Items marked **(recommendation)** are my suggestions, not findings.

## 1. At a glance

|                               | `previews` (PHP)                                                                                     | `previews_parsing` (Python/MySQL)                         | `previews_parsing_pandas`                                   |
|-------------------------------|------------------------------------------------------------------------------------------------------|-----------------------------------------------------------|-------------------------------------------------------------|
| Listed period                 | Sep–Oct 2016                                                                                         | Feb–Mar 2020                                              | Jun–Jul 2023                                                |
| Real code dates               | 2013–2014 (`pp.php` created 2013-03-11; DB dump 2014-08-16); the repo is a 2016 archive of that work | 2020-02-18 → 2020-03-07, 16 commits                       | 2023-06-22 and 2023-07-10, 2 commits                        |
| Stack                         | PHP + MySQL, hand-run scripts                                                                        | Python, one 1,439-line `main.py`, MySQL 8, SQL-heavy      | Python, one 743-line `main.py`, pandas + SQLite (+ anytree) |
| COF data held                 | 53 files JAN09–AUG14, PDFs, zips, DB dump                                                            | 135 files JAN09–MAR20 (converted/edited)                  | none; scripts for JAN10–AUG23                               |
| Structure parsing             | complete enough to load ~100k items                                                                  | staged pipeline, stops at item "explode"                  | line typing + page numbers only                             |
| Heading hierarchy             | working but manual (3 levels)                                                                        | dated hierarchy, algorithm written, manual levelling step | design + start of algorithm, unfinished                     |
| Item fields (code/date/price) | done (`pp.php`)                                                                                      | done in `explode_line_text` (with bugs)                   | not implemented                                             |
| Description parsing           | **prototype** (`tt.php`, comics with `#`/ONE SHOT)                                                   | **none**                                                  | **none** (README says "potentially NLP")                    |
| Tests                         | none                                                                                                 | none                                                      | none                                                        |
| Docs                          | extensive notes (`directory_contents.md`, analysis docs)                                             | 2-line README                                             | README + `cof_notes.md` (valuable)                          |
| Secrets committed             | local DB credentials in PHP                                                                          | root DB password in code and tracked `.idea/`             | none found                                                  |

Net progress across 10 years: the **structure** problem was solved in 2013–14, re-engineered in 2020, and restarted in 2023; the **description** problem was prototyped once in 2013–14 and has not advanced since.

## 2. Design decisions side by side

| Topic                   | 2013–14 PHP                                                                                | 2020 Python/MySQL                                                                                                    | 2023 pandas                                                                            |
|-------------------------|--------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------|
| **Processing model**    | 3 scripts: load files, parse lines, prototype tokenizer; status flags (`NEW`/`REPROCESS`)  | status machine (`LOGGED→LOADED→TYPED→PAGED…`) re-runnable per file; steps chosen by editing `__main__`               | same stage names as 2020 (`design.md`), re-created as pandas steps; most commented out |
| **Where logic lives**   | PHP + a handful of SQL queries                                                             | SQL `CASE`/window/CTE inside Python strings                                                                          | pandas/numpy with SQL tables as storage                                                |
| **Line classification** | IDENT, BLANK, PAGE, H1/H2/H3, NOTFOUND, ITEM — headings recognised by text lookup          | IDENT, BLANK, ITEM(≥2 tabs), PAGE, JUNK, HDG (anything else)                                                         | JUNK, BLANK, PAGE (`M-`aware), IDENT, ITEM(≥3 fields), NOTE, HDG                       |
| **Heading levels**      | text matched against a manual 3-level table; unknown ⇒ `NOTFOUND`; `override_pvhl_id` hack | name-and-path match in a table with `valid_from/valid_to`; unmatched exported to TSV, levelled in Excel, re-imported | same dated-table idea; `resolve_heading_hierarchy` unfinished                          |
| **Identification line** | one format                                                                                 | four variants + filename-derived expected value; mismatches queryable                                                | same four variants + ident type 40 (scrape the order-form item row)                    |
| **Item fields**         | `explode` + hack for FEB09 double tab; flag kept in `pv_value`                             | field-count quirks (extra column, missing date), 2/4-digit years, `FREE` price; flag called `promo_cd`               | prose only (README)                                                                    |
| **Dates/prices**        | PI indicator, `E` for unknown price type; blank-date bug fixed 2014-08-24                  | SRP/MSRP/none/UNKNOWN + PI/FREE; blank price crashes the run                                                         | n/a                                                                                    |
| **Description**         | regex tokenizer, 13 output columns, comics only                                            | schema comment only                                                                                                  | none                                                                                   |
| **Data hygiene**        | none beyond notes                                                                          | `chardet` re-encoding into `converted/`                                                                              | `charset_normalizer` re-encoding; **hand edits** tracked in `cof_notes.md`             |
| **Config**              | hard-coded paths and local DB credentials                                                  | hard-coded paths and root password                                                                                   | hard-coded home path, relative output paths                                            |
| **Error handling**      | try/catch prints                                                                           | ad hoc; one bad price aborts the run; malformed lines dropped                                                        | minimal                                                                                |

## 3. What each repo got right, got wrong, and what to learn

### 3.1 `previews` (2013–14 PHP)

**Right:** worked end to end; produced ~100k parsed ITEM rows; kept every raw line (`previews_lines`) separate from parsed rows (`previews_raw`); recorded the target schema for description parsing (the 20 unfilled columns); documented the domain (caution/cancellation codes, token examples, `directory_contents.md`); the only attempt at tokenizing descriptions.

**Wrong / limited:** heading list was manual and never finished (2,094 `NOTFOUND`); knowledge locked in code comments and spreadsheets; tokenizer assumed one grammar (`(OF n)` first token) that the data contradicts; no tests; big binary artefacts and local credentials committed; flag codes stored but never defined.

**Lesson:** separate raw from parsed; keep the target schema; unknown headings must surface as a small review queue, not a growing `NOTFOUND` pile.

### 3.2 `previews_parsing` (2020)

**Right:** staged, re-runnable, status-tracked pipeline; **data-driven, date-validated heading hierarchy** with a real path-search algorithm; four ident-line variants and the filename cross-check; a list of item-field quirks discovered on 2014–2019 data; large corpus (135 files) extended through MAR20; a hand-levelled heading extract (JAN09).

**Wrong / limited:** never reached description parsing; everything in one file mixing SQL strings and Python; fragile code paths (a blank price aborts the run, `sol_code[6]` index error, reversed `BETWEEN`, missing `PARTITION BY`); destructive `TRUNCATE` with no guard; manual levelling step per month; hard-coded password and tracked `.idea/`; no tests/README.

**Lesson:** the heading-path idea is the best architectural contribution; the implementation (SQL-in-Python, DB-bound) is not.

### 3.3 `previews_parsing_pandas` (2023)

**Right:** careful **data-defect documentation** (`cof_notes.md`) and decisions about conventions (page 0/−1, `M-` pages, repeated-heading rule); vectorised line typing; ident type 40; download scripts that extend coverage to AUG23 (including PDFs); first explicit statement of wanting raw + edited lines and Postgres.

**Wrong / limited:** no results, no committed data, no NLP despite the stated goal; abandoned after two commits; relied on hand-editing source files; same SQL-staging architecture as 2020, just with pandas as the engine, so little new; unfinished heading stage; stale debug filters; needs SQLAlchemy < 2.

**Lesson:** the pandas rewrite changed the tool, not the problem. The unsolved parts (headings, descriptions, corpus provenance) are the same ones.

## 4. Why progress stalled (pattern across repos)

1. **Each restart re-solved the same solved problem** (line typing, ident, pages) because knowledge lived in code and notes rather than in a spec and tests. `cof_format_spec.md` is meant to end that.
2. **The description problem was never scoped.** The 2013–14 tokenizer covered ~25% of items and guessed at a grammar; later repos treated it as "later".
3. **Headings needed a human each time** and no repo built the review loop as a first-class feature.
4. **Data was edited in place** with no machine-readable patch log, so a clean re-download could not be reconciled with the working copies.
5. **No tests.** Format quirks were found, fixed, and re-forgotten (e.g. the FEB09 double tab was patched in 2013, 2020 *and* 2023).
6. **Infrastructure before results.** Both later repos built databases, status machines, and schemas before producing any parsed output a user could look at.

## 5. Keep / rewrite / drop for `vibe_preview_parsing`

| Item                                                               | Source                                        | Decision **(recommendation)**                    | Notes                                                                                                                                            |
|--------------------------------------------------------------------|-----------------------------------------------|--------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------|
| COF text files                                                     | 2020 repo (+ 2016 for cross-check)            | **Keep** — one canonical corpus, UTF-8, pristine | Repair the 4 damaged POKÉMON lines from the `*_original_txt` backups; APR20–AUG23 may be unobtainable now (see decision 9) — back up what exists |
| Per-file defects and manual edits                                  | 2023 `cof_notes.md`, `modified_files.txt`     | **Keep, convert**                                | Turn into a machine-readable patch list applied at load time                                                                                     |
| Line-type taxonomy                                                 | all three                                     | **Keep** (spec §3)                               | pure functions, no DB                                                                                                                            |
| Ident variants + filename check                                    | 2020/2023                                     | **Keep** (spec §2.1)                             | filename authoritative                                                                                                                           |
| Item field normalization rules                                     | 2020 + measurements                           | **Keep** (spec §4)                               | one test per anomaly                                                                                                                             |
| Heading path search + dated table                                  | 2020/2023                                     | **Keep the idea, rewrite**                       | pure Python over a curated file                                                                                                                  |
| Hand-levelled headings                                             | 2020 extract, 2016 table                      | **Keep as seed data**                            | JAN09 only; 2016 table is a 2013–14 snapshot                                                                                                     |
| Target field inventory                                             | 2016 `previews_raw`, 2020 schema comments     | **Keep**                                         | basis for output schema                                                                                                                          |
| Token regexes and notes                                            | 2016 `tt.php`, `solicitations text codes.txt` | **Keep as baseline rules, expect to extend**     | measured grammar in spec §6 corrects several assumptions                                                                                         |
| `main.py` (2020, 2023)                                             | –                                             | **Drop**                                         | DB-bound, one file, known bugs                                                                                                                   |
| PHP code                                                           | 2016                                          | **Drop**                                         | reference only                                                                                                                                   |
| MySQL dump                                                         | 2016                                          | **Keep as oracle, not as dependency**            | exclude the `users` table                                                                                                                        |
| Django bi-temporal experiment, Get Cover Date, title index scraper | 2016                                          | **Drop** from scope                              | unrelated to parsing                                                                                                                             |
| Analysis spreadsheets (`titles and token parsing.xlsx` etc.)       | 2016                                          | **Review, maybe seed labels**                    | unopened so far; quality unknown                                                                                                                 |
| Download scripts                                                   | 2020/2023                                     | **Keep for provenance; likely obsolete**         | the source site is reported decommissioned (`previews_world_decommissioned.md`); untested                                                        |

## 6. Decisions still open

Each has a suggested default, not a settled choice.

| #  | Decision                                   | Options                                       | Suggested default **(recommendation)**                                                                                                                                                                              | Why                                                                                                                                                                                                   |
|----|--------------------------------------------|-----------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1  | **Storage / architecture**                 | files + pure Python; SQLite; Postgres         | Pure parsing library with typed records, output to files (CSV/Parquet) plus SQLite for exploration; Postgres only if a web app is real                                                                              | both prior DB pipelines stalled on infrastructure; the 2023 README's Postgres wish (accent-insensitive search) is a downstream need                                                                   |
| 2  | **Scope of parsing**                       | comics only; all items                        | Structure for all items; description parsing for comics and books first, merchandise as a separate simple grammar                                                                                                   | ~30% of items carry `#n`; merchandise (`T/S`, `FIG`, `AF`…) has a different grammar                                                                                                                   |
| 3  | **Heading levels**                         | manual table per file; inferred; hybrid       | Infer candidates automatically, maintain a curated dated hierarchy, review queue for unknowns                                                                                                                       | removes the manual per-month cost; JAN09-only gold data exists today                                                                                                                                  |
| 4  | **Handling the April 2018 catalog change** | one hierarchy; versioned hierarchies          | Versioned hierarchy with `valid_from/valid_to`                                                                                                                                                                      | 2018 restructure merges comics into PREMIER PUBLISHERS                                                                                                                                                |
| 5  | **Raw vs patched data**                    | edit files; patch list                        | Immutable raw + patch list, both in the repo                                                                                                                                                                        | auditability; ends the FEB09-style rediscovery                                                                                                                                                        |
| 6  | **Description parsing method**             | rules only; rules + dictionary; ML/NLP        | Rules for closed-vocabulary tokens (caution, advisory, `(OF n)`, printing, codes); dictionary + ML for title/subtitle/artist                                                                                        | measured token order is near-deterministic for metadata, free text is not                                                                                                                             |
| 7  | **Evaluation data**                        | none; hand-label sample                       | Build a labelled set (start with the 25 hard samples) *before* choosing an NLP approach                                                                                                                             | no labelled data exists in any repo                                                                                                                                                                   |
| 8  | **Flag/`M-`/`(Net)` semantics**            | infer; get authoritative source               | Source Diamond documentation; store raw until confirmed                                                                                                                                                             | spec §9 lists them as unconfirmed                                                                                                                                                                     |
| 9  | **Corpus scope and source**                | **Decided: recover originals from the Internet Archive** | Collect the COF text files and PDFs as published by the source (not the author's edited copies) from the Wayback Machine (the author is willing to build search/download tooling). A rule-based normalizer then turns originals into clean COF files, which are the basis for all later processing. The current 135 files become a comparison reference, not the source of truth. Also check the old archive URL paths (section 10) | the 2026-11-13 index probe (section 10) shows the archive holds far more than expected |
| 9b | **Forward-looking data source**            | **Decided: historical archive only**          | The parser is for the historical COF corpus: JAN09–MAR20 today, extended to whatever the archive yields (the probe shows captures up to 2025). No pipeline for current months; PRH / Lunar / comicreleases.com / League of Comic Geeks are out of scope      | decided by the author; replacement sources remain listed in `previews_world_decommissioned.md`                                                                                                        |
| 10 | **Secrets and tooling**                    | –                                             | `.gitignore` for `.idea/`, env-var config, no credentials in code                                                                                                                                                   | both older repos leaked local DB passwords                                                                                                                                                            |
| 11 | **Is an NLP model needed at all?**         | –                                             | Decide after the labelled set and a rules baseline are measured                                                                                                                                                     | the repos never produced evidence either way                                                                                                                                                          |

## 7. Corrections to `previous_repositories.md`

- The pandas repo is not an NLP attempt; "potentially may use NLP" is its only mention.
- The pandas repo's period is printed as "Jul 2023 – Jun 2023"; the commits are 2023-06-22 and 2023-07-10 (Jun–Jul 2023).
- The 2016 repo's code is from 2013–2014 (committed Sep–Oct 2016).
- The pandas repo's description "attempt to refactor … so that it uses pandas to do its heavy lifting" is accurate in intent but the repo does not get beyond line typing and page numbers.

## 8. Not verified / caveats

- This comparison relies on the three analysis documents; the repos were not re-read for it. Their own caveats apply (several bug claims come from reading, not running; the 2020 and 2023 code was not executed).
- `previews_world_decommissioned.md` (this repo) was only read after the first draft of this document and led to the changes in decisions 9/9b and the sequence. Its claims (Diamond's bankruptcy and closure, dead previewsworld.com links, replacement distributors) come from the author's notes and an AI overview; I have not verified them or tested the old URLs.
- Not analyzed: the 2016 analysis spreadsheets, the replacement catalogs' formats, and COFs after MAR20.
- The "keep/rewrite/drop" and "suggested default" columns are judgement calls and have not been discussed with the project owner.
- I have not weighed effort or ordering; see the next section only as a rough sequence.

## 9. A rough sequence **(recommendation)**

0. Decisions 9 and 9b are settled: historical archive only, with originals recovered from the Internet Archive (section 10). The COF stopped being published when Diamond closed, so everything below applies to a fixed, finite corpus.
1. Acquire originals from the Wayback Machine (text and PDF), keep them as downloaded, with a manifest, then write the normalization rules (the patch list, damaged-line repairs, layout variants) that produce clean COF files; re-run the measurement scripts on anything added.
2. Structure parser as a pure, tested library (spec §3–§4 and the anomaly register as fixtures), with an explicit unknowns report.
3. Heading discovery plus a curated, dated hierarchy and review queue.
4. Labelled sample set for descriptions; rules baseline for closed tokens; measure; then decide on dictionary/ML for the open-vocabulary parts.
5. Output format and storage chosen last, driven by what the consumers need.

## 10. Project goals and the Internet Archive plan (set by the author, 2026-11-13)

**Goals.** (1) The cleaned corpus and parsed output serve later projects. (2) The techniques, learnings and algorithms inform how to find and process a replacement data source. (3) Solving description parsing is a learning exercise in NLP/ML for the author, so the method matters as much as the result.

**Meaning of "original".** An original is a file as published by the source (Diamond / Previews World), not a copy edited by the author. Publisher updates are not a problem: staff and customers reviewed the files and Diamond may have corrected errors, so a later published version can be the better one. The author's own hand edits (the files in the earlier repos) are the thing to avoid. If a month has several published versions, keep all of them and compare, rather than assuming the first or the last is right.

**Data plan.** Find every published COF text file, and the PDFs where possible (the PDFs carry more detail and can verify the text files), in the Internet Archive. Keep them as downloaded, with a manifest. Build rules from the known quirks that normalize a downloaded file into a clean COF file. All further processing starts from the clean files.

**Pipeline principle.** The corpus is finite, so format drift is not a risk, but the code should still behave like a pipeline: staged, re-runnable, config-driven, with immutable inputs and explicit unknowns reports, building on the good patterns in the earlier repos.

**Three URL eras (from the comments in the 2013 PHP script `pp.php`, then checked against the archive index).**
1. `previewsworld.com/support/previews_docs/orderforms/MMMYY_COF.txt` (and `.pdf`): the current-month location.
2. `.../orderforms/archive/2013/JAN13_COF.txt` and `.../orderforms/archive/2009/JAN09/JAN09_COF.txt`: where older forms were moved. The year folder, and for 2009 a month folder, are part of the path.
3. `previewsworld.com/Catalog/CustomerOrderForm/TXT/MMMYY` (and `/PDF/`): the later site, which the 2020 and 2023 download scripts used.

The 2023 pandas repo's `README.md` repeats the same three formats, using these example links: `.../orderforms/MAR13_COF.txt`, `.../orderforms/archive/2013/JAN13_COF.txt`, `.../orderforms/archive/2009/JAN09/JAN09_COF.txt` and `/Catalog/CustomerOrderForm/TXT/JUL23`. It adds a listing page, `previewsworld.com/Catalog/CustomerOrderForms`, which listed forms back to JAN 2017 (the author noted that older files might exist but not be listed there). The Wayback index has about 580 captures of that listing page, from 2016 to 2026, so the lister can read it at several dates to see which months were linked and where.

The earlier repos have no further notes about the site's archive area beyond those. The local `Archive.zip` and `Archive 2` files in the 2016 repo are the author's own copies and are unrelated.

**Probe of the Wayback Machine CDX index (2026-11-13; index queries only, no files downloaded or opened).** Counting entries that report a 200 status, the right file type and a plausible size:

| | Text | PDF |
|---|---|---|
| Era 3 only (first probe) | 183 months | 183 months |
| Eras 1 and 2 only | 90 months | 89 months |
| All three eras combined | 195 months | 195 months |
| Of the 135 corpus months (JAN09–MAR20) | 134 | 135 |
| Corpus months not found | DEC16 | none |
| After MAR20 | 61 months; missing MAY20, NOV21, DEC21, APR23, AUG23 | 60 months; missing MAY20, NOV21, DEC21, JUN22, JAN23, AUG23 |

The old paths supply all 12 months of 2009 for both text and PDF, which the first probe missed. Every month through MAR20 has a PDF.

Things to keep in mind:
- These are index entries, not verified files. Each downloaded file must be checked against the expected layout and, for months in the current corpus, compared with the existing copy.
- The index query kept one capture per URL. Months can have several captures, and several URL spellings, so the lister should record all of them and compare their content.
- Some entries were redirects (301/307) or 404s and were excluded.
- Index requests sometimes return an "Internet Archive: Temporarily Offline" page. A retry worked. The downloader needs retries, backoff, rate limits and a log of what was fetched.

**Consequences for the plan.**
- The existing copies are no longer the only source for any month except possibly DEC16. They become a comparison reference.
- Corpus growth to about AUG25 changes the format-drift assumption: the "no new drift" claim holds only for JAN09–MAR20 until the later files are measured.
- The PDFs give a second source: parse a sample, and compare item counts and fields with the text files.

**Next steps (not started):** (a) a read-only CDX lister covering all three URL eras and recording every capture per month in a manifest; (b) fetch a pilot set, including the two files already found (`TXT/JUL23`, `PDF/JAN18`), and compare with the spec's layouts; (c) decide the storage layout for downloaded files and the manifest.
