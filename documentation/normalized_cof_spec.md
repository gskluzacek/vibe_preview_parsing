# Normalized COF: the target specification

What a clean COF text file looks like, and which rule turns each published defect into that form. The normalizer (`cof-normalize`, stage 2 of the pipeline) is written and tested against this document.

Two other documents describe the *input*:
- `original_files_analysis.md`: what is actually in the published files (measured, 232 files).
- `cof_format_spec.md`: the older description of the author's edited corpus (JAN09–MAR20).

The authoritative rule list is `config/rules.yaml`. Each rule has a detector with the same id (`src/cof/normalize/detectors.py`), and a test keeps the two in step. The table in section 5 is a copy for reading.

## 1. Principles

1. **Never touch the originals.** Files under `data/originals/` are as downloaded. Normalized files are new files.
2. **Fix structure and encoding, not content.** Product names, descriptions, prices and dates are kept as published, except where the rule below says a form is rewritten to its canonical spelling without changing its meaning. Typos in descriptions are never corrected.
3. **One line in, one line out.** The normalizer never adds, removes, merges, splits or reorders lines. A normalized file has exactly as many lines as the decoded source. (Tests enforce this.)
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
| Final newline | Exactly one LF ends the file. Blank lines at the end of the source are kept |
| File name | `YYYY_MM.txt` (for example `2013_01.txt`), so a directory listing sorts chronologically. The month comes from the source file name |

The facts found here (original encoding, compression, line-ending style, count of non-ASCII bytes) are recorded in `summary.csv` for each file.

## 3. Structure of a normalized file

A file is a sequence of lines of these types (classification algorithm: `src/cof/normalize/classify.py`, first match wins):

`BLANK`, `PAGE` (`PAGE n` or `PAGE M-n`), `NOTE` (`(NOTE: ...)`), `IDENT`, `ITEM`, `FOOTER` (the last non-blank line if it is a bare number), `ANNOTATION` (`[...]`), `HEADING`, `UNKNOWN`.

- Non-item lines (headings, PAGE lines, notes) have **no trailing tabs or spaces** (L01).
- The **ident line** (the first lines before the first PAGE line) is kept as published when it is consistent with the file name. When the month, volume or issue disagrees with the file name, they are replaced by the values derived from the file name, in the same form (F07, F08). A missing ident line is **not** invented (F06).
  - Derivation: volume = year − 1990; issue in volume = month number; catalog issue number = (volume − 1) × 12 + month + 27 (verified JUN19 to MAR20 only).
- Page numbers and heading levels are not corrected or interpreted at this stage.

### Item lines

Seven tab-separated fields:

| # | Field | Normalized form |
|---|---|---|
| 0 | flag | empty, or a known flag (`SS`, `SPOT`, `OA`, `FI`, `KIDS`, `GEM`, and the combinations seen). Unknown flags are kept and reported (I13) |
| 1 | sol code | `^[A-Z]{3}\d\d \d{4}$`. A missing space is inserted (I05). Other forms are kept and reported (I06). A month that differs from the file name is allowed (I07) |
| 2 | text | as published, with leading and trailing whitespace trimmed (I14) and CSV quoting removed (I20). Never otherwise changed |
| 3 | release date | empty or `mm/dd/yy`. `m/d/yyyy` forms are rewritten (I11). A date that is not valid is kept and reported (I12) |
| 4 | price | `SRP: $n.nn`, `MSRP: $n.nn`, `SRP: PI`, `MSRP: PI`, `SRP: FREE` or a bare `$n.nn`; surrounding whitespace trimmed (I19), quoting removed (I20), a missing space after the colon inserted (I09). Thousands separators (`$1,094.99`) are kept as published. Other forms are kept and reported (I10) |
| 5 | tail | exactly ` = $` (I04) |
| 6 | trailing empty field | empty |

Layout variants are converted to this form: 6 fields without the trailing field (I01), 8 fields with an empty field after the sol code (I02), 6 fields with no date (I03). An item line that fits none of them is kept and reported (I16).

**Placeholder items.** The publisher left items whose text is `DO NOT ORDER FROM THIS LINE` in some files, sometimes with only three fields (`flag`, sol code, text). They are kept exactly as published (L06). Downstream code should drop them by their text. Padding them to seven fields would invent data.

## 4. Open and informational rules

Left as published and reported, never silently changed:

