# `cof.common` – the shared library

Small helpers used by every stage. Nothing here knows about the Internet Archive or about COF line formats; it only knows the project's directories, month codes and CSV files. **Dependencies point one way: `adhoc` → pipeline stages (`acquire`, `normalize`) → `common`. This package imports from neither.**

## What is in it

| Module | What it does |
|---|---|
| `settings.py` | `Settings` (typed scalars, directories, delays) and `load_yaml()` (structured configuration), plus `PROJECT_ROOT` |
| `months.py` | Month codes (`JAN13`) and sortable periods (`2013_01`): `month_index`, `months_between`, `to_period`, `from_period`, and the `MONTHS` list |
| `csvio.py` | `read_rows()` (CSV → list of dicts) and `write_rows_atomic()` (write a temp file, then rename, so a crash cannot truncate a result file) |

## Using it

```python
from cof.common.settings import Settings, load_yaml
from cof.common.months import month_index, to_period
from cof.common.csvio import read_rows, write_rows_atomic

settings = Settings()  # reads COF_* environment variables and .env
settings.normalized_dir  # Path('.../data/normalized')
to_period("JAN13")  # '2013_01'
sorted(["JAN13", "DEC12"], key=month_index)  # chronological order across the century
rules = load_yaml("rules.yaml", settings)  # a mapping read from config/rules.yaml
```

## Configuration: where each kind of value lives

- **Scalars** (directories, delays, retry counts, user agent) are fields of `Settings`. Each can be overridden by an environment variable `COF_<FIELD>` (for example `COF_WAYBACK_DELAY=0`) or a line in `.env`. Copy `.env.example` to `.env`; every key is optional.
- **Structured settings** (URL patterns, thresholds, the rule registry) are YAML files in `config/`, read with `load_yaml(name)` and validated by pydantic models in the stage that owns them (`acquire/params.py`, `normalize/rules.py`).
- `config.py`-style Python constants are used only when neither fits.

Directory fields of `Settings`: `config_dir`, `acquire_dir` (`data/acquire`), `originals_dir` (`data/originals`), `normalized_dir` (`data/normalized`), `pdf_links_dir` (`data/pdf`), `analysis_dir` (`data/original_analysis`), `corpus_dir` (the author's earlier corpus, read-only reference).

## How the code works (for readers new to the libraries)

- **pydantic-settings.** `Settings` subclasses `BaseSettings`. Declaring `wayback_delay: float = 2.0` means "read `COF_WAYBACK_DELAY` if set, convert it to a float, else use 2.0". `model_config` sets the prefix (`env_prefix="COF_"`) and the `.env` path. Because values are validated, a typo such as `COF_WAYBACK_RETRIES=abc` fails at start-up with a clear message.
- **PyYAML.** `load_yaml` uses `yaml.safe_load` (no arbitrary object construction) and insists on a mapping at the top level.
- **Month codes.** `JAN13` is the publisher's name for the form; two-digit years are read as 20YY, which covers every COF (2009 onwards). `month_index` gives a number to sort by, so months compare correctly across 1999/2000 style boundaries. `to_period` gives the `YYYY_MM` form that file names use so directory listings sort by date.
- **Atomic writes.** `write_rows_atomic` writes `<name>.tmp` and calls `os.replace`, which is atomic on one file system.

## Tests

`tests/common/` mirrors this package. Run `uv run pytest tests/common`.
