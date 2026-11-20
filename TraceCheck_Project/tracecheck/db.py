from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .config import DB_PATH

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS evidence_records (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    source_system TEXT,
    event_type TEXT NOT NULL,
    timestamp_original TEXT,
    timestamp_utc TEXT,
    timezone_status TEXT NOT NULL DEFAULT 'unknown',
    request_id TEXT,
    vendor_id TEXT,
    credential_id TEXT,
    actor TEXT,
    action TEXT,
    ip_address TEXT,
    approval_ref TEXT,
    vendor_field TEXT,
    resource_path TEXT,
    record_count REAL,
    size_bytes REAL,
    schedule TEXT,
    record_origin TEXT NOT NULL DEFAULT 'imported',
    expected_outcome TEXT,
    description TEXT,
    payload_json TEXT NOT NULL,
    fingerprint TEXT NOT NULL UNIQUE,
    batch_id TEXT,
    ingested_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_evidence_request ON evidence_records(request_id);
CREATE INDEX IF NOT EXISTS idx_evidence_source ON evidence_records(source_id);
CREATE INDEX IF NOT EXISTS idx_evidence_type ON evidence_records(event_type);
CREATE INDEX IF NOT EXISTS idx_evidence_timestamp ON evidence_records(timestamp_utc);
CREATE INDEX IF NOT EXISTS idx_evidence_vendor ON evidence_records(vendor_id);

CREATE TABLE IF NOT EXISTS findings (
    id TEXT PRIMARY KEY,
    rule_id TEXT NOT NULL,
    title TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Open',
    confidence TEXT NOT NULL,
    summary TEXT NOT NULL,
    explanation TEXT NOT NULL,
    recommendation TEXT NOT NULL,
    evidence_record_ids_json TEXT NOT NULL,
    source_evidence_ids_json TEXT NOT NULL,
    entity TEXT,
    request_id TEXT,
    analyst_note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_findings_status ON findings(status);
CREATE INDEX IF NOT EXISTS idx_findings_severity ON findings(severity);
CREATE INDEX IF NOT EXISTS idx_findings_rule ON findings(rule_id);

CREATE TABLE IF NOT EXISTS import_batches (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    imported_count INTEGER NOT NULL DEFAULT 0,
    skipped_count INTEGER NOT NULL DEFAULT 0,
    error_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    target_id TEXT,
    details_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def connect(db_path: Path | str | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 15000")
    return conn


def initialize(db_path: Path | str | None = None) -> None:
    with connect(db_path) as conn:
        conn.executescript(SCHEMA)
        conn.commit()


@contextmanager
def database(db_path: Path | str | None = None) -> Iterator[sqlite3.Connection]:
    conn = connect(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
