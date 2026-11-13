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
