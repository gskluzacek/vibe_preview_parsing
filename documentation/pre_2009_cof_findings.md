# Customer Order Forms before 2009: what exists and in what form

Research of 2026-11-17 into the sources listed in `additional_sources_of_cof_and_catelog_pdfs.md`. Nothing here has entered the pipeline; a small sample is stored in `data/originals_pre2009/`.

## Summary

- The only substantial source found is **one Internet Archive item**, `diamond-customer-order-form-2002-07` ("Diamond Customer Order Forms 1998-2010", the community upload mentioned on Reddit). It holds **120 monthly order forms, JAN98 to MAR12**, of which **104 are before 2009** (JAN98–MAR08).
- They are **scanned print-outs, not text files**: each is a PDF of page images with an OCR layer. The item's OCR is **unusable as it stands** (it was run with a Cyrillic-heavy language setting, so Latin letters come out as look-alike Cyrillic letters). Using these forms means re-running OCR on the page images, then normalizing the result.
- The Wayback Machine has **no pre-2009 order-form files** under the paths in our configuration: `diamondcomics.com/support/previews_docs/orderforms/*` has only 9 captures, the oldest from 2012 (APR10 and DEC10 files); `previewsonline.com` has one 2001 home page and no forms. The "late 1990s text file" claim in the history notes could not be confirmed from the archive index.
- 16 months of the item (2009–2012) overlap our corpus, which gives a ground truth to measure OCR accuracy.

## The Internet Archive item

| | |
|---|---|
| Address | `https://archive.org/details/diamond-customer-order-form-2002-07` |
| Content | 120 PDFs named `Diamond Customer Order Form YYYY MM.pdf`, each also as `.cbr` (page images), `_jp2.zip` (page images, JPEG 2000), `_djvu.txt` (OCR text), `_hocr.html`, `_djvu.xml` and other OCR formats |
| Size | about 9.4 GB for the item; the 120 PDFs total 588 MB (3–6 MB each); each OCR text is 125–325 KB |
| Added | 2026-10-04 |
| Index | `data/originals_pre2009/ia_item_files.csv` (period, file name, sizes) |

Coverage by year (files per year): 1998 12 · 1999 **4** · 2000 12 · 2001 11 · 2002 12 · 2003 12 · 2004 11 · 2005 12 · 2006 12 · 2007 **3** · 2008 **3** · 2009 6 · 2010 4 · 2011 3 · 2012 3.

Missing months (51): 1999-04 to 1999-11, 2001-06, 2004-11, 2007-04 to 2007-12, 2008-04 to 2008-12, 2009-04 to 2009-09, 2010-05 to 2010-12, 2011-04 to 2011-12. Since our text corpus starts at JAN09, the useful new months are **JAN98–MAR08 minus the gaps: 104 months**, of which the long unbroken run is JAN00–MAR07 (except JUN01 and NOV04). The 2009–2012 files are duplicates of what we have in better (text) form.

The naming follows our convention: the month in the name is the order-form month (the JUL02 form has `JLO2`-style codes, order deadline July 13 2002, shipping in September 2002).

## What the files look like

- Page images were printed from the publisher's layout software (the 2002 samples carry a header such as `6/13/2002 1:09 PM Page 6`), so a page holds a block of item lines in the same shape as the text files: flag, sol code, description, price (`MSRP: $3.25 = $`). Page markers (`PAGE 21`) are printed in the page.
- The OCR layer in the PDF and in `_djvu.txt` is from `tesseract` with the languages `lat+rus+kir+kaz+kat+que+Cyrillic+Latin` and detected language `kk` (Kazakh). In the 2005 sample about 16,000 of ~137,000 letters are Cyrillic look-alikes (`PREVIEWS` → `РКЕМЕУУ5`, `SPOT` → `5РОТ`, `MAR08` → `МАВ08`-like), and digits are often wrong (`0` for `O`, `5` for `S`). Sol codes and prices are partly readable; descriptions are not reliable.
- 1998 forms are larger (about 225 KB of OCR for the first sample) and use a different layout from 2002; the 2002 and 2008 layouts already resemble the 2009 text files.

## Options

1. **Re-OCR with an English model** (recommended first experiment). Neither `tesseract` nor poppler tools are installed here. Install tesseract (`brew install tesseract`) and either run it on the PDFs (`ocrmypdf --force-ocr -l eng`) or on the item's `_jp2.zip`/`.cbr` page images, which are higher quality than the PDFs. Measure accuracy on the 16 overlapping 2009–2012 months by comparing with `data/normalized/`: item count, sol codes, prices.
2. **Constrain the OCR.** Items have a rigid shape (sol code `MMMYY nnnn`, `SRP|MSRP: $n.nn`, `= $`), so sol codes, flags and prices can be validated and corrected against the grammar, and the month supplies the code prefix. Descriptions need a spelling-aware second pass.
3. **Use the item's text as it is** only for sol codes and prices, which are partly recoverable by mapping look-alike letters, and treat descriptions as missing. Not recommended: it cannot be verified.
4. **Other sources.** Alternate Worlds and ACE Comics (see the sources document) cover late 2024 onward and the CSV format respectively; they do not help before 2009. Mile High Comics and YUMPU PDFs (2010s) overlap the existing corpus. The "Diamond Previews" catalog items on archive.org (`magazine-diamond-previews-NNN`, issues 265–423 seen, plus a few 1991–1993 issues) are full catalogs, not order forms, but carry the same item codes and descriptions.

## What is stored

- `data/originals_pre2009/sample/`: OCR texts of 1998_01, 2002_07, 2005_06 and 2008_03 as downloaded (garbled, kept to document the problem), and the PDF of 2005_06 (kept out of git).
- `data/originals_pre2009/ia_item_files.csv`: index of the 120 forms.

## Suggested `config/acquire.yaml` change

None yet. The acquire stage finds files through the Wayback index; this source is a normal archive.org item, so a small separate command (list the item's files through the metadata API, download chosen PDFs or page-image archives) would be the right addition if option 1 proves worthwhile.