- **Foreign layout (F01):** a file that is not a COF text file (a header row of column names). It cannot be normalized and must not be chosen for its month.
- **Unknown values:** flags (I13), prices (I10), sol codes (I06), unclassified lines such as `??` (L07), a damaged PAGE line like `GE 24` (L02), PAGE numbers ≥ 1000 (L03), duplicate sol codes (I08), the replacement character (I15).
- **Informational:** a missing ident line (F06), NOTE lines (L04), bracketed annotations (L05), numeric-only lines (L08), `DO NOT ORDER` placeholders (L06), sol month differing from the file name (I07), unbalanced parentheses (I17), double spaces (I18).

A **patch list** (`config/patches.yaml`, to be created when needed) can record a specific reviewed edit (file, line, old text, new text, reason) for an open issue, such as restoring a damaged character. Patched issues are reported as `patched`, not `fixed`.

## 5. Rule table

Classes: **auto-lossless** (fixed, nothing lost), **auto-derived** (fixed with a value computed from a trusted source), **open** (reported, not fixed), **info** (noted only).

| Rule | Issue | Class | Action |
|---|---|---|---|
| F01 | foreign layout | open | none; the file cannot be selected |
| F02 | mixed line endings | auto-lossless | all LF (standard transform) |
| F03 | bare `\r` inside a line | open | none |
| F04 | byte undefined in Windows-1252 | open | replaced by U+FFFD; needs a patch |
| F05 | truncated gzip stream | open | partial content; prefer another version |
| F06 | ident missing | info | kept as published; period comes from the file name |
| F07 | ident month wrong | auto-derived | month from the file name |
| F08 | ident volume or issue wrong | auto-derived | numbers from the file name |
| F09 | footer missing | open | none |
| F10 | empty file | open | none |
| L01 | trailing whitespace on non-item line | auto-lossless | trimmed |
| L02 | damaged PAGE line | open | none |
| L03 | page number ≥ 1000 | open | none |
| L04 | NOTE line | info | kept |
| L05 | bracketed annotation | info | kept |
| L06 | `DO NOT ORDER` placeholder | info | kept |
| L07 | unclassified line | open | none |
| L08 | numeric-only line | info | kept |
| I01 | layout B | auto-lossless | add the empty trailing field |
| I02 | layout C | auto-derived | drop the empty field |
| I03 | layout D | auto-derived | insert an empty date |
| I04 | odd tail | auto-lossless | ` = $` plus empty field |
| I05 | sol code without space | auto-derived | insert the space |
| I06 | sol code malformed | open | none |
| I07 | sol month differs from file | info | kept |
| I08 | duplicate sol code | open | none |
| I09 | price without space | auto-lossless | insert the space |
| I10 | price unrecognized | open | none |
| I11 | date `m/d/yyyy` | auto-derived | rewrite as `mm/dd/yy` |
| I12 | invalid date | open | none |
| I13 | unknown flag | open | none |
| I14 | text edge whitespace | auto-lossless | trimmed |
| I15 | replacement character | open | needs a patch |
| I16 | unknown item layout | open | none |
| I17 | unbalanced parentheses | info | kept |
| I18 | double space | info | kept |
| I19 | price edge whitespace | auto-lossless | trimmed |
| I20 | CSV-quoted field | auto-lossless | quotes removed, `""` becomes `"` |

## 6. Outputs of a run

| File | Content |
|---|---|
| `data/normalized/YYYY_MM.txt` | the clean file, one per month, from the selected version only |
| `data/normalized/issues.csv` | one row per issue: file, rule, line, class, status (`fixed`, `open`, `patched`, `info`), before, after, how |
| `data/normalized/summary.csv` | one row per file: source month, source digest, original encoding, compression, line-ending style, line count, counts of fixed / open / info issues |

## 7. Post-conditions (checked on every run)

1. The output decodes as strict UTF-8, has no BOM, no `\r`, and ends with exactly one LF.
2. The output has the same number of lines as the decoded source.
3. Running the detectors on the output reports **no issue for any rule fixed automatically**.
4. Normalizing the output again gives identical bytes (idempotent).
5. Every issue found in the source is accounted for in `issues.csv` as fixed, open, patched or info.

## 8. Decisions made here that the author may want to change

- **Ident line policy** (section 3): keep when consistent, correct from the file name when not, never invent. An alternative is to always write one canonical ident line for every month.
- **Thousands separators and the bare `PI` price** are left as published and reported. An alternative is to canonicalize prices to a number plus a flag.
- **Placeholders** stay three-field lines.
- **Carried-over sol codes** (I07) are informational, not corrected, because the code is the item's original solicitation.
