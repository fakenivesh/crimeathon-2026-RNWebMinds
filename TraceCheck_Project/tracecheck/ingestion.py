from __future__ import annotations

import csv
import io
import json
import uuid
from typing import Any

from .config import MAX_IMPORT_BYTES, MAX_IMPORT_RECORDS
from .normalize import fingerprint, normalize_record


def parse_upload(filename: str, content: str) -> list[dict[str, Any]]:
    encoded = content.encode("utf-8")
    if len(encoded) > MAX_IMPORT_BYTES:
        raise ValueError(f"File exceeds the {MAX_IMPORT_BYTES // (1024 * 1024)} MB import limit.")
    suffix = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if suffix == "csv":
        reader = csv.DictReader(io.StringIO(content))
        if not reader.fieldnames:
            raise ValueError("CSV needs a header row.")
        rows = list(reader)
    elif suffix in {"json", "jsonl", "ndjson"}:
        if suffix in {"jsonl", "ndjson"}:
            rows = [json.loads(line) for line in content.splitlines() if line.strip()]
        else:
            parsed = json.loads(content)
            if isinstance(parsed, list):
                rows = parsed
            elif isinstance(parsed, dict) and isinstance(parsed.get("records"), list):
                rows = parsed["records"]
            elif isinstance(parsed, dict):
                rows = [parsed]
            else:
                raise ValueError("JSON must be an object, an array, or an object containing a records array.")
    else:
        raise ValueError("Only CSV, JSON and JSONL files are supported.")
    if not rows:
        raise ValueError("No records were found in the file.")
    if len(rows) > MAX_IMPORT_RECORDS:
        raise ValueError(f"Import contains more than {MAX_IMPORT_RECORDS:,} records.")
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError("Every imported record must be a JSON object or CSV row.")
    return rows


def store_records(conn, filename: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    batch_id = "batch-" + uuid.uuid4().hex[:10]
    imported = skipped = 0
    errors: list[dict[str, Any]] = []
    conn.execute(
        "INSERT INTO import_batches(id, filename) VALUES(?, ?)",
        (batch_id, filename[:255]),
    )
    for index, raw in enumerate(rows, start=1):
        try:
            normalized = normalize_record(raw)
            if normalized["event_type"] == "unknown":
                raise ValueError("event_type/type column is required")
            digest = fingerprint(raw)
            record_id = normalized["record_id"] or "ev-" + digest[:14]
            values = (
                record_id, normalized["source_id"], normalized["source_system"], normalized["event_type"],
                normalized["timestamp_original"], normalized["timestamp_utc"], normalized["timezone_status"],
                normalized["request_id"], normalized["vendor_id"], normalized["credential_id"],
                normalized["actor"], normalized["action"], normalized["ip_address"], normalized["approval_ref"],
                normalized["vendor_field"], normalized["resource_path"], normalized["record_count"],
                normalized["size_bytes"], normalized["schedule"], normalized["record_origin"],
                normalized["expected_outcome"], normalized["description"],
                json.dumps(raw, ensure_ascii=False, default=str), digest, batch_id,
            )
            cursor = conn.execute(
                """INSERT OR IGNORE INTO evidence_records(
                id,source_id,source_system,event_type,timestamp_original,timestamp_utc,timezone_status,
                request_id,vendor_id,credential_id,actor,action,ip_address,approval_ref,vendor_field,
                resource_path,record_count,size_bytes,schedule,record_origin,expected_outcome,description,
                payload_json,fingerprint,batch_id
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                values,
            )
            if cursor.rowcount:
                imported += 1
            else:
                skipped += 1
        except Exception as exc:
            errors.append({"row": index, "error": str(exc)})
    conn.execute(
        "UPDATE import_batches SET imported_count=?, skipped_count=?, error_count=? WHERE id=?",
        (imported, skipped, len(errors), batch_id),
    )
    return {"batch_id": batch_id, "imported": imported, "skipped_duplicates": skipped, "errors": errors}
