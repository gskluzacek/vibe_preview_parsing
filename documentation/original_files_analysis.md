# Analysis of the originals (as published)

Analysis of every text file downloaded from the Internet Archive: 232 files (distinct content versions), covering 199 months, JAN09 to OCT25. Run on 2026-11-16 with the detectors in `src/cof/normalize/detectors.py`.

This document supersedes `cof_format_spec.md` wherever they differ. That spec was measured on the author's 135 edited UTF-8 files (JAN09–MAR20). These are the files as published, and 61 of the months (APR20 onward) were never measured before.

Reproduce with:

```bash
uv run python adhoc/compare_versions.py     # data/originals/version_diffs.csv
uv run python adhoc/analyze_originals.py    # data/original_analysis/{issues,files,rules}.csv
uv run python adhoc/compare_with_corpus.py  # data/original_analysis/corpus_{comparison,diffs}.csv
```

## 1. Summary

- 232 files, 564,281 item lines (about 489,000 when one version per month is counted). 202 files have no errors or warnings.
- Detection found 31,556 issues of 37 kinds. Most are the known layout variants (JAN13/JUL13, FEB09, MAR09/APR09) and the newer 2023–2025 variants (trailing spaces in prices).
- **The corpus is faithful.** 133 of the 135 corpus months are line-for-line identical (ignoring encoding and line endings) to one published version. The only differences are three damaged POKÉMON lines (JAN09 lines 5489 and 5613, JUN17 line 3977).
- **So the spec's "hand edits" are mostly publisher defects.** The ident-month errors (A14), the tab-padded JAN13/JUL13 lines (A4) and the `DO NOT ORDER FROM THIS LINE` line (A6) all exist in the archive copies.
- **Format drift does exist**, but only in the 2021–2025 files and only in small ways (section 6). One archive capture is a different export format altogether.

## 2. How the files are stored

| Property | Files | Notes |
|---|---|---|
| Windows-1252 text | 143 | `0xC9` is É, `0xB7` is `·`, `0x97` is an em dash. No byte undefined in Windows-1252 occurs |
| Plain ASCII | 70 | no non-ASCII character at all |
| **gzip stream, Windows-1252 inside** | 17 | the archive stored the file still compressed, with no header saying so: JAN24–SEP25, 17 months. Decompressed, they are identical to the plain copies |
| UTF-8 with byte-order mark | 1 | DEC15 |
| **UTF-16 with byte-order mark** | 1 | JUN17 (the only capture of that month) |
| Line endings | all CRLF | no mixed endings and no stray `\r` once UTF-16 is decoded |

The published encoding is therefore **not** uniform. The decoder detects it (UTF-16/UTF-8 byte-order mark, gzip magic, strict UTF-8, then Windows-1252) and records what it found per file.

## 3. Months with more than one version (32 months)

| Group | Months | What differs |
|---|---|---|
| Same content, one copy gzip-compressed | 17: JAN24 to SEP25 | nothing |
| Ident line changed | 7 changes in 5 months: AUG10, JAN12, JAN13, FEB13 (two changes), JUN14 | see below |
| Blank line added or removed | OCT10, JAN11, AUG12, NOV13 | one blank line |
| Ident added or removed | AUG17 (removed), JUN19, JUL19, AUG19 (two-line "ISSUE #" form added) | 1–3 lines |
| **Item added** | MAR12 | `MAR12 0575 OPT IN FOR USER PASSWORD CUSTOMIZED SPIDER-MEN #1` appears in the later version, with a PAGE line |
| **Different export** | NOV23 | the first capture (2023-10-21) is a tab-delimited export with a header row (`PreviewsVolumeNo`, `PreviewsNo`, `OrderFormItemNo`, ...) and items coded `OCT230001`; it is not a COF text file |

**Later is not reliably better.** Ident lines changed in both directions: AUG10 `JULY` to `AUGUST` (right), JAN13 `DECEMBER` to `JANUARY` (right), JAN12 `JANUARY` to `DECEMBER` (wrong), FEB13 `FEBRUARY` to `DECEMBER` to `FEBRUARY VOL. 22` (wrong volume). A rule such as "prefer the later version" would be wrong. Because the ident line is derived from the file name, these differences do not matter for the choice. The MAR12 item addition shows a later version can be more complete.

## 4. Issues found, by rule

Class: `auto-lossless` / `auto-derived` can be fixed by the normalizer; `open` needs a human or a patch; `info` is recorded only. Full definitions: `config/rules.yaml`.

