from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
STATIC_DIR = PROJECT_ROOT / "static"
DEFAULT_DB = PROJECT_ROOT / "tracecheck.sqlite3"
DB_PATH = Path(os.environ.get("TRACECHECK_DB_PATH", str(DEFAULT_DB))).expanduser()
MAX_IMPORT_BYTES = 5 * 1024 * 1024
MAX_IMPORT_RECORDS = 10_000
MAX_ANALYSIS_RECORDS = 10_000
