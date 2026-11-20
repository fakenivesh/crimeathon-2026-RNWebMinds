from __future__ import annotations

import csv
import io
import json
import uuid
from collections import Counter
from datetime import datetime, timezone
from typing import Any

from .correlation import build_correlations
from .db import database
from .rules import RULE_CATALOG, run_rules


def _record(row) -> dict[str, Any]:
    value = dict(row)
    try:
        value["payload"] = json.loads(value.pop("payload_json"))
    except Exception:
        value["payload"] = {}
        value.pop("payload_json", None)
    return value


def get_records(conn, query: str = "", source_id: str = "", event_type: str = "", limit: int = 500) -> list[dict[str, Any]]:
    clauses, args = [], []
    if query:
        pattern = f"%{query}%"
        clauses.append("(id LIKE ? OR request_id LIKE ? OR vendor_id LIKE ? OR credential_id LIKE ? OR description LIKE ?)")
        args.extend([pattern] * 5)
    if source_id:
        clauses.append("source_id = ?")
        args.append(source_id)
    if event_type:
        clauses.append("event_type = ?")
        args.append(event_type)
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    rows = conn.execute(f"SELECT * FROM evidence_records{where} ORDER BY COALESCE(timestamp_utc,'') DESC, id LIMIT ?", (*args, max(1, min(limit, 10_000)))).fetchall()
    return [_record(row) for row in rows]


def analyze_database(conn) -> dict[str, Any]:
    records = get_records(conn, limit=10_000)
    findings = run_rules(records)
    keep_ids = []
    for finding in findings:
        keep_ids.append(finding["id"])
        conn.execute(
            """INSERT INTO findings(id,rule_id,title,severity,confidence,summary,explanation,recommendation,
            evidence_record_ids_json,source_evidence_ids_json,entity,request_id)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(id) DO UPDATE SET title=excluded.title,severity=excluded.severity,confidence=excluded.confidence,
            summary=excluded.summary,explanation=excluded.explanation,recommendation=excluded.recommendation,
            evidence_record_ids_json=excluded.evidence_record_ids_json,source_evidence_ids_json=excluded.source_evidence_ids_json,
            entity=excluded.entity,request_id=excluded.request_id,updated_at=CURRENT_TIMESTAMP""",
            (finding["id"], finding["rule_id"], finding["title"], finding["severity"], finding["confidence"],
             finding["summary"], finding["explanation"], finding["recommendation"],
             json.dumps(finding["evidence_record_ids"]), json.dumps(finding["source_evidence_ids"]),
             finding["entity"], finding["request_id"]),
        )
    if keep_ids:
        placeholders = ",".join("?" for _ in keep_ids)
        conn.execute(f"DELETE FROM findings WHERE id NOT IN ({placeholders})", keep_ids)
    else:
        conn.execute("DELETE FROM findings")
    conn.execute("INSERT INTO audit_log(action,target_id,details_json) VALUES(?,?,?)",
                 ("analysis_run", None, json.dumps({"record_count": len(records), "finding_count": len(findings)})))
    return {"records_analyzed": len(records), "findings_generated": len(findings), "findings": findings}


def get_findings(conn, status: str = "", severity: str = "") -> list[dict[str, Any]]:
    clauses, args = [], []
    if status:
        clauses.append("status = ?"); args.append(status)
    if severity:
        clauses.append("severity = ?"); args.append(severity.upper())
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    rows = conn.execute(f"SELECT * FROM findings{where} ORDER BY CASE severity WHEN 'CRITICAL' THEN 0 WHEN 'HIGH' THEN 1 WHEN 'MEDIUM' THEN 2 ELSE 3 END, created_at DESC").fetchall()
    output = []
    for row in rows:
        item = dict(row)
        item["evidence_record_ids"] = json.loads(item.pop("evidence_record_ids_json"))
        item["source_evidence_ids"] = json.loads(item.pop("source_evidence_ids_json"))
        output.append(item)
    return output


