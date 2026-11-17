# `cof.acquire` – stage 1: find, download and verify COF files

Previews World (Diamond) is gone, so the COF files exist only as captures in the Internet Archive's Wayback Machine. This stage finds the captures, downloads every distinct version, and checks each file. Nothing here interprets the content; files are stored exactly as fetched and never edited.

## What it does

```
index ──► listing (optional) ──► manifest ──► report ──► fetch
CDX answers   COF listing page    manifest.csv  coverage    originals/ + downloads.csv
(raw JSON)    links (HTML+CSV)    one row per   per month   verified, one file per distinct version
                                  capture
```

| Step       | What happens                                                                                                                                                  | Output (under `data/`)                                                                           |
|------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| `index`    | asks the archive's CDX index for every capture matching each URL pattern in `config/acquire.yaml` (4 patterns: old and new site, both URL eras, text and PDF) | `acquire/raw/cdx/<pattern>.json`                                                                 |
| `listing`  | downloads sampled captures of the site's COF listing page (about one per 90 days) and extracts the links, a second list of what existed                       | `acquire/raw/listing/*.html`, `acquire/listing_links.csv`                                        |
| `manifest` | classifies every index row (which month, text or PDF, which URL era; plausible = status 200, expected MIME type, minimum size)                                | `acquire/manifest.csv`                                                                           |
| `report`   | summarizes which months have a plausible capture, expected JAN09–DEC25                                                                                        | `acquire/report.txt`                                                                             |
| `fetch`    | downloads one file per distinct content version (the archive's digest tells identical bytes apart), checks the digest and completeness                        | `originals/txt/<MMMYY>/<digest>_<timestamp>.txt`, `originals/pdf/...`, `originals/downloads.csv` |

URL eras (`urls.py`): era 1 `/support/previews_docs/orderforms/MMMYY_COF.txt`; era 2 `.../archive/YYYY/[MMMYY/]MMMYY_COF.txt`; era 3 `/Catalog/CustomerOrderForm/TXT/MMMYY` (and `/PDF/MMMYY`).

## Running it

```bash
uv run cof-acquire --help
uv run cof-acquire index          # CDX queries only; no files downloaded
uv run cof-acquire listing        # listing-page captures
uv run cof-acquire manifest       # build manifest.csv from the raw index files
uv run cof-acquire report         # coverage per month; also writes report.txt
uv run cof-acquire all            # index + manifest + report, in order

uv run cof-acquire fetch --pilot                      # the pilot set in config/acquire.yaml
uv run cof-acquire fetch --months JAN13,AUG10         # chosen months
uv run cof-acquire fetch --all                        # every month in the manifest
uv run cof-acquire fetch --all --kinds txt            # text files only (default: txt,pdf)
uv run cof-acquire fetch --months JAN13 --dry-run     # list what would be fetched
```

`fetch` is safe to re-run: files already on disk are skipped and failures are listed so a re-run retries only those. `index` overwrites the raw files, so commit them first if you want to compare. After fetching, run `adhoc/select_versions.py` to choose one version per month (writes `originals/selection.csv`).

Settings (all optional, via `.env` or `COF_*` variables): `COF_WAYBACK_DELAY` (seconds between requests, default 2.0), `COF_WAYBACK_RETRIES` (5), `COF_WAYBACK_TIMEOUT` (120), `COF_LISTING_EVERY_DAYS` (90), `COF_ACQUIRE_DIR`, `COF_ORIGINALS_DIR`.

## How the code works

| Module                     | Role                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
|----------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `cli.py`                   | the **entry point**: `cof-acquire` is declared in `pyproject.toml` (`[project.scripts]`) as `cof.acquire.cli:app`. `app` is a **typer** application; each `@app.command()` function becomes a sub-command and its type-annotated parameters become options (`Annotated[bool, typer.Option(...)]` → `--dry-run`). The functions only wire settings to the stage modules                                                                                                                   |
| `wayback.py`               | `WaybackClient`: a polite client for web.archive.org built on **httpx** (HTTP client with timeouts and redirects) and **tenacity** (retry with exponential backoff). It pauses `delay` seconds before every request, retries network errors, 5xx, 429 and the archive's "temporarily offline" page that arrives as HTTP 200 (`looks_offline`), and does not retry 404. Methods: `cdx()`, `fetch_capture()` (uses the `id_` timestamp suffix so the archive does not rewrite the content) |
| `index.py`                 | stage 1a: one CDX query per pattern, raw JSON saved unmodified                                                                                                                                                                                                                                                                                                                                                                                                                           |
| `listing.py`               | stage 1b: sample listing-page captures, extract links with a small `html.parser` subclass                                                                                                                                                                                                                                                                                                                                                                                                |
| `manifest.py`, `models.py` | stage 1c: `Capture` dataclass (one manifest row), `build_captures`, `write_manifest`, `read_manifest`, `coverage_report`                                                                                                                                                                                                                                                                                                                                                                 |
| `urls.py`                  | `classify()` turns a URL into month, kind (txt/pdf) and era                                                                                                                                                                                                                                                                                                                                                                                                                              |
| `params.py`                | pydantic models for `config/acquire.yaml` (`AcquireParams`, `Plausibility`) and `load_params()`; a bad YAML fails with a validation error rather than a `KeyError` later                                                                                                                                                                                                                                                                                                                 |
| `fetch.py`                 | stage 1d: `distinct_versions` (earliest plausible capture of each digest), `archive_digest` (base32 SHA-1, the archive's own fingerprint, to verify the download), `looks_right` (cheap sanity check), `run_fetch`, and the download log                                                                                                                                                                                                                                                 |

Design points a newcomer should know:

- **Testing without network.** `WaybackClient` accepts a `transport` (httpx's `MockTransport` in tests) and a `sleep` function, so the tests run instantly and never touch the Internet. Tests that need the network are marked `network` and are deselected by default.
- **Configuration vs settings.** URL patterns and thresholds are YAML (`config/acquire.yaml`); delays and directories are `Settings` scalars (see `cof.common`).
- **Never edit originals.** Corrections happen in stage 2, on copies.
- **User agent.** A generic client name is sent; no personal details.

## Tests

`tests/acquire/` mirrors the modules. `uv run pytest tests/acquire`.
