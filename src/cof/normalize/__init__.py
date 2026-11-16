"""Pipeline stage 2: turn the downloaded COF text files into clean, normalized files."""

from cof.normalize import detectors as _detectors  # noqa: F401,E402  (importing registers every detector)
