# Review of selection decisions and open issues

Reviewed 2026-11-17 (pending task 1 of the session handoff).

## Version selection (`data/originals/selection.csv`)

The 15 non-trivial decisions are the `fewer_defects` (11) and `later_version` (4) rows. In every case the selected version is the more complete or more correct one, so `config/selection_overrides.yaml` stays empty. The other `not_used` rows are `truncated` PDFs, `identical_content` copies, `superseded` PDFs and one `foreign_layout` file (NOV23), which need no review.

| Month | Reason        | Finding                                                                      | Decision |
| ----- | ------------- | ---------------------------------------------------------------------------- | -------- |
| AUG10 | fewer_defects | The unused capture has a wrong identification line (JULY for AUGUST).        | Accept   |
| OCT10 | later_version | The unused capture lacks one trailing blank line.                            | Accept   |
| JAN11 | later_version | The unused capture lacks one trailing blank line.                            | Accept   |
| JAN12 | fewer_defects | The unused capture says DECEMBER in the identification line.                 | Accept   |
| MAR12 | fewer_defects | The unused capture lacks `PAGE 24` and a data line.                          | Accept   |
| AUG12 | later_version | The unused capture has one extra blank line; the selected one is newer.      | Accept   |
| JAN13 | fewer_defects | The unused capture says DECEMBER in the identification line.                 | Accept   |
| FEB13 | fewer_defects | Two unused captures have a wrong month or volume in the identification line. | Accept   |
| NOV13 | later_version | Same capture date; the unused copy has an extra blank line.                  | Accept   |
| JUN14 | fewer_defects | The unused capture says MAY in the identification line.                      | Accept   |
| AUG17 | fewer_defects | The unused capture lacks the identification line.                            | Accept   |
| JUN19 | fewer_defects | The unused capture lacks the two identification lines.                       | Accept   |
| JUL19 | fewer_defects | The unused capture lacks the two identification lines.                       | Accept   |
| AUG19 | fewer_defects | The unused capture lacks the two identification lines.                       | Accept   |

## Open issues (`data/normalized/issues.csv`)

22 issues were open. After the review none is: 5 are patched (`config/patches.yaml`) and the rest are fixed or reported as info by rules.

| Month               | Rule | Line       | Finding                                                                                 | Decision                                 |
| ------------------- | ---- | ---------- | --------------------------------------------------------------------------------------- | ---------------------------------------- |
| NOV14               | L02  | 4          | `GE 24` is a damaged `PAGE 24` (next page line is `PAGE 25`)                            | Patch                                    |
| NOV16               | I08  | 3579       | Sol code `2862` is a typo for `2962` (neighbours 2961 and 2963)                         | Patch                                    |
| SEP25               | I13  | 53         | Flag `S` is undefined; the neighbours and the prior-solicit code point to `SS`          | Patch                                    |
| MAY11               | F11  |            | Publisher repeated #273 (APR11 has it too; JUN11 is #275); the correct value is #274    | Patch of both `PREVIEWS #273` items      |
| SEP16, DEC18, FEB24 | I08  | several    | A sol code repeated in the same file; the `-1`, `-2` suffix removes the ambiguity       | I08 is now `info`, not `open`            |
| MAR17               | L03  | 3002       | The `PAGE 12` line between two items of the same T-shirt series on page 501 is errant   | Patch: line 3000 made blank              |
| FEB20               | L03  | 2075       | `PAGE 2999` and `PAGE 3000` are pages 299 and 300 (checked against the printed catalog) | Patch of both PAGE lines                 |
| DEC23               | L03  | 2870       | The `M-` pages end and ordinary numbering resumes (404 after M-84)                      | Rule: a new section starts there; no L03 |
| JAN20, DEC21        | L07  | several    | Trailing `??` lines after the last item                                                 | New info rule L09; kept in the side-car  |
| SEP23, DEC23        | I06  | 2964, 2596 | `STAR1 7580` is the legacy SKU `STAR17580`, split by the form                           | New fixer I22: only the space is removed |

The FEB24 duplicates (`NOV23 7540`, `NOV23 7545`, `AUG22 8425`) are the same case as SEP16 and DEC18: each code occurs twice in the file. They are not a re-solicitation effect.

## Rule and pipeline changes made from the review

- `emit()` classifies lines from the repaired text, so a patch that changes a line's type (for example `GE 24` to `PAGE 24`) takes effect.
- A new `section` also starts where the `M-` pages end and ordinary numbering resumes (only DEC23 changes: lines 18 and 2871). L03 does not report the jump there.
- New rules: I22 (legacy `STAR` sol code, space removed, digits unchanged) and L09 (unclassified line after the last item, info). L07 now covers only lines before the last item. I06 accepts the legacy `STAR` form. I08 is `info`.
- The patch for MAR17 blanks the errant line; the issue record for it shows empty before and after values because the issue (line 3002) and the patch (line 3000) are on different lines.
- Tests: 181 pass; ruff and mypy are clean.
