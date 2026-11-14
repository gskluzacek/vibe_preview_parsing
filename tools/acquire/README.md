# COF archive lister

Finds which Customer Order Form files the Internet Archive (Wayback Machine) holds. It reads the capture index and a sample of the site's listing page. **It downloads no COF file.**

```bash
python3 -I tools/acquire/lister.py index      # CDX index queries, one per URL pattern in config.py
python3 -I tools/acquire/lister.py listing    # sample ~1 capture per 90 days of /Catalog/CustomerOrderForms, extract links
python3 -I tools/acquire/lister.py manifest   # raw index -> data/acquire/manifest.csv
python3 -I tools/acquire/lister.py report     # per-month coverage -> data/acquire/report.txt
python3 -I tools/acquire/lister.py all        # index, manifest, report
python3 -I tools/acquire/test_cof_urls.py     # URL classifier tests
```

Standard library only. Settings and overrides (environment variables `ACQUIRE_OUT`, `WAYBACK_DELAY`, `WAYBACK_RETRIES`, `WAYBACK_TIMEOUT`, `LISTING_EVERY_DAYS`) are in `config.py`.

## Outputs (`data/acquire/`)

| Path | What |
|---|---|
| `raw/cdx/*.json` | index responses exactly as returned, with the query and fetch time. Never edited |
| `raw/listing/*.html` | sampled captures of the listing page, as stored by the archive |
| `manifest.csv` | one row per capture of a single COF file: month, kind (txt/pdf), era (1–3), timestamp, original URL, status, MIME type, length, digest, plausible |
| `listing_links.csv` | COF links found on the sampled listing-page captures |
| `report.txt` | per-month table and a summary of missing months and months with more than one distinct file |

Only the first stage that needs the network is `index` (and `listing`); `manifest` and `report` rebuild from what is on disk. Rerunning `index` overwrites the raw responses, so rename or commit them first if you want to compare index snapshots over time.

## URL eras

1. `/support/previews_docs/orderforms/MMMYY_COF.{txt,pdf}`
2. `/support/previews_docs/orderforms/archive/YYYY/[MMMYY/]MMMYY_COF.{txt,pdf}`
3. `/Catalog/CustomerOrderForm/{TXT,PDF}/MMMYY`

"Plausible" means status 200, the expected MIME type and a minimum size (text > 5,000 bytes, PDF > 100,000 bytes). It is a filter on index metadata, not proof that a file is a real COF.

## Limits

- The index does not say what is inside a file. Each download still has to be checked against the layouts in `documentation/cof_format_spec.md`.
- Several captures of one month with different `digest` values are different files. The report flags them; deciding which to keep needs a content comparison.
- Index requests sometimes return an "Internet Archive: Temporarily Offline" page. The client retries with backoff.
