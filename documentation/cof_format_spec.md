# COF Format Specification (working draft)

Status: draft 1, 2026-11-13. A synthesis of the three earlier repositories plus **fresh measurements over the 135-file corpus** (JAN09 → MAR20).

Inputs: `analysis_previews.md`, `analysis_previews_parsing.md`, `analysis_previews_parsing_pandas.md` (this folder) and four read-only measurement passes (line structure, item fields, headings, description tokens) run by subagents against the data. Numbers marked **[V]** were produced by code run during this work. The numbers are only as good as those scripts; they have not been independently re-run by a second pass.

## 0. Conventions and confidence

| Tag | Meaning |
|---|---|
| **[V]** | Verified by running code over the corpus (counts given). |
| **[D]** | Documented in a source repo or notes, not independently verified here. |
| **[I]** | Inferred from data patterns; plausible, not proven. |
| **[U]** | Meaning unconfirmed. Do not rely on it without an authoritative source (Diamond documentation). |

"COF" = Previews World Customer Order Form, text version. Corpus = `previews_parsing/cof_files/MMMYY.txt`, 135 files, JAN09 → MAR20, no MAY20 (Diamond issued a combined May/June 2020 form [D]).

## 1. Corpus and encoding

### 1.1 Sources and coverage

| Source | Coverage | Note |
|---|---|---|
| `previews_parsing/cof_files/*.txt` | JAN09 → MAR20 (135 files, 29 MB) | The only complete set; files were converted/hand-edited |
| `previews/.../*_COF.txt` (2016 repo) | JAN09 → AUG14 (53 files) | Overlaps; **52 of 53 months are identical** to the 2020 set after normalizing (see 1.3) **[V]** |
| `previews_parsing_pandas` download scripts | JAN10 → AUG23 | No data committed; the only route to APR20 → AUG23 **[D]** |

