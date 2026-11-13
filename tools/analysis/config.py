"""Paths for the corpus measurement scripts.

Every location can be overridden with an environment variable; the defaults
assume the three reference repos are cloned next to this repo (see CLAUDE.md).

COF_DIR          directory with the MMMYY.txt files (2020 repo, 135 files)
OLD_COF_DIR      directory with the 2016 repo's *_COF.txt files (+ originals/)
DUMP_SQL         the 2016 MySQL dump (only heading INSERT rows are read)
HEADING_EXTRACT  hand-levelled heading extract (2020 repo, JAN09 only)
OUT_DIR          where pickles and captured outputs are written (gitignored)

COF_DIR and OLD_COF_DIR keep a trailing slash because scripts concatenate
file names onto them.
"""
import os

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
_SIB = os.path.dirname(REPO_ROOT)


def _dir(value):
    return value if value.endswith('/') else value + '/'


COF_DIR = _dir(os.environ.get('COF_DIR') or os.path.join(_SIB, 'previews_parsing', 'cof_files'))
OLD_COF_DIR = _dir(os.environ.get('OLD_COF_DIR') or os.path.join(
    _SIB, 'previews', 'old_code', 'Preview Parsing', 'previews parsing'))
DUMP_SQL = os.environ.get('DUMP_SQL') or os.path.join(OLD_COF_DIR, 'bipolar_2014_08_16.sql')
HEADING_EXTRACT = os.environ.get('HEADING_EXTRACT') or os.path.join(
    _SIB, 'previews_parsing', 'headings_hrch_extract_2.txt')
OUT_DIR = os.environ.get('OUT_DIR') or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')


def check(need=('COF_DIR',)):
    """Return a list of problems for the inputs named in `need`."""
    paths = {'COF_DIR': COF_DIR, 'OLD_COF_DIR': OLD_COF_DIR, 'DUMP_SQL': DUMP_SQL,
             'HEADING_EXTRACT': HEADING_EXTRACT}
    return [f'{k} not found: {paths[k]}' for k in need if not os.path.exists(paths[k])]
