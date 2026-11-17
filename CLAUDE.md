# vibe_preview_parsing

Latest attempt at parsing the Previews World customer order form (COF). See `documentation/previous_repositories.md` for the history of earlier attempts.

## Reference repositories (read-only)

Earlier iterations are cloned as siblings of this repo and are available as additional working directories (see `.claude/settings.json`):

- `../previews_parsing` — original Python parser (2020)
- `../previews_parsing_pandas` — pandas refactor, possible NLP (2023)
- `../previews` — original PHP, COF files, notes & analysis docs, early Python (2016)

Rules:
- Treat these as **read-only reference material**. Never edit, commit to, or run git write operations in them.
- Write all analysis and findings into `documentation/` in this repo (e.g. `documentation/analysis_<repo>.md`).
- Analyze one repo at a time; use subagents for broad reads to keep the main context small.

## Code layout and standards

```
src/cof/common/      shared library (settings, month helpers, CSV helpers)            README.md in each package
src/cof/acquire/     PIPELINE stage 1: find, download and verify COF files from the Internet Archive
src/cof/normalize/   PIPELINE stage 2: decode, detect issues, fix, write clean tables (`cof-normalize run`)
adhoc/               ad-hoc programs (version comparison, analysis, selection); not part of the pipeline
tests/               pytest tests mirroring the above
config/              YAML configuration; scalars come from `.env` (see `.env.example`)
tools/analysis/      LEGACY measurement scripts behind the format spec; leave as they are
data/                acquire/ (index, manifest), originals/ (as downloaded), normalized/ (clean files)
```

Dependencies point one way: `adhoc` -> pipeline stages -> `common`. Nothing imports from `adhoc`.

Standards for all new code (the user's requirements):
- Type hints on every parameter and return value (`mypy --strict`); Google-style docstrings on every module, class, function and method; inline comments where they help.
- Configuration: `.env` for scalars, `config/*.yaml` for structured settings; `config.py` only if neither fits.
- Prefer maintained libraries (httpx, tenacity, pydantic-settings, typer) over hand-written stdlib code.
- Add pytest tests with the code; no real network access in tests.
- Standard transforms (UTF-8, LF, `YYYY_MM` file names) are not recorded as edits. Only real defects are issues.

Commands (the environment is managed with `uv`):

```bash
uv sync                        # install
uv run pytest                  # tests
uv run ruff check . && uv run ruff format --check .
uv run mypy
uv run cof-acquire --help      # index | listing | manifest | report | all | fetch
uv run cof-normalize --help    # run [--full-checks] | rules | detect
uv run python adhoc/<name>.py  # compare_versions, analyze_originals, compare_with_corpus, select_versions, link_pdfs, flag_inventory
```