Item lines in the 135 files: **≈328,800** **[V]** (328,795–328,801 depending on the predicate, see 3.2). By year **[V]**: 2009 29.5k · 2010 19.9k · 2011 22.8k · 2012 22.7k · 2013 26.1k · 2014 29.8k · 2015 30.7k · 2016 34.0k · 2017 35.6k · 2018 34.0k · 2019 35.5k · 2020 (Jan–Mar) 8.3k. *(The earlier "~100k items" figure in `analysis_previews.md` referred to the 2016 repo's smaller dataset and should not be quoted.)*

### 1.2 Bytes

- **Line endings:** 135/135 files are pure CRLF; no LF-only, lone CR, or mixed files **[V]**. Always strip `\r`.
- **Encoding:** all 135 decode as **strict UTF-8**, no BOM, no control characters other than TAB/CR/LF **[V]**. The `chardet`/`charset_normalizer` labels in the earlier repos (ISO-8859-1, cp1250, Windows-1252) are detector guesses and are wrong for these files. Decode as UTF-8.
- **Non-ASCII characters** **[V]**: `É` (64 occurrences, 46 files, e.g. POKÉMON), `·` (48, 24 files, from APR18 on, in `COMICS · GRAPHIC NOVELS · PRINT`), `’` (7), `È` (NOV09), `Ï` (APR14).
- **Damage from earlier re-encoding** (4 lines) **[V]**: JAN09 lines 5489 and 5613 read `POK…MON` (bytes E2 80 A6 where the original has É); JUN17 line 3977 has double-encoded `POKÃ‰MON`; one more `POKÃ‰MON` in the item text. Originals are the `*_original_txt` backups (JAN09 is Latin-1, JUN17 is UTF-16LE with BOM, DEC15 differs only by a BOM).
- **Caution on an earlier claim:** the token-measurement pass reported "18 items with mojibake" because it read the files as Latin-1. Those are valid UTF-8 characters (É, ’) read the wrong way, not 18 damaged items. Only the 4 lines above are actually damaged **[V]** (the discrepancy between the two passes was resolved by the strict UTF-8 decode).
- **End of file:** 133 files end with 6 blank CRLF lines; JAN13 and JUL13 end without them **[V]**.

### 1.3 Relationship to the 2016 repo's files

Normalized comparison (decode old as cp1252 and new as UTF-8, strip trailing whitespace, drop ident and blank lines): 52 of 53 identical; JAN09 differs by the two damaged POKÉMON lines. Raw differences are limited to the ident line (old = normalized `PREVIEWS APR VOL 19 #04`, new = original/hand-typed), blank lines, and encoding **[V]**. **Implication:** one canonical corpus is feasible; use the 2020 set (fixing the 4 damaged lines from the backups) and treat the 2016 set as redundant.

### 1.4 Hand edits already applied

The 2023 notes (`previews_parsing_pandas/data/cof_notes/cof_notes.md`) list manual edits made to the files (extra tab in FEB09, wrong ident months, DEC12 `PAGE 0` inserted, JAN13/AUG13 PAGE line moved, NOV14 `GE 24` repaired, JUN20 ident rewritten) **[D]**. It is **unclear which of those edits are present in the `previews_parsing/cof_files` copies** (the two repos kept their own file sets). See §8 for the recommended "pristine raw + patches" approach.

## 2. File-level structure

A COF is a sequence of lines. In order: optional identification text, then repeating blocks of `PAGE n` / heading lines / item lines, then a footer.

### 2.1 Identification ("ident") text

The first non-blank line(s) before the first PAGE line. Variants found **[V]**:

| Variant | Form | Files |
|---|---|---|
| A | `PREVIEWS <MONTH> VOL. nn #n` (month spelled out, or 3-letter in a few files) | 2011–2018, plus 4 files in 2019 |
| B | `PREVIEWS <MON> Vnn #n` | Apr/May/Jun/Jul/Sep/Dec 2009 and all of 2010 |
| C | `PREVIEWS ORDER FORM` followed by `<MON> Vnn #n` (terse) | OCT09, NOV09 |
| D | two lines: `PREVIEWS <MONTH> YYYY` then `ISSUE #nnn (VOL. nn #n)` | JUN19 → MAR20 (10 files) |
| none | first line is `PAGE n` | JAN09, FEB09, MAR09, AUG09, AUG17, MAR19, APR19, MAY19 (8 files) |

Fallback when no ident exists (from the 2023 code **[D]**): derive from the item row `PREVIEWS #nnn <MONTH YEAR> CUSTOMER ORDER FORM` near the top.

**Relation to the filename** (`MMMYY.txt`):
- Volume = `year − 1990` holds in **every** file that has an ident (19 for 2009 … 30 for 2020), zero exceptions **[V]**.
- Issue-in-volume `#n` equals the filename month in all files except JUL14 (`#6` instead of `#7`) **[V]**.
- The "catalog issue number" formula `(vol−1)×12 + month + 27` matches all 10 D-variant files (369–378) but is **untestable elsewhere** since only D carries the number **[V]**.
- Month text disagrees with the filename in 12 files **[V]**: APR09, MAY09, JUN09, JUL09, SEP09 say `MAR`; AUG10 says `JULY`; JAN10 says `DEC`; JAN12, JAN13, JAN14, FEB13 say `DECEMBER`. These are stale hand-typed originals; the 2016 repo's normalized idents are always consistent with the filename.
- **Rule:** the **filename is authoritative** for period; the ident text is a cross-check, not a source. (Matches the 2020/2023 repos' `fn_*` vs `txt_*` approach.)

**Period semantics** [D/I]: the file month is the order-form month. The item `PREVIEWS #nnn <MONTH YEAR>` refers to the catalog two months later (e.g. MAR13 file ↔ `PREVIEWS #296 MAY 2013`). Release dates are typically 1–3+ months after the file month. Model `order_period`, `catalog_issue`, and `release_date` separately.

### 2.2 PAGE lines

- Forms **[V]**: `PAGE n` (68,051 lines) and `PAGE M-n` (2,327 lines, **only in the 24 files MAY18 → MAR20**). No other forms apart from one damaged line (NOV14 line 4: `GE 24`). The pass over headings also tolerated an `S-` prefix in its regex, but the line pass found none; treat `M-` as the only verified prefix.
- **`M-` meaning is [U].** The 2023 notes say "merchandise pages"; the line pass observed that the `M-` run has its own numbering sequence and called it "Marvel's"; neither is confirmed by an authoritative source.
- Anchor the pattern (`^PAGE (M-)?\d+$`): 1,393 item titles contain "PAGE" (`80 PAGE GIANT`) and a heading-like line `BETTIE PAGE` exists (MAY12) **[V]**. No real heading begins with the word PAGE **[V]** (contradicts the "some headings start with page" note in the 2023 docs).
- **Position:** first PAGE is at line 1 in 8 files, line 3 in 30, line 4 in 75, line 5 in 19, line 6 in 1, line 9 in 1, and **line 28 in DEC12** (26 lines of non-blank text before it) **[V]**. No item precedes the first PAGE line in any file **[V]**.
- **Numbering is not a sequence key:** a front-matter run (first page 9–47) then a reset to 1–6, then forward jumps (171 jumps > 20), small backward steps (41), 3 duplicate consecutive pages (DEC14, DEC15, JAN19), typos (FEB20 `PAGE 2999`/`3000`) **[V]**. In the MAY18+ files the sequence resets again around the `M-` section (3 times in NOV19). Use page numbers only as a locator attribute on items.
- Sentinel convention from the 2023 notes **[D]**: page `0` = items before the first PAGE line (none occur in this corpus except DEC12-style cases), page `-1` = informational lines. Prefer `NULL` for "unknown".

### 2.3 Footer

The last non-blank line of **every** file (135/135) is a bare integer (e.g. JAN09 `143`, MAR20 `1`, DEC15 `70`), then 6 blank lines in 133 files **[V]** — [I] PDF-footer residue, not data. **Do not classify bare-number lines blindly:** a real heading `300` (the movie) appears in MAY14, SEP16, DEC16, MAY17, SEP17, and 140 stray numeric lines occur in body text (~56 distinct) **[V]**. Rule: the *final* non-blank line is the footer; treat other numeric-only lines as noise to log.

### 2.4 Other non-item lines **[V]**

- `(NOTE: …)` lines: 8 lines in 7 files (e.g. MAR09:2518, JAN11:6, NOV11:780). Detected by `^\(NOTE:`.
- One editor annotation: JAN14 line 7, `[GR: FREE COMIC BOOK DAY HORIZONTAL LOGO -- ALSO, A YELLOW BACKGROUND BEHIND FCBD ITEMS]`.
- One hand-added item: JUN13:2000 `\tJUN13 1650\tDO NOT ORDER FROM THIS LINE`.
- Interior blank runs: 138 (lengths 1–4). Blank lines are *not* a heading signal (only 0.4% of headings are preceded by one).
- No lowercase text and no other instruction text exist outside the `(Net)` token.

## 3. Line classification

### 3.1 Recommended algorithm (first match wins, after stripping `\r`)

1. **BLANK**: empty after trimming spaces/tabs.
2. **PAGE**: `^PAGE (M-)?\d+\s*$` (after stripping trailing tabs/spaces; JAN13/JUL13 pad PAGE lines with tabs).
3. **NOTE**: `^\(NOTE:`.
4. **IDENT**: only before the first PAGE line (or within the first 8 lines), matching one of the variants in 2.1.
5. **ITEM**: column 1 non-empty and matches the sol-code pattern (4.3), after trimming. Fall back to "non-empty column 1" so that malformed codes (e.g. `FEB138491`) are still flagged as items, then flagged as anomalies.
6. **FOOTER**: last non-blank line of the file, if numeric-only.
7. **HEADING**: any remaining non-empty line that has no tab content (trailing tabs allowed), contains a letter, and is not bracket-annotated (`[`…).
8. **UNKNOWN**: everything else (log; do not silently drop).

### 3.2 Why not "≥ 2 tabs"

Three item predicates disagree on 1,444 of ~441k lines **[V]**:
- 1,439 are **tab-padded headings** in JAN13 (701) and JUL13 (738), e.g. `PREVIEWS PUBLICATIONS\t\t\t\t\t` — these have ≥ 2 tabs but are headings (and PAGE lines).
- 1 is JUN13:2000 (hand-added 3-field line).
- 4 are items with a malformed sol code (`FEB138491` AUG13:2635; `FEB158476` MAY15:2916, JUL15:2899, SEP15:2700).

"Non-empty column 1" is the safest single predicate. In the other 133 files all three predicates agree **[V]**.

Line-class totals **[V]**: ITEM 328,801 · PAGE 70,378 · HEADING 35,393 (≈262/file) · BLANK 2,251 · IDENT 125 (+ a few remnants) · NOTE 8.

## 4. Item line grammar

### 4.1 Canonical layout (layout A, 318,223 lines)

Tab-separated, after stripping `\r`:

| Idx | Field | Rule |
|---|---|---|
| 0 | flag(s) | empty or space-separated tokens (4.2) |
| 1 | sol code | `^[A-Z]{3}\d\d \d{4}$` |
| 2 | sol text | uppercase text (§6); max 101 chars; never contains a tab |
| 3 | release date | empty, `mm/dd/yy`, or `m/d/yyyy` forms (4.4) |
| 4 | price | 4.5 |
| 5 | tail | literal ` = $` (all 328,799 parseable lines) |
| 6 | (empty) | trailing empty field before `\r` |

### 4.2 Layout variants **[V]**

| Layout | Fields (incl. trailing) | Lines | Where | Normalization |
|---|---|---|---|---|
| A | 7 | 318,223 | all files except below | none |
| B | 6 (no tab before `\r`) | 4,021 | all of JAN13 (1,819) and JUL13 (2,198); 2 lines each in JUL11 and JAN19 | none needed after dropping the empty last field |
| C | 8, empty field at index 2 | 5,131 | FEB09 (all 5,123 items); 8 lines in SEP15 | drop index 2 |
| D | 6, **date missing** (price in the date position) | 1,424 | MAR09 (1,390 of 4,921 items), APR09 (34) | insert empty date at index 3 |

Plus single-line exceptions: MAR18:864 tail is `\t = $\t \r` (tab-space) and JUN13:2000 (3 fields).

*(This corrects the earlier note that JAN13 lines were "missing a date": JAN13/JUL13 only lack the trailing empty field; their dates are present, in `m/d/yyyy` form.)*

Normalization (from the item-field pass): (1) drop the last field if empty; (2) if 7 fields remain and index 2 is empty, drop it (layout C); (3) if 5 fields remain, insert an empty date (layout D); then parse by position.

### 4.3 Flags (field 0) **[V counts / U meanings]**

15 distinct values (counts are lines; first/last = months seen):

| Flag | Lines | First → last |
|---|---|---|
| (empty) | 198,813 | JAN09 → MAR20 |
| `SS` | 50,069 | JAN09 → MAR20 |
| `SPOT` | 32,351 | JAN09 → MAR20 |
| `OA` | 18,149 | JAN09 → MAR20 |
| `FI` | 15,873 | JAN09 → MAR20 |
| `KIDS` | 11,433 | OCT10 → MAR20 |
| `GEM` | 1,772 | JAN09 → MAR20 |
| `OA SS` | 127 | JAN09 → MAR15 |
| `OA FI` | 67 | JUL09 → APR15 |
| `SS KIDS` | 64 | OCT10 → DEC14 |
| `OA SPOT` | 50 | JAN09 → MAR15 |
| `OA KIDS` | 20 | OCT10 → OCT14 |
| `SS SPOT` | 9 | JUL09 → OCT14 |
| `SS FI` | 1 | JUN12 only (line 2430) — likely a combination typo |
| `FO` | 1 | SEP19 only (line 2850) — possible typo of `FI` |

Grammar: `(OA|SS)? (SS|FI|SPOT|KIDS)?` or `SPOT|FI|KIDS|GEM`; combinations always put `OA`/`SS` first.

Data-derived relations **[V]**:
- `SS` lines carry a previous-solicitation code in parentheses in 99% (49,607 of 50,069): 47,599 as `(MMMYYNNNN)`, 2,008 as `(STARnnnnn)`.
- `OA` lines contain `(O/A)` in 99% (≈18,0xx of 18,150); `(O/A)` also occurs in ~1,056 lines without the `OA` flag. So the flag and the text token are largely redundant.
- `KIDS` carries a previous-sol code in only 2,045 of 11,433 lines; `GEM` lines are almost all comic titles; `FI` clusters under `PREVIEWS EXCLUSIVE WEAR`.
- **Meanings of SS / SPOT / OA / FI / KIDS / GEM are [U].** The relations above are suggestive ("SS" ↔ previously solicited; "OA" ↔ offered again) but they are *correlations*, not documentation. Store the raw flag string and derive nothing semantic from it until confirmed.

### 4.4 Sol code **[V]**

- 328,795 of 328,799 parsed items match `^[A-Z]{3}\d\d \d{4}$`.
- **Exceptions:** 4 lines without the space (`FEB138491` AUG13:2635; `FEB158476` in MAY15/JUL15/SEP15). The month prefix equals the filename month on all lines except JUN17:3473 (`FEB17 8885`).
- Normalized form used by earlier code: remove the space (`MAR130008`). Keep both.
- Numbers: not unique in 3 files (one duplicate pair each: DEC18 `0319`, NOV16 `2862`, SEP16 `3113`); mostly ascending with descents in AUG19, JAN19, JUN17, MAY18, NOV13, NOV16; every file has gaps (34,378 missing numbers overall). Typical low block starts at 1 (94 of 135 files), else 5 (14), 2 (3), 53 (3). 696 codes ≥ 5000 appear in only 4 files (JAN09, FEB09, MAR09 at end-of-file; JUN17). Max 8885. **Do not assume contiguity or uniqueness; the key is `(file period, sol code, line number)`.**
- A previous-solicitation code uses the same shape but is a **code, not a date**: `[A-Z]{3}\d{6}` (month + year + 4 digits), 49,900 items. Its lag behind the current month is 3–23 months for 46% and ≥ 24 months for 54%. Its 4 digits equal the item's own digits in only 93 cases (so it is not a self-reference) **[V]**. (Corrects the 2016 note "previous resolicitation date".) `(STAR\d{5})` is a second code family (2,021 items; 4.7% of 2009 items, near zero by 2020).

### 4.5 Release date **[V]**

| Form | Lines | Files |
|---|---|---|
| `mm/dd/yy` | 313,399 | all except JAN13, JUL13 |
| empty | 11,416 | all 135 files |
| `m/d/yyyy`, `m/dd/yyyy`, `mm/d/yyyy`, `mm/dd/yyyy` | 3,046 / 617 / 218 / 103 | JAN13 and JUL13 only |

Every non-empty value is a valid calendar date; no `TBD` or text. Two-digit years are 20xx. Blank dates: layout A with empty field 8,619; layout D 1,424; layout C 1,373; heaviest in MAR09 (1,390), FEB09 (1,373), JAN09 (1,337), NOV19 (213), MAY17 (181); 6,933 of them also carry a caution code. Store `NULL`, never a fabricated date (the 2014 PHP bug turned blank into a bogus date).

### 4.6 Price **[V]**

| Form | Lines |
|---|---|
| `SRP: $d+.dd` | 316,784 |
| `SRP: PI` | 8,565 |
| `MSRP: $d+.dd` | 3,414 |
| bare `$d+.dd` (no prefix) | 33 (FEB17 8, APR14 4, MAR09 3, …) |
| `SRP:PI` (no space) | 1 (AUG13:2766) |
| `SRP: FREE` | 1 (FEB12:387) |
| `MSRP: PI` | 1 (SEP17:14) |

Always exactly two decimals; no commas, ranges, or blanks; no `$0.00`; maximum 20000.00. Regex covering all but the one no-space line: `^(?:(?:M?SRP): (?:\$\d+\.\d\d|PI|FREE)|\$\d+\.\d\d)$` (use `SRP: ?` to cover 100%). `PI` ⇒ price not yet set ("please inquire") **[D]**. `(Net)` does not predict price form **[V]** (Net items have PI in 4,853 of 14,900 vs 3,141 non-Net).

### 4.7 Item text hygiene **[V]**

Never empty; 55 have trailing whitespace (DEC14 20, APR11 19, JAN11 16), 15 leading whitespace, 4 contain a double space; 4 are CSV-quoted with `""` for inch marks; 18 contain non-ASCII (valid UTF-8, see 1.2); 18 have unbalanced parentheses (likely source truncation, e.g. `(C: 1-1 (O/A) (C: 1-1-2)`).

## 5. Headings and hierarchy

### 5.1 Facts **[V]**

- **First heading is `PREVIEWS PUBLICATIONS` in all 135 files; the second is `PREMIER PUBLISHERS` in all 135.** `FREE COMIC BOOK DAY` is a *sub*-heading under PREVIEWS PUBLICATIONS (26 files, plus 2 with "…MERCHANDISE"), not a first heading (contradicts the 2023 README note).
- All heading text is uppercase; 2,056 distinct strings overall (~1,997 after removing ~59 noise strings); per year 392 (partial 2020) to 646.
- Frequency distribution: in 1 file 617; 2–5 files 615; 6–50 files 653; > 50 files 171; all 135 files 24. Many single-file strings are typos (`COLLECTED EDTIONS`, `DC UNIVESE: GREEN LANTERN`).
- Levels cannot be read from the text (no indentation; trailing tabs/spaces carry no meaning); only context determines them.
- Heading is *never* followed directly by a PAGE line in normal files (9 cases); preceded by a PAGE line 38.6%; preceded by another heading 5.1%.

### 5.2 Level structure

Combining the 2016 table (918 rows: 19 level-1, 803 level-2, 96 level-3, no level 4) and the hand-levelled JAN09 extract (316 rows: 21/243/21/27 at levels 1–4):

- Up to **4 levels**; the extra level arises from `… BACKLIST` nodes (the extract makes `DC COMICS BACKLIST` level 3 and its children level 4; the 2016 table puts them at 2 and 3). 277 of 310 leveled names agree between the two; 31 of the 33 disagreements are exactly this backlist shift **[V]**.
- A heading's identity is **name + path**, not name: 107 names occur more than once with different parents/levels (e.g. `COMICS` is level 1 and also level 2 under three parents; `MOVIE/TV` 10 times).
- The 2016 table is a **2013–2014 snapshot**: only 709 of 2,056 distinct corpus headings (35%) appear in it (73.8% of occurrences). The hand-levelled extract covers **JAN09 only**. No level assignment exists for later headings.

### 5.3 Repeated headings within a file

`COMICS` repeats in 111 files (the 2nd/3rd occurrences follow BOOKS / MAGAZINES and are level-2 children of those, not the level-1 section); `DESIGNER TOYS` in 39 files, `GAMES` 19, `APPAREL` 10, `INTERNATIONAL` 5, `PREVIEWS PUBLICATIONS` 6 (DEC10, JAN11, JUL12, DEC12, JAN13, AUG13) **[V]**. In the three contexts examined, the item-code sequence continues across the repeat — i.e. a repeat means "resume that section" **[I]**, consistent with the 2023 todo ("a repeated heading resets to the level at which it first occurred"). Only 3 of the 6+ cases were inspected.

### 5.4 Eras

- **2009 → Mar 2018:** level-1 order is stable-ish (76 distinct level-1 sequences). Typical sequence: PREVIEWS PUBLICATIONS, PREMIER PUBLISHERS, COMICS, BOOKS, COMICS, MAGAZINES, COMICS, INTERNATIONAL, TRADING CARDS, APPAREL, OTHER APPAREL, TOYS, DIAMOND SELECT TOYS & COLLECTIBLES, DESIGNER TOYS, STATUES & MODELS, IMPORT TOYS & MODELS, COLLECTIBLES & NOVELTIES, GAMES, DVDS & DIGITAL MEDIA.
- **April 2018 restructure** **[V observation / I cause]**: the level-1 `COMICS`, `BOOKS`, `MAGAZINES` sections vanish after MAR18 (`COMICS` appears last in APR19 only as stray repeats); items under PREMIER PUBLISHERS jump from ~880 (MAR18) to ~1,860 (APR18) and 2,000+/month, and COMICS items fall to 0 by MAY18. New heading `COMICS · GRAPHIC NOVELS · PRINT`. Items under PREMIER PUBLISHERS: 11,090 of 35,555 (2017) → 25,811 of 35,505 (2019). Cause (a Diamond catalog reorganization merging comics into one publisher list) is **inferred**, not documented.
- Other disappearances: `STATUES & MODELS` last AUG15, `DVDS & DIGITAL MEDIA` last JUL15, `TOYS` last MAY18, `INTERNATIONAL` last MAR18, `BOOKS & MAGAZINES` AUG09–DEC13, `WIZARD ENTERTAINMENT` JAN09–FEB11, `PREMIERE COLLECTIBLES` JAN09–APR13.
- Renames/aliases to handle: `DARK HORSE` ↔ `DARK HORSE COMICS` (flip around SEP17–APR18), `D. E./DYNAMITE ENTERTAINMENT` → `DYNAMITE ENTERTAINMENT` (APR18), `DC COMICS` → `DC ENTERTAINMENT` (SEP17+), `ACTION LAB ENTERTAINMENT` / `ACTION LAB - DANGER ZONE`, `VIZ MEDIA LLC`, etc.
- Items per level-1 section (full corpus): PREMIER PUBLISHERS 138,161 · COMICS (level 1, 2009–Mar18) 75,769 · APPAREL 18,002 · DESIGNER TOYS 16,948 · COLLECTIBLES & NOVELTIES 15,190 · IMPORT TOYS & MODELS 14,458 · OTHER APPAREL 9,839 · DIAMOND SELECT 9,776 · GAMES 7,562 · DVDS 5,262 · others < 2,500 each; 358 items before any level-1 heading (the PREVIEWS PUBLICATIONS area counted as 1,035 under its own heading). Comic-book items live under COMICS before Apr 2018 and under PREMIER PUBLISHERS after, and PREMIER is also where publishers like DC/Marvel sit in all years — so "comic" cannot be inferred from the level-1 heading alone.

### 5.5 Extraction rule

After removing BLANK/PAGE/NOTE/IDENT/ITEM/FOOTER, a remaining line that is all-caps, has a letter, and doesn't start with `[` is a heading. On JAN09 vs the hand-levelled extract this gives precision 1.0 / recall 1.0 (the one false positive without the all-caps/letter rule is the stray `143`). **Caveat:** the extract was almost certainly produced from the same non-item lines, so this is close to tautological; whole-corpus precision is unmeasured (noise is ~145 of 35,393 occurrences, 0.4%).

### 5.6 Level resolution (design)

Needs: (a) a curated, dated heading table keyed by path (valid_from/valid_to, from the 2020/2023 design), (b) a path search — try the longest prefix of the current path plus the heading down to the heading alone, pick the deepest valid match, and (c) the repeated-heading rule above, (d) an alias table for typos and renames, (e) a review queue for unknown headings. Discovery should be automatic; level assignment of *new* headings stays a human decision (as in all three prior repos), but it should be a small queue, not the 2,094 NOTFOUND rows of 2014.

## 6. Description text (`sol_text`) grammar

All **[V]** unless tagged. 328,797 items; 287,319 distinct texts (87%); length min 4, median 42, mean 41.5, p90 59, p99 71, max 101 (the max suggests source truncation **[I]**). Uppercase only (the only lowercase is `et` of `(Net)`). Punctuation is sparse: apostrophes stripped (33 left; a backtick stands in for one in 78 items: `YOU`RE`), commas almost absent (4). `-` (mostly caution codes), `#`, `/`, `&`, `:`, parentheses are the structural characters.

### 6.1 Token classes (items matching; share of corpus)

**Parenthesised metadata:**

| Token | Items | Notes |
|---|---|---|
| `(C: d-d-d)` caution | 157,501 (47.9%) | digit ranges {0,1}/{0,1}/{0..4}; **last parenthesis in 99.96%** and ends the string in 157,436; premier 11.4% vs "other" 98% |
| `(MR)` | 44,687 (13.6%) | rising 10.9% → 16.7% over 2009→2020 |
| `(A)` | 3,368 | never co-occurs with `(MR)` |
| `(O/A)` | 19,294 | |
| `(RES)` | 3,255 | |
| `(Net)` | 16,952 | mostly "other" scope (14,090) |
| `(NOTE PRICE)` | 653 | |
| `(OF n)` | 24,048 (7.3%) | 6 with stray space `( OF 3)`, 2009–Nov 2010 |
| previous sol `(MMMYYnnnn)` | 49,900 (15.2%) | 29% in 2009, ~11% 2010–13, 17% by 2019 |
| `(STARnnnnn)` | 2,021 | always 5 digits; 4.7% in 2009 → ~0 by 2020 |
| printing `(NEW PTG)` / `(CURR PTG)` / `(nND PTG)` | ~1,800 | `CURR PTG` first seen SEP10 |
| `(ONGOING)` | 499 | 454 directly before `#`; last seen JUL19 |
| `(ONE SHOT)` / `(ONE-SHOT)` | 227 / 56 | |
| `(OSW)` | 10 | SEP09–JAN10 only; 9 on one-shots; **[U]** |
| `(PD)` | 4 | MAR13–APR13 only, all X-O MANOWAR (VU) #13/#14; **[U]** |
| four-digit year `(2016)` | 479 | series volume year, systematic from 2016 (e.g. `GI JOE (2016) #5`) — **absent from the 2016 grammar** |

**Bare tokens:**

| Token | Items | Notes |
|---|---|---|
| `#n` | 102,566 (31%) | 19.7% (2009) → 37% (2020) |
| `VOL nn` | 66,850 | `VOL` precedes `#` in 96% (`VOL 2 #1`) |
| `TP` / `HC` / `GN` / `SC` | 49,257 / 28,145 / 21,095 / 5,871 | `TPB` only 8; `OMNIBUS` 3,082; `GN/TP/HC` precede `VOL` 99.8% |
| `CVR` | 30,400 | 2.2% (2009) → 14.9% (2020) |
| `VAR` | 12,290 | 0.9% → 10.6% |
| `CVR/COVER <letter>` | 20,839 | 0.6% → 13.3%; letters beyond C common after 2016 |
| `SGN` / `LTD ED` / `PX ED` / `SP ED` / `US ED` | 1,959 / 854 / 304 / 153 / 88 | |
| `T/S` / `FIG` / `AF` / `STATUE` / `PX` | 25,937 / 15,018 / 8,400 / 3,810 / 5,290 | merchandise markers |
| `SET` / `PACK` / `BUNDLE` / `BOX SET` | 5,150 / 2,330 / 373 / 998 | packaged items |
| printing words | `NEW PTG` 3,322 bare, `CURR PTG` 616, `2ND PTG` 188, 3rd+ 263, `2ND PRINTING` 2 | |
| specials | `ANNUAL` 921, `NUDE` 1,205, `DOUBLE DIGEST` 367, `DIRECTORS CUT` 98, `POSTER` 1,581, `DVD` 4,170 | |

**`#` forms:** plain integers 102,401 (804 `#0`, 999 ≥ 1000); decimals 187 (`#654.1`, `#0.2014`, `#1.MU`, `#20.NOW`); ranges `#a-b` 96; `#a & #b` 15; digits+letters 10 (`#8AU`); letters only 27 (hashtags such as `#TEAMVERONICA`, not issue numbers); **201 items contain more than one `#`** (`ANGELIC #2 CVR B WALKING DEAD #50 TRIBUTE VAR`). `ONE SHOT`: 1,154 bare, 162 `ONE-SHOT`, 227 `(ONE SHOT)`; `ONE SHOT #n` 49; `#n ONE SHOT` 6.

### 6.2 Ordering (measured, near-deterministic for the *meta* groups)

Canonical sequence of trailing parenthetical metadata:

```
[free text / (OF n) / PTG]  (Net)  (O/A | RES)  (prev-sol)  (MR | A)  (NOTE PRICE)  (C: d-d-d)
```

- Caution code is last parenthesis in 99.96% (exceptions are duplicated/truncated artefacts, 31 of 59 from APR13).
- Pairwise: `(Net)` before sol-info 1,192:0; sol-info/Net before prev-sol 369:0 and 335:0; `(MR)/(A)` after prev-sol 12,260:73; before caution 11,413:1.
- `#n` precedes `(OF n)` in 100% of 22,324 pairs, precedes `CVR/VAR/COVER` in 100% (38,416); `(OF n)` precedes `CVR` in 100% (9,634).
- Free text — title tail, subtitle, artist, variant label — has **no** fixed order; 8,092 of 254k parenthesised items carry free text *after* the last parenthesis (`(OF 6) YARDIN INTERNATIONAL VAR`).
- **The 2016 tokenizer's assumption that `(OF n)` is recognized only when it is the first token does not match the data:** after `#n`, `(OF n)` is typically followed by cover/artist text (~9.6k items).

### 6.3 Tokens the 2016 grammar lacks (first seen)

`SUBSCRIPTION VAR` SEP12 · `MAIN CVR` and `(N52)` NOV12 (362 items to FEB20) · `PREORDER CVR` FEB13 · `CONNECTING VAR` NOV14 · `(NEW ARC)` and `(NEXT)` DEC14 · `(DARK CIRCLE)` JAN15 · `DECO CVR` FEB15 · `ADULT CVR`/`COSPLAY CVR` SEP15 · `POLYBAG` JAN16 · `SUB CVR` MAY16 · `(WALKING DEAD HERES NEGAN PT n)` JUN16 · `(REBIRTH)` OCT16 · `(Pn)` MAY19 · year-in-parentheses (systematic from 2016). Event/crossover tags (`(BLACKEST NIGHT)`, `(ZERO YEAR)`, `(BRIGHTEST DAY)`) and publisher-edition tags (`(DH ED)`, `(TITAN ED)`, `(IMAGE ED)`) are the largest *unclassified* parenthetical families (373 distinct groups, 5,972 occurrences) **[I]**. Other recurring unclassified markers: `DLX`, `PREM HC` (1,209), `DF` (2,541), `EXC`, `COPY INCV` / `1:nn` ratio variants, `NEWSSTAND`, `CGC`, `PREORDER`.

### 6.4 Where it is hard (needs NLP/dictionary)

The title/subtitle boundary, cover artist vs title words, and creator-in-title are unmarked and grow harder over time (variant covers 2.2% → 14.9%). Sample of raw hard cases (labels deliberately not guessed):

```
CALIBAN #6 DESIGN SKETCH VAR (MR)
ENCHANTED TIKI ROOM #2 (OF 5) CHRISTOPHER ACTION FIGURE VAR
BATMAN AND ROBIN #34 DCU SELFIE VAR ED (ROBIN RISES)
REX MUNDI TP VOL 02 THE RIVER UNDERGROUND DH ED (SEP060028)
GFT GRIMM FAIRY TALES #100 D CVR CHEN (AOFD) (MR)
WAR OF REALMS #3 (OF 6) HEEJIN JEON MARVEL BATTLE LINES VAR
RED SONJA CONAN #2 (OF 4) CVR B EXC SUBSCRIPTION CVR
GFT PRESENTS NEVERLAND #2 (OF 6) 10 COPY INCV CVR BASULDUA
DF DAREDEVIL #600 CSA EXC SGN MILLER & GRANOV
STREET FIGHTER II TURBO #10 B CVR Q TRENCHCOAT
UNCLE SCROOGE MYSTERIOUS STONE RAY & CASH FLOW (C: 1-0-0)
PIERCE BROWN RED RISING #1 ATLAS COMICS BROWN SGN (C: 0-1-2)
```

(25 samples are in the measurement output; 12 shown.)

### 6.5 Scope

Description parsing should be scoped explicitly. The 2016 tokenizer only handled comics with `#` or `ONE SHOT`; about 30% of items carry `#n`, and merchandise (`T/S`, `FIG`, `AF`, `STATUE`, `POSTER`, `DVD`) and books (`GN/TP/HC/SC VOL`) follow different grammars. Section membership is not a reliable scope filter (see 5.4).

## 7. Anomaly register (all verified)

| ID | Where | Anomaly | Handling |
|---|---|---|---|
| A1 | FEB09 | All 5,123 items have an extra empty field at index 2 (layout C) | drop index 2 |
| A2 | SEP15 | 8 lines with the same extra field | drop index 2 |
| A3 | MAR09 (1,390), APR09 (34) | date missing (layout D) | insert empty date |
| A4 | JAN13, JUL13 | tab-padded headings/PAGE lines; items without trailing tab; `m/d/yyyy` dates; no trailing blanks | strip trailing tabs; layout B |
| A5 | JUL11 (2), JAN19 (2) | items missing the trailing tab | layout B |
| A6 | JUN13:2000 | hand-added line `DO NOT ORDER FROM THIS LINE` | flag/exclude |
| A7 | AUG13:2635; MAY15:2916; JUL15:2899; SEP15:2700 | sol code without space; foreign month prefix | tolerant regex + flag |
| A8 | JUN17:3473 | sol code `FEB17 8885` (month ≠ file) | flag |
| A9 | DEC18, NOV16, SEP16 | duplicate sol number within file | key on line number too |
| A10 | MAR18:864 | tail `\t = $\t ` | tolerant tail |
| A11 | AUG13:2766 | price `SRP:PI` | tolerant price regex |
| A12 | FEB12:387; SEP17:14 | `SRP: FREE`; `MSRP: PI` | include in price grammar |
| A13 | JUN12:2430; SEP19:2850 | flags `SS FI`, `FO` | keep raw; flag |
| A14 | 12 files (see 2.1) | ident month stale | filename authoritative |
| A15 | JUL14 | ident `#6` vs expected `#7` | filename authoritative |
| A16 | 8 files | no ident line | filename only |
| A17 | NOV14:4 | `GE 24` (truncated PAGE) | repair or flag |
| A18 | DEC12 | first PAGE at line 28 | do not assume position |
| A19 | FEB20 | `PAGE 2999`, `PAGE 3000` | page numbers are not trusted |
| A20 | JAN14:7 | bracketed editor annotation | non-data line |
| A21 | 8 lines / 7 files | `(NOTE: …)` | NOTE type |
| A22 | JAN09:5489, 5613; JUN17:3977 | damaged POKÉMON bytes | repair from `*_original_txt` |
| A23 | whole corpus | 5 files contain a bare heading `300`; last line of every file is a bare number | footer rule (2.3) |

## 8. Recommended data-quality approach

1. **Keep a pristine raw corpus** (decoded UTF-8, CRLF preserved) and a separate **patch list** (file, line, rule, reason) instead of editing files. This is what the 2023 todo asked for ("track edited vs original COFs") and makes every anomaly in §7 auditable.
2. Treat the filename as the source of period; store ident text as an observed attribute.
3. Parse with the layout normalization in 4.2, and make every deviation a logged anomaly with line number, never a silent drop (the 2020 code dropped lines with < 4 fields).
4. Decide the `M-` page semantics, flag semantics, and `(Net)` meaning from an authoritative Diamond source before encoding them.

## 9. Open questions

- Meaning of flags `SS`, `SPOT`, `OA`, `FI`, `KIDS`, `GEM` **[U]** (only correlations known).
- Meaning of `PAGE M-n` pages (merchandise vs Marvel-specific) **[U]**.
- Meaning of `(Net)`, `(OSW)`, `(PD)`, `(N52)`, `(AOFD)`, `(AH)`, `(DOTF)`, `(VF)`, `(P2)`, `C/O`, `BMB`, `DF`, `EXC`, `INCV` **[U]**.
- Whether the April 2018 restructure corresponds to a Diamond catalog change (cause inferred only).
- Which hand edits listed in the 2023 notes are present in `previews_parsing/cof_files` (compare against freshly downloaded copies — the author already planned this).
- Heading levels for everything after JAN09 (no gold data); alias list for renames/typos.
- Whether the download URL pattern still works and whether APR20 → AUG23 files differ in layout from the 135 analyzed (not analyzed here).
- Repeated-heading rule validated on only 3 of ≥ 6 cases.
- Whether the "premier vs comics" split correlates with where the old `tt.php` found its 24–26k comic items.

## 10. Suggested fixtures for a new parser

One small test file per anomaly in §7 (A1–A23), plus: one file per ident variant (A–D, none), one per layout (A–D), JAN13 (padded headings), MAY18+ (`M-` pages), APR18 (restructure), a file with each flag value, and the 25 hard sol_text samples with hand labels.

## 11. Corrections to earlier documents

| Earlier statement | Where | Correction |
|---|---|---|
| ~100k items / 105,450 item lines | `analysis_previews.md` | that count covered only JAN09–AUG14 (and a different line count); the 135-file corpus has ≈328.8k |
| 2013 files "missing a field"/6 columns means missing date | `analysis_previews.md` | only the trailing empty field is missing (layout B); dates present in `m/d/yyyy` |
| FEB09 only quirk; SEP15 not mentioned | various | SEP15 has 8 lines with the same extra field |
| FCBD "may be the first heading" | 2023 README | FCBD is a sub-heading; first heading is always PREVIEWS PUBLICATIONS |
| "some headings start with the word page" | 2023 `cof_notes.md` | no heading begins with PAGE (only item titles and `BETTIE PAGE`) |
| `(MMMYYcccc)` = previous resolicitation *date* | 2016 notes | it is a code (month+year+4 digits), not a date |
| `(OF n)` recognized only as first token | `tt.php` | measured: nearly always follows `#n` and precedes artist text |
| Encodings ISO-8859-1 / cp1250 | 2020/2023 listings | all 135 files are strict UTF-8 |
| Page sentinel mismatch (0 vs −1) | 2023 code vs notes | irrelevant for this corpus; prefer NULL |
| `TPB` as a standard book type | 2016 notes | only 8 occurrences; `TP` dominates |

## 12. Provenance

Measurement scripts and intermediate outputs live in the session scratchpad (`.../scratchpad/{lines,items,headings,tokens}/`). That directory may be cleared; **if these numbers are to be relied on, the scripts should be moved into this repo** (e.g. `tools/analysis/`) and re-run as tests. Not done yet.

Limits: the measurement passes read the corpus once each; counts differ by ±6 between passes in a few places (e.g. 328,795 / 328,796 / 328,797 / 328,801 items) because they used slightly different predicates — the spec quotes the predicate-specific figure where it matters. The heading-level analysis rests on one hand-levelled file (JAN09) and a 2013–14 table. No part of this spec has been validated against a parser implementation.