def get_summary(conn) -> dict[str, Any]:
    total = conn.execute("SELECT COUNT(*) AS n FROM evidence_records").fetchone()["n"]
    source_count = conn.execute("SELECT COUNT(DISTINCT source_id) AS n FROM evidence_records").fetchone()["n"]
    matched = build_correlations(get_records(conn, limit=10_000))
    findings = get_findings(conn)
    statuses = Counter(f["status"] for f in findings)
    severities = Counter(f["severity"] for f in findings)
    event_counts = {row["event_type"]: row["n"] for row in conn.execute("SELECT event_type,COUNT(*) AS n FROM evidence_records GROUP BY event_type")}
    provenance = {row["record_origin"]: row["n"] for row in conn.execute("SELECT record_origin,COUNT(*) AS n FROM evidence_records GROUP BY record_origin")}
    return {
        "total_records": total, "source_count": source_count,
        "matched_request_count": matched["matched_request_count"], "unmatched_count": matched["unmatched_count"],
        "finding_count": len(findings), "open_findings": statuses.get("Open", 0),
        "high_findings": severities.get("HIGH", 0), "status_counts": dict(statuses),
        "severity_counts": dict(severities), "event_counts": event_counts, "provenance_counts": provenance,
    }


def update_finding(conn, finding_id: str, status: str | None, note: str | None) -> dict[str, Any] | None:
    allowed = {"Open", "In Review", "Resolved", "False Positive"}
    row = conn.execute("SELECT * FROM findings WHERE id=?", (finding_id,)).fetchone()
    if not row:
        return None
    fields, args = [], []
    if status is not None:
        if status not in allowed:
            raise ValueError(f"Status must be one of: {', '.join(sorted(allowed))}")
        fields.append("status=?"); args.append(status)
    if note is not None:
        if len(note) > 2000:
            raise ValueError("Analyst note must be 2,000 characters or fewer.")
        fields.append("analyst_note=?"); args.append(note)
    if fields:
        fields.append("updated_at=CURRENT_TIMESTAMP")
        args.append(finding_id)
        conn.execute(f"UPDATE findings SET {', '.join(fields)} WHERE id=?", args)
        conn.execute("INSERT INTO audit_log(action,target_id,details_json) VALUES(?,?,?)",
                     ("finding_updated", finding_id, json.dumps({"status": status, "note_updated": note is not None})))
    return next((f for f in get_findings(conn) if f["id"] == finding_id), None)


def get_correlation(conn, request_id: str = "") -> dict[str, Any]:
    records = get_records(conn, limit=10_000)
    result = build_correlations(records)
    if request_id:
        result["pairs"] = [pair for pair in result["pairs"] if pair["request_id"] == request_id]
        result["unmatched_api"] = [r for r in result["unmatched_api"] if r.get("request_id") == request_id]
        result["unmatched_changes"] = [r for r in result["unmatched_changes"] if r.get("request_id") == request_id]
        result["matched_request_count"] = len({pair["request_id"] for pair in result["pairs"]})
        result["unmatched_count"] = len(result["unmatched_api"]) + len(result["unmatched_changes"])
    return result


def csv_export(conn, table: str) -> str:
    if table == "evidence":
        rows = conn.execute("SELECT id,source_id,source_system,event_type,timestamp_original,timestamp_utc,timezone_status,request_id,vendor_id,credential_id,actor,action,ip_address,approval_ref,vendor_field,resource_path,record_count,size_bytes,schedule,record_origin,expected_outcome,description FROM evidence_records ORDER BY timestamp_utc,id").fetchall()
    elif table == "findings":
        rows = conn.execute("SELECT id,rule_id,title,severity,status,confidence,summary,source_evidence_ids_json,entity,request_id,analyst_note,created_at,updated_at FROM findings ORDER BY severity,created_at").fetchall()
    else:
        raise ValueError("Unsupported export table")
    output = io.StringIO()
    if not rows:
        output.write("no_records\n")
    else:
        writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows([dict(r) for r in rows])
    return output.getvalue()


def get_audit_log(conn, limit: int = 30) -> list[dict[str, Any]]:
    return [dict(row) for row in conn.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (min(max(limit, 1), 100),))]


def get_import_batches(conn, limit: int = 50) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT id, filename, imported_count, skipped_count, error_count, created_at "
        "FROM import_batches ORDER BY created_at DESC, id DESC LIMIT ?",
        (min(max(limit, 1), 200),),
    ).fetchall()
    return [dict(row) for row in rows]