| Rule | Name | Class | Files | Issues | Months (examples) |
|---|---|---|---:|---:|---|
| F01 | foreign layout | open | 1 | 1 | NOV23 (first capture) |
| F06 | ident missing | open | 91 | 91 | the 8 files in the spec, JUN19–AUG19 (first captures), and every month from JUN20 on except JUL20 |
| F07 | ident month mismatch | auto-derived | 12 | 12 | APR09 MAY09 JUN09 JUL09 SEP09 JAN10 AUG10 JAN12 JAN13 FEB13 JAN14 JUN14 |
| F08 | ident volume/issue mismatch | auto-derived | 2 | 2 | FEB13 (`VOL. 22`), JUL14 (`#6`) |
| F09 | footer missing | open | 1 | 1 | NOV23 (first capture) |
| L01 | trailing whitespace on non-item lines | auto-lossless | 5 | 2,143 | JAN13, JUL13, SEP23, DEC23 |
| L02 | damaged PAGE line | open | 1 | 1 | NOV14 line 4 `GE 24` |
| L03 | implausible page number | open | 1 | 2 | FEB20 `PAGE 2999`, `3000` |
| L04 | NOTE line | info | 9 | 10 | |
| L05 | bracketed annotation | info | 1 | 1 | JAN14 |
| L06 | `DO NOT ORDER FROM THIS LINE` placeholder | info | 4 | 21 | JAN09 (4), JUN13 (1), AUG25 (8, two versions) |
| L07 | unclassified line | open | 2 | 8 | `??` lines in JAN20 and DEC21 |
| L08 | numeric-only line (not footer) | info | 5 | 5 | the heading `300`: MAY14 SEP16 DEC16 MAY17 SEP17 |
| I01 | layout B (no trailing empty field) | auto-lossless | 13 | 6,695 | JUL11 JAN13 JUL13 JAN19 and SEP23–MAY24 |
| I02 | layout C (extra empty field) | auto-derived | 2 | 5,131 | FEB09, SEP15 |
| I03 | layout D (no date) | auto-derived | 2 | 1,424 | MAR09, APR09 |
| I04 | odd tail | auto-lossless | 1 | 1 | MAR18 line 864 |
| I05 | sol code without space | auto-derived | 4 | 4 | AUG13 MAY15 JUL15 SEP15 |
| I06 | sol code malformed | open | 2 | 2 | `STAR1 7580` in SEP23 and DEC23 |
| I07 | sol month differs from file | info | 25 | 5,358 | see section 6 |
| I08 | duplicate sol code | open | 5 | 9 | SEP16 NOV16 DEC18 FEB24 |
| I09 | price without space after colon | auto-lossless | 1 | 1 | AUG13 line 2766 `SRP:PI` |
| I10 | price unrecognized | open | 1 | 8 | JAN22: bare `PI` |
| I11 | four-digit-year date | auto-derived | 3 | 5,788 | JAN13, JUL13 |
| I13 | unknown flag | open | 5 | 14 | `BL` (AUG24, 10), `S` (SEP25, 2), `SS FI` (JUN12), `FO` (SEP19) |
| I14 | text edge whitespace | auto-lossless | 27 | 100 | |
| I17 | unbalanced parentheses | info | 45 | 65 | |
| I18 | double space in text | info | 5 | 7 | |
| I19 | price with edge whitespace | auto-lossless | 15 | 4,642 | MAY23 onward (`SRP: PI `) |
| I20 | CSV-quoted field | auto-lossless | 6 | 9 | JUL13, JUN23, JAN24, MAR24 |

Rules F02–F05, F10, I12 and I15 (mixed endings, bare `\r`, undefined bytes, truncated gzip, empty file, invalid dates, replacement characters) found nothing in the originals.

## 5. Findings that correct `cof_format_spec.md`

| Spec statement | What the originals show |
|---|---|
| "All 135 files are strict UTF-8" | True only of the author's conversions. The published files are Windows-1252, UTF-16 (JUN17), UTF-8 with BOM (DEC15), or gzip-compressed |
| A6: JUN13:2000 is a hand-added line | It is in the archive copy. "DO NOT ORDER FROM THIS LINE" is a publisher placeholder, also seen in JAN09 (4 lines, with full item fields) and AUG25 (8 lines) |
| A4, A14: JAN13/JUL13 padding and stale ident months are hand-typed originals | They are publisher defects, present in the archive. The ident month was later corrected in some captures (JAN13), wrongly changed in others (JAN12, FEB13) |
| A22: damaged POKÉMON bytes | Correct in the corpus only; the archive copies hold a proper É (`0xC9`) |
| Sol-code month equals the file month except JUN17:3473 | Holds through 2020. From 2021 on, carried-over items keep their original code (`JAN23 2053` inside OCT23): 5,358 lines in 25 files. Not a defect |
| Layout A-D only | New in 2023–2025: layout B lines with a trailing-space price; a 3-field placeholder; thousands separators in prices (`$1,094.99`); CSV-quoted fields |
| Flags: 15 values | New flags `BL` (AUG24) and `S` (SEP25) |
| Ident forms A-D exist throughout | The ident line is missing from most months after MAR20: only APR20 and JUL20 still have the two-line form; every other month from JUN20 to OCT25 has none |
| JUN17 is a normal file | Its only capture is UTF-16; the corpus copy is a UTF-8 conversion |

## 6. The 2021–2025 files (never measured before)

- Layout A with the same fields. Layout B items appear in SEP23 to MAY24, mostly with a trailing space inside the price field.
- Ident line gone from most months after MAR20 (APR20 and JUL20 still have it).
- Carried-over items with an older month code (I07); not a defect.
- Prices: thousands separators, CSV quoting, a bare `PI`.
- New flags `BL`, `S`.
- Sol code `STAR1 7580` (SEP23, DEC23), and `??` lines (JAN20, DEC21).
- Foreign export in the first NOV23 capture. This changes the "no format drift" assumption: a month's file can hold a different export format, so each file must be checked.

## 7. Items for the target spec and later work

- Decide the handling of the open rules: bare `PI` price, flags `BL`/`S`/`FO`/`SS FI`, `STAR1` sol codes, `??` lines, damaged PAGE line.
- The ident line: keep the published text when it matches the file name, correct month/volume/issue when it does not (rules F07, F08), and do not invent one when it is missing (F06).
- Meaning of the flags and of `M-` pages is still unconfirmed.
- Whether the post-MAR20 months (never in the corpus) should be part of the normalized set. They are in the plan: yes.
