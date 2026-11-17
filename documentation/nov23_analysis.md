# NOV23 in detail, and where the tab and field-count problems are

Measured on 2026-11-17 from `data/originals/` (as downloaded) and `data/normalized/issues.csv`. "Fields" means tab-separated fields on item lines; the canonical item has 7.

## Short answer

- NOV23 looks troublesome because its **first capture is not a COF at all**, and because its selected file belongs to a group of 2023–24 months with a different tab layout. By the numbers it is not the worst month: 475 issues that needed action, 7th of 199 (see the ranking below).
- **Field-count differences** (an item line that does not have exactly 7 fields) occur in **14 months** of 199 once the 3-field `DO NOT ORDER` placeholders (AUG25, JUN13) are set aside. Counting the placeholder months, 16 months and 21 of the 232 downloaded files.

## The two NOV23 text captures

| | capture 2023-10-21 (not used) | capture 2024-04-12 (selected; same bytes recaptured 2024-11-04) |
|---|---|---|
| Layout | tab-delimited export with a header row: `PreviewsVolumeNo, PreviewsNo, OrderFormItemNo, OrderFormItemDesc, CountryCode, CountryDesc, ItemClass, Description` | the normal COF text layout |
| Size | 2,567 lines (2,566 data rows), 8 fields on every row | 3,029 lines, 657 blank; items: 2,303 with 7 fields, 69 with 6 |
| Content | volume 33, issue 10 on every row, codes `OCT230001`…: this is the **October 2023** order form (Previews #423, December 2023 issue), served at the NOV23 address | NOV23 codes (1,964 items) plus carried-over items from 34 other months |
| Extra columns | country of origin (`*USA` 1,342; CANADA 717; CHINA 366; HONG KONG, KOREA, ENGLAND, MEXICO, … ) and a numeric item class with a description (`382`, `361`, `247`, …): customs/tariff-style data, not in any other COF | none |
| Verdict | rejected by rule F01 (foreign layout); `F09` (no footer) also fires | accepted |

The first capture is therefore the wrong month's data in a different export format, not a damaged NOV23. It was never selected, but its existence is the reason `F01` and the per-file layout check exist.

## What is wrong with the selected NOV23 file

| Rule | Lines | What |
|---|---|---|
| I07 | 408 | the sol code's month differs from the file name: carried-over items (JAN23 55, JAN22 51, MAR22 31, DEC21 29, …) keep their original code; normal from 2021 on |
| I19 | 405 | whitespace after the price (`SRP: $18.00 `, `SRP: PI `) |
| I01 | 69 | item lines with 6 fields: the last tab is missing (lines 1913–1986, all merchandise carried over from earlier months, e.g. `JUL23 2153 IRONGUARD ONE-TOUCH …`) |
| F06 | 1 | no ident line |
| I14, I17 | 1 each | edge whitespace in a text; unbalanced parenthesis |

Everything but the I07 and F06 notes is repaired automatically; nothing is open.

## All files with field-count differences

(Original files, item lines only; `selected` / `only_version` are the ones that reach the normalized set.)

| Month | Capture | Role | Item lines by field count | Cause |
|---|---|---|---|---|
| FEB09 | 2011-12-20 | only | 8 × 5,123 | extra empty field after the sol code (layout C, I02) |
| MAR09 | 2011-12-20 | only | 7 × 3,531, 6 × 1,390 | release date missing (layout D, I03) |
| APR09 | 2011-12-20 | only | 7 × 1,623, 6 × 34 | release date missing (I03) |
| JUL11 | 2012-03-13 | only | 7, 6 × 2 | missing trailing field (I01) |
| JAN13 | 2012-12-16 and 2013-06-01 | not used, selected | 6 × 1,819 | tab-padded layout, no trailing field (I01) |
| JUL13 | 2013-06-18 | only | 6 × 2,198 | same padded layout as JAN13 |
| JUN13 | 2013-06-13 | only | 7, 3 × 1 | a `DO NOT ORDER` placeholder (3 fields) |
| SEP15 | 2015-08-22 | only | 7, 8 × 8 | extra empty field (I02) |
| JAN19 | 2021-05-12 | only | 7, 6 × 2 | missing trailing field |
| SEP23 | 2024-09-20 | only | 7, 6 × 70 | missing trailing field |
| OCT23 | 2024-02-29 | only | 7 × 2,546, 6 × 187 | missing trailing field |
| **NOV23** | 2023-10-21 | not used | 8 × 2,567 | foreign export (above) |
| **NOV23** | 2024-04-12 | selected | 7 × 2,303, 6 × 69 | missing trailing field |
| DEC23 | 2024-02-29 | only | 7 × 2,225, 6 × 71 | missing trailing field |
| JAN24 | 2024-01-16 and 2024-04-13 | not used, selected | 7 × 2,555, 6 × 71 | missing trailing field |
| MAY24 | 2024-04-26 and 2024-09-13 | selected, not used | 7 × 2,427, 6 × 158 | missing trailing field |
| AUG25 | 2025-08-05 and 2025-08-11 | selected, not used | 7 × 1,294, 3 × 8 | `DO NOT ORDER` placeholders |

The 6-field lines of SEP23–MAY24 are all carried-over items (their sol-code months are older than the file's); they come from the publisher's own export, so the absence of the last tab is a publisher defect, not a download artifact.

## Where the issues are (all 199 months, issues needing action or fixing)

JUL13 5,124 · FEB09 5,123 · JAN13 4,325 · MAR09 1,390 · OCT23 748 · SEP23 499 · **NOV23 475** · DEC23 385. The first four are the old layout variants (tab padding, extra field, missing date); the 2023 group is price whitespace plus missing last tab plus carried-over codes. Rule counts per month are in `data/normalized/issues.csv`.
