# Normalized COF: the target specification

What a clean COF text file looks like, and which rule turns each published defect into that form. The normalizer (`cof-normalize`, stage 2 of the pipeline) is written and tested against this document.

Two other documents describe the *input*:
- `original_files_analysis.md`: what is actually in the published files (measured, 232 files).
- `cof_format_spec.md`: the older description of the author's edited corpus (JAN09–MAR20).

The authoritative rule list is `config/rules.yaml`. Each rule has a detector with the same id (`src/cof/normalize/detectors.py`), and a test keeps the two in step. The table in section 5 is a copy for reading.

## 1. Principles

1. **Never touch the originals.** Files under `data/originals/` are as downloaded. Normalized files are new files.
2. **Fix structure and encoding, not content.** Product names, descriptions, prices and dates are kept as published, except where the rule below says a form is rewritten to its canonical spelling without changing its meaning. Typos in descriptions are never corrected.
3. **Every source line is accounted for.** A normalized file is a table of rows, not a copy of the source's lines. Each row carries the number of the source line it came from (`0` for the one row that did not exist, the ident). Every source line is either kept as a row, dropped (page, blank and footer lines), moved to the side-car, or replaced (ident lines), and the ledger (`ledger.csv`) counts each by type. Lines are never merged, split or reordered. (Checked on every run.)
4. **Correct only with a trusted source.** A value may be replaced automatically only if it can be computed from something authoritative (the file name) or the change loses nothing (whitespace, quoting). Anything else is reported as an open issue and left as published.
5. **Report everything.** Every defect is listed per file with its line, its rule, what was done, and whether it is fixed or still open. The standard transform (section 2) is not a defect and is not listed as one; its facts are recorded per file.
6. **Deterministic.** The same input and rules always give byte-identical output. Outputs carry no timestamps.

## 2. The standard transform (applied to every file, not reported as an edit)

| Step | Rule |
|---|---|
| Decompress | If the bytes start with the gzip signature, decompress. A stream that ends early is recovered as far as possible and reported (F05) |
| Detect encoding | UTF-16 byte-order mark, then UTF-8 byte-order mark, then pure ASCII, then strict UTF-8, otherwise Windows-1252. Bytes Windows-1252 leaves undefined are replaced by U+FFFD and reported (F04) |
| Re-encode | Write **UTF-8, no byte-order mark** |
| Line endings | Convert to **LF**. Mixed endings (F02) and stray `\r` (F03) are reported |
| Final newline | Exactly one LF ends the file |
| File name | `YYYY_MM.txt` (for example `2013_01.txt`), so a directory listing sorts chronologically. The month comes from the source file name |
| Whitespace | Leading and trailing spaces and tabs are removed, every run of spaces or tabs becomes one space, and a stray `\r` inside a line becomes a space (never seen in the corpus). Not reported as defects |
| CSV quoting | `"..."` quoting is removed and `""` becomes `"` (also reported as I20) |
| Release date | `YYYY-MM-DD` (every date is in the 2000s) |
| Price | split into `price_designation` (`SRP`, `MSRP`, empty) and `price` (digits only, no `$`, no thousands separator, two decimals, e.g. `0.50`). `PI` and `AR` give an empty price, `FREE` gives `0.00` |
| Sol code | `MMMYY nnnn` becomes `YYYY-MM-nnnn-m`; `m` is `0` for the first occurrence of the code in the file and counts up for repeats. A malformed code is kept as published |
| Case | Flags, sol codes and price designations are upper case. Descriptions are **not** changed: 7% of them contain lower case, which is information for later text processing |

The facts found here (original encoding, compression, line-ending style, count of non-ASCII bytes) are recorded in `summary.csv` for each file.

## 3. Structure of a normalized file

The classifier (`src/cof/normalize/classify.py`, first match wins) sorts the source lines into `BLANK`, `PAGE` (`PAGE n` or `PAGE M-n`), `NOTE` (`(NOTE: ...)`), `IDENT`, `ITEM`, `FOOTER` (the last non-blank line if it is a bare number), `ANNOTATION` (`[...]`), `HEADING` and `UNKNOWN`. What happens to each:

