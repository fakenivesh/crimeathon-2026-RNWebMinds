from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

ALIASES = {
    "source_id": ("source_id", "evidence_id", "evidence", "source", "log_id"),
    "source_system": ("source_system", "system", "platform", "application"),
    "event_type": ("event_type", "event", "type", "activity_type"),
    "timestamp": ("timestamp", "event_time", "time", "datetime", "created_at", "occurred_at"),
    "request_id": ("request_id", "requestid", "correlation_id", "api_request_id"),
    "vendor_id": ("vendor_id", "vendor", "supplier_id"),
    "credential_id": ("credential_id", "key_id", "integration_key", "token_id", "service_account"),
    "actor": ("actor", "user", "username", "principal", "initiator"),
    "action": ("action", "operation", "method", "activity"),
    "ip_address": ("ip_address", "ip", "source_ip", "client_ip"),
    "approval_ref": ("approval_ref", "approval_reference", "approval_id", "ticket_approval"),
    "vendor_field": ("vendor_field", "field", "changed_field", "attribute"),
    "resource_path": ("resource_path", "destination_path", "path", "object_path", "resource"),
    "record_count": ("record_count", "rows", "records", "item_count", "exported_records"),
    "size_bytes": ("size_bytes", "bytes", "file_size_bytes"),
    "schedule": ("schedule", "schedule_type", "frequency", "run_type"),
    "record_origin": ("record_origin", "provenance", "origin"),
    "expected_outcome": ("expected_outcome", "expected", "ground_truth"),
    "description": ("description", "message", "details", "summary"),
}


def _key(value: Any) -> str:
    return str(value).strip().lower().replace(" ", "_").replace("-", "_")


def _num(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None


def _boolish(value: Any) -> bool | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    value = str(value).strip().lower()
    if value in {"true", "yes", "1", "enabled", "restricted"}:
        return True
    if value in {"false", "no", "0", "disabled", "unrestricted"}:
        return False
    return None


def parse_timestamp(value: Any) -> tuple[str | None, str]:
    """Return ISO UTC timestamp and timezone confidence; never assume a missing zone."""
    if value is None or str(value).strip() == "":
        return None, "missing"
    raw = str(value).strip()
    try:
        normalized = raw.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            return None, "unknown"
        return dt.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"), "known"
    except ValueError:
        return None, "unparseable"


def normalize_record(raw: dict[str, Any]) -> dict[str, Any]:
    lowered = {_key(k): v for k, v in raw.items()}
    canonical: dict[str, Any] = {}
    for field, keys in ALIASES.items():
        for alias in keys:
            if _key(alias) in lowered:
                canonical[field] = lowered[_key(alias)]
                break

    timestamp_original = canonical.get("timestamp")
    timestamp_utc, timezone_status = parse_timestamp(timestamp_original)
    event_type = str(canonical.get("event_type") or "unknown").strip().lower().replace("-", "_").replace(" ", "_")
    source_id = str(canonical.get("source_id") or "UNSPECIFIED").strip()
    record_id = str(lowered.get("record_id") or lowered.get("id") or "").strip()

    normalized = {
        "record_id": record_id,
        "source_id": source_id,
        "source_system": str(canonical.get("source_system") or "Unknown source").strip(),
        "event_type": event_type,
        "timestamp_original": str(timestamp_original) if timestamp_original is not None else None,
        "timestamp_utc": timestamp_utc,
        "timezone_status": timezone_status,
        "request_id": _optional_str(canonical.get("request_id")),
        "vendor_id": _optional_str(canonical.get("vendor_id")),
        "credential_id": _optional_str(canonical.get("credential_id")),
        "actor": _optional_str(canonical.get("actor")),
        "action": _optional_str(canonical.get("action")),
        "ip_address": _optional_str(canonical.get("ip_address")),
        "approval_ref": _optional_str(canonical.get("approval_ref")),
        "vendor_field": _optional_str(canonical.get("vendor_field")),
        "resource_path": _optional_str(canonical.get("resource_path")),
        "record_count": _num(canonical.get("record_count")),
        "size_bytes": _num(canonical.get("size_bytes")),
        "schedule": _optional_str(canonical.get("schedule")),
        "record_origin": str(canonical.get("record_origin") or "imported").strip(),
        "expected_outcome": _optional_str(canonical.get("expected_outcome")),
        "description": _optional_str(canonical.get("description")),
        "payload": raw,
    }
    return normalized


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def fingerprint(raw: dict[str, Any]) -> str:
    encoded = json.dumps(raw, sort_keys=True, ensure_ascii=False, default=str, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