| Source line | Fate |
|---|---|
| `IDENT` | replaced by one canonical ident row (kind `D`) |
| `HEADING` | row, kind `H` |
| `ITEM` | row, kind `I` |
| `PAGE`, `BLANK`, `FOOTER` | dropped; the page number moves into the `page` column of the rows that follow |
| `NOTE`, `ANNOTATION`, `UNKNOWN` (including numeric-only lines), "DO NOT ORDER FROM THIS LINE" placeholder items, items of unknown layout | side-car file, `data/normalized/sidecar/YYYY_MM.txt` (only written when non-empty) |

### The table (`data/normalized/YYYY_MM.txt`)

Tab-separated, UTF-8, LF, one header row, eleven columns on every row:

| # | Column | Content |
|---|---|---|
| 0 | `src_line` | 1-based line number in the decoded source; `0` for an ident row inserted into a file that had none; for a replaced ident, the number of its first line |
| 1 | `page` | number of the last PAGE line seen, without the `M-` prefix; `0` before the first PAGE line |
| 2 | `section` | starts at 1 and goes up by one whenever a PAGE number is lower than the previous one (the numbering restarts; the comics, then the merchandise and other parts are separate runs) |
| 3 | `merchandise_flag` | `1` when the last PAGE line was `PAGE M-n` (catalog merchandise pages, APR18 onward), else `0` |
| 4 | `kind` | `D` ident, `H` heading, `I` item |
| 5 | `flag` | empty or one or two codes such as `SS`, `OA FI` (see `flag_and_code_definitions.md`) |
| 6 | `sol_code` | `YYYY-MM-nnnn-m` |
| 7 | `text` | the heading text or the item description |
| 8 | `release_date` | `YYYY-MM-DD` or empty |
| 9 | `price_designation` | `SRP`, `MSRP` or empty |
| 10 | `price` | number with two decimals, or empty |

Headings and the ident row leave columns 5 and 6 and 8 to 10 empty. The old tail ` = $` and the trailing empty field are dropped (they never varied except in one line of MAR18). Heading levels are not interpreted at this stage (see `hierarchical_heading_parsing.md`).

### The ident row

Every file starts with one row of kind `D` with a canonical text, `PREVIEWS <MONTH> <YYYY> ISSUE #<catalog> (VOL. <volume> #<issue>)`, computed from the file name: volume = year − 1990, issue in volume = month number, catalog issue number = (volume − 1) × 12 + month + 27. An ident line in the source (one or two lines) is replaced by this row after the usual checks (F07, F08); when the file has none, the row is inserted with `src_line` 0 (F06 is still reported). The formula is cross-checked against the first `PREVIEWS #nnn <MONTH> <YEAR>` item of the month, which names the issue two months later (item number − 2 = formula; rule F11), and against the ident line when it carries the number. The formula agrees with the item in every file that has one except MAY11 (the item says #273, the formula implies #274), reported as F11; the derived number is used.

`data/normalized/idents.csv` records, per file: source encoding, the raw ident line(s), what they say (month, year, volume, issue, catalog), what the file name implies, the number from the first PREVIEWS item, and a yes/no/empty check for each comparison.

### The side-car (`data/normalized/sidecar/YYYY_MM.txt`)

Tab-separated with the columns `src_line, page, section, merchandise_flag, kind, text`; `kind` is `NOTE`, `ANNOTATION`, `UNKNOWN`, `PLACEHOLDER` or `UNPARSED_ITEM`. Tabs inside a moved line are shown as ` | `.

### The ledger (`data/normalized/ledger.csv`)

One row per file, line type and fate (`kept`, `dropped`, `sidecar`, `replaced`) with the number of source lines, so the lines removed or moved can be summarized by type.

## 4. Open and informational rules

Left as published and reported, never silently changed:

- **Foreign layout (F01):** a file that is not a COF text file (a header row of column names). It cannot be normalized and must not be chosen for its month.
- **Unknown values:** flags (I13), prices (I10), sol codes (I06), unclassified lines such as `??` (L07), a damaged PAGE line like `GE 24` (L02), PAGE numbers ≥ 1000 (L03), duplicate sol codes (I08), the replacement character (I15).
- **Informational:** a missing ident line (F06), NOTE lines (L04), bracketed annotations (L05), numeric-only lines (L08), `DO NOT ORDER` placeholders (L06), sol month differing from the file name (I07), unbalanced parentheses (I17), double spaces (I18).

Rules marked **optional** (column *Set* in section 5) have never fired on the selected set. They only run with `cof-normalize run --full-checks`. Moving a rule between the required and the optional set is a one-word edit (`optional: true`) in `config/rules.yaml`; `cof-normalize rules` lists both sets.

A **patch list** (`config/patches.yaml`, to be created when needed) can record a specific reviewed edit (file, line, old text, new text, reason) for an open issue, such as restoring a damaged character. Patched issues are reported as `patched`, not `fixed`.

## 5. Rule table

Classes: **auto-lossless** (fixed, nothing lost), **auto-derived** (fixed with a value computed from a trusted source), **open** (reported, not fixed), **info** (noted only).

| Rule | Issue | Class | Set | Description | Action |
|---|---|---|---|---|---|
| F01 | foreign layout | open | required | The file is not a COF text file (for example a tab-delimited export with a header row). | none; the file cannot be selected |
| F02 | mixed line endings | auto-lossless | optional | Some lines end with CRLF and others with LF. | all LF (standard transform) |
| F03 | bare `\r` inside a line | open | optional | A carriage return appears inside a line, not as part of a line ending. | replaced by a space in the final file (standard transform); never seen in the corpus |
| F04 | byte undefined in Windows-1252 | open | optional | The file contains a byte that Windows-1252 leaves undefined. | replaced by U+FFFD; needs a patch |
| F05 | truncated gzip stream | open | optional | The archive stored the file as a gzip stream that ends early; only part of the file was recovered. | partial content; prefer another version |
| F06 | ident missing | info | required | The file has no identification line before the first PAGE line. | kept as published; period comes from the file name |
| F07 | ident month wrong | auto-derived | required | The month named in the identification line differs from the file name. | month from the file name |
| F08 | ident volume or issue wrong | auto-derived | required | The volume or issue number in the identification line differs from the value derived from the file name. | numbers from the file name |
| F09 | footer missing | open | required | The last non-blank line is not a bare number. | none |
| F10 | empty file | open | optional | The file has no lines. | none |
| L01 | trailing whitespace on non-item line | auto-lossless | required | A heading or PAGE line is padded with trailing tabs or spaces. | trimmed |
| L02 | damaged PAGE line | open | required | A line looks like a PAGE line with its first characters cut off (for example 'GE 24'). | none |
| L03 | page number jump | open | required | A PAGE number is more than max_jump above the previous PAGE number. Going backwards is normal: the numbering restarts in every section. | none; the page is carried as published |
| L04 | NOTE line | info | required | A '(NOTE: ...)' line. | kept |
| L05 | bracketed annotation | info | required | A bracketed editor annotation line. | kept |
| L06 | `DO NOT ORDER` placeholder | info | required | An item whose text is 'DO NOT ORDER FROM THIS LINE' (a publisher placeholder, sometimes with only 3 fields). | kept |
| L07 | unclassified line | open | required | A line that is not blank, PAGE, NOTE, IDENT, ITEM, FOOTER, annotation or heading. | none |
| L08 | numeric-only line | info | required | A line holding only a number that is not the footer. | kept |
| I01 | layout B | auto-lossless | required | An item line has no tab after ' = $' (6 fields instead of 7). | add the empty trailing field |
| I02 | layout C | auto-derived | required | An item line has an extra empty field after the sol code (8 fields). | drop the empty field |
| I03 | layout D | auto-derived | required | An item line has no release-date field (6 fields, price in the date position). | insert an empty date |
| I04 | odd tail | auto-lossless | required | The end of an item line is not exactly ' = $' followed by an empty field. | ` = $` plus empty field |
| I05 | sol code without space | auto-derived | required | The sol code has no space between month/year and number (for example FEB138491). | insert the space |
| I06 | sol code malformed | open | required | The sol code does not match the sol-code pattern even after adding a space. | none |
| I07 | sol month differs from file | info | required | The month in the sol code differs from the file name. Normal from 2021 on (carried-over items keep their original code); a typo candidate in earlier files. | kept |
| I08 | duplicate sol code | open | required | The same sol code appears more than once in the file. | none |
| I09 | price without space | auto-lossless | required | A price has no space after 'SRP:' or 'MSRP:'. | insert the space |
| I10 | price unrecognized | open | required | The price does not match any known form (a bare PI, AR or FREE is known). | none; raw text kept in the price column |
| I11 | date `m/d/yyyy` | auto-derived | required | The release date uses a four-digit year or non-padded fields (m/d/yyyy). | rewrite as `mm/dd/yy` |
| I12 | invalid date | open | optional | The release date is neither empty nor a valid calendar date in a known form. | none |
| I13 | unknown flag | open | required | The flag field holds a value outside the known set. | none |
| I14 | text edge whitespace | auto-lossless | required | The item text has leading or trailing whitespace. | trimmed |
| I15 | replacement character | open | optional | The item or heading text contains U+FFFD (a lost character). | needs a patch |
| I16 | unknown item layout | open | optional | An item line does not fit any known layout. | none |
| I17 | unbalanced parentheses | info | required | The item text has unequal numbers of '(' and ')'. | kept |
| I18 | double space | info | required | The item text contains two consecutive spaces. | collapsed to one space in the final file (standard transform) |
| I19 | price edge whitespace | auto-lossless | required | The price field has leading or trailing whitespace (for example 'SRP: PI '). | trimmed |
| I20 | CSV-quoted field | auto-lossless | required | A field is wrapped in CSV-style double quotes, with inner quotes doubled (used when the field holds a comma or a quote mark). | quotes removed, `""` becomes `"` |
| I21 | price without designation | info | required | The price has no SRP or MSRP designation (a bare '$n.nn' or a bare 'PI'). | designation left empty |
| F11 | catalog number mismatch | open | required | The number in the first 'PREVIEWS #nnn' item, minus 2 (it names the issue shipping two months later), differs from the catalog number derived from the file name. | none; the number derived from the file name is used |

## 6. Outputs of a run

| File | Content |
|---|---|
| `data/normalized/YYYY_MM.txt` | the clean table, one per month, from the selected version only |
| `data/normalized/sidecar/YYYY_MM.txt` | lines moved out of the table (notes, annotations, unknown lines, placeholders) |
| `data/normalized/ledger.csv` | every source line counted by type and fate |
| `data/normalized/idents.csv` | identification facts and consistency checks per file |
| `data/normalized/issues.csv` | one row per issue: file, rule, line, class, status (`fixed`, `open`, `patched`, `info`), before, after, how |
| `data/normalized/summary.csv` | one row per file: source month, source digest, original encoding, compression, line-ending style, source lines, output rows, side-car rows, dropped lines, counts of fixed / open / info issues |

## 7. Post-conditions (checked on every run)

1. The repair stage keeps the line count, leaves no automatically repaired rule detectable, and is stable when repeated (the repaired text is normalized to itself).
2. Every source line is counted exactly once in the ledger; rows = kept lines + the ident row.
3. The table renders without tabs or line breaks inside values, decodes as strict UTF-8, ends with exactly one LF, and reads back to the same rows with eleven columns.
4. Every issue found in the source is accounted for in `issues.csv` as fixed, open, patched or info.
5. The same input and rules give byte-identical output.

## 8. Decisions

The policies that were open in the first version are settled:

- **Ident line:** always one canonical row built from the file name; the source ident is validated first and replaced.
- **Prices:** split into designation and number; thousands separators removed; bare `PI` gives an empty designation and price and is reported as info (I21), not an open issue.
- **Placeholders** go to the side-car.
- **Carried-over sol codes** (I07) keep their own year and month in `sol_code`; the file name is not imposed on them.
- **Page numbers** are carried as published (without `M-`); the old "1000 or more" rule became a jump check (L03, threshold 300 in `rules.yaml`) because the numbering restarts in every section and a legitimate gap can be over 200 pages.
