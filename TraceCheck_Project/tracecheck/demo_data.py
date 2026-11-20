from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .config import DATA_DIR
from .db import database, initialize
from .ingestion import store_records

ANCHOR_REQUEST_ID = "req-5f61b0de8"
ANCHOR_CHANGE_ID = "chg-8b9888c39b"


def build_demo_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    start = datetime(2026, 9, 3, 1, 0, 0, tzinfo=timezone.utc)
    fields = ["phone"] * 44 + ["email"] * 26 + ["bank_account"]
    for index, field in enumerate(fields, start=1):
        is_anchor = index == 71
        request_id = ANCHOR_REQUEST_ID if is_anchor else f"req-demo-{index:04d}"
        vendor_id = "V-0412" if is_anchor else f"V-{100 + ((index - 1) % 38):04d}"
        timestamp = "2026-09-03T01:44:30Z" if is_anchor else (start + timedelta(seconds=(index - 1) * 38)).isoformat().replace("+00:00", "Z")
        provenance = ("case-summary-fixture" if is_anchor else "synthetic-example")
        api_id = "api-anchor-0412" if is_anchor else f"api-demo-{index:04d}"
        change_id = ANCHOR_CHANGE_ID if is_anchor else f"chg-demo-{index:04d}"
        operation = "update_bank_account" if field == "bank_account" else f"update_{field}"
        records.append({
            "record_id": api_id, "source_id": "E18", "source_system": "TallyBridge API log",
            "event_type": "api_request", "timestamp": timestamp, "request_id": request_id,
            "vendor_id": vendor_id, "credential_id": "key-tb-07", "actor": "tallybridge-integration",
            "action": operation, "ip_address": "203.0.113.17" if not is_anchor else None,
            "vendor_field": field, "record_origin": provenance,
            "description": "Fixture API request created from the request ID stated in the case presentation; original E18 row ID was not provided" if is_anchor else "Synthetic example API request to reproduce the reported E18/E19 join counts",
        })
        records.append({
            "record_id": change_id, "source_id": "E19", "source_system": "Vendor master change log",
            "event_type": "vendor_change", "timestamp": timestamp, "request_id": request_id,
            "vendor_id": vendor_id, "credential_id": "key-tb-07", "actor": "tallybridge-integration",
            "action": operation, "vendor_field": field,
            "approval_ref": "" if is_anchor else f"APR-SYN-{index:04d}",
            "record_origin": provenance,
            "description": "Bank account change recorded at 2026-09-03 01:44:30 UTC; approval_ref is blank in the case presentation" if is_anchor else "Synthetic linked change record; values are fixtures, not original case evidence",
        })

    # Case-context fixtures based on the findings summarized in the submitted presentation.
    records.append({
        "record_id": "credential-e04-demo", "source_id": "E04", "source_system": "TallyBridge integration register",
        "event_type": "credential_inventory", "timestamp": "2026-09-01T00:00:00Z",
        "credential_id": "key-tb-07", "actor": "integration-register", "action": "credential_review",
        "permissions": "read:write all-modules", "ip_restricted": False, "token_expiry": None,
        "record_origin": "case-summary-fixture",
        "description": "Presentation summary: broad read/write all-modules permissions; no recorded IP restriction or token lifetime. Fixture representation, not the original E04 file.",
    })
    for n in range(1, 11):
        records.append({
            "record_id": f"support-export-demo-{n:02d}", "source_id": "E02", "source_system": "HelpDeskr support integration",
            "event_type": "export", "timestamp": f"2026-09-{n+1:02d}T02:15:00Z",
            "credential_id": "support-integration-02", "actor": "support-integration", "action": "export_create_download",
            "record_count": 420 + n * 7, "schedule": "ad_hoc", "description": "Support integration export cycle; synthetic representation of the ten additional cycles described in the presentation",
            "record_origin": "synthetic-example", "expected_outcome": "review",
        })
    records.append({
        "record_id": "large-export-demo-01", "source_id": "E01", "source_system": "LedgerOne vendor export",
        "event_type": "export", "timestamp": "2026-09-02T23:10:00Z", "credential_id": "ledger-export-service",
        "actor": "vendor-export-service", "action": "bulk_export", "record_count": 14500, "size_bytes": 18_400_000,
        "schedule": "ad_hoc", "description": "Synthetic large-export fixture based on the E01 large vendor export finding; volume is illustrative, not a value from the original evidence",
        "record_origin": "synthetic-example", "expected_outcome": "review",
    })
    records.append({
        "record_id": "finance-path-demo-01", "source_id": "E05", "source_system": "BlueVault object access",
        "event_type": "storage_access", "timestamp": "2026-09-03T02:02:00Z", "credential_id": "storage-key-fin-01",
        "actor": "storage-integration-service", "action": "read", "resource_path": "/finance/vendor-master/",
        "description": "Synthetic access record illustrating the finance-path concern summarized for E05; not the original access log",
        "record_origin": "synthetic-example", "expected_outcome": "review",
    })
    records.extend([
        {
            "record_id": "weekly-support-export-normal", "source_id": "SYNTH-NORMAL-01", "source_system": "HelpDeskr support integration",
            "event_type": "export", "timestamp": "2026-09-07T02:00:00Z", "credential_id": "support-integration-02",
            "actor": "support-integration", "action": "scheduled_export", "record_count": 350, "schedule": "weekly",
            "description": "Normal weekly support export used as a validation fixture", "record_origin": "synthetic-validation",
            "expected_outcome": "normal",
        },
        {
            "record_id": "nightly-sync-normal", "source_id": "SYNTH-NORMAL-02", "source_system": "TallyBridge sync",
            "event_type": "sync", "timestamp": "2026-09-04T01:00:00Z", "credential_id": "key-tb-07",
            "actor": "tallybridge-integration", "action": "scheduled_nightly_sync", "schedule": "nightly",
            "description": "Normal nightly synchronization used as a validation fixture", "record_origin": "synthetic-validation",
            "expected_outcome": "normal",
        },
        {
            "record_id": "maintenance-context-demo", "source_id": "E20", "source_system": "Vendor maintenance note",
            "event_type": "maintenance_window", "timestamp": "2026-09-03T00:30:00Z", "actor": "vendor-maintenance",
            "action": "planned_maintenance", "description": "Maintenance/build-host context mentioned in the case presentation; illustrative context record",
            "record_origin": "synthetic-example",
        },
        {
            "record_id": "sso-context-demo", "source_id": "E03", "source_system": "SSO audit", "event_type": "authentication_context",
            "timestamp": "2026-09-03T01:40:00Z", "actor": "tallybridge-integration", "action": "service_authentication",
            "description": "Synthetic SSO context row to demonstrate multi-source normalization", "record_origin": "synthetic-example",
        },
        {
            "record_id": "private-link-context-demo", "source_id": "E15", "source_system": "Private Link flow log", "event_type": "network_flow",
            "timestamp": "2026-09-03T01:41:00Z", "actor": "integration-network", "action": "private_link_flow",
            "description": "Synthetic network-flow context row; not an attribution claim", "record_origin": "synthetic-example",
        },
    ])
    return records


def evidence_catalog() -> list[dict[str, str]]:
    descriptions = {
        "E01": "Large vendor exports are noted in the case analysis; exact raw values are not reproduced in the presentation.",
        "E02": "Ten additional support integration export create/download cycles are noted in the case analysis.",
        "E03": "SSO activity is listed as a relevant identity context source.",
        "E04": "TallyBridge key key-tb-07 is summarized as read:write all-modules, with no recorded IP restriction or token lifetime.",
        "E05": "Finance-path access is listed as a relevant storage-access finding.",
        "E10": "Policy/control gap evidence is referenced in the presentation; detailed fields are not reproduced there.",
        "E11": "Audit/control gap evidence is referenced in the presentation; detailed fields are not reproduced there.",
        "E15": "Private-link flow is listed as a technical input source.",
        "E18": "September API log: 71 vendor-change API requests; counts stated as 44 phone, 26 email and 1 bank-account update.",
        "E19": "Vendor-change records: 71 edits joined to E18 by exact request IDs; V-0412 bank change has a blank approval reference.",
        "E20": "Maintenance/build-host context is noted; IP addresses may be reassigned.",
    }
    return [{"evidence_id": f"E{i:02d}", "description": descriptions.get(f"E{i:02d}", "Reviewed evidence item; detailed contents are not described in the submitted presentation."),
             "detail_available_in_presentation": f"E{i:02d}" in descriptions} for i in range(1, 21)]


def write_fixtures() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "demo_records.json").write_text(json.dumps({
        "notice": "Illustrative fixture. Contains one case-summary fixture for V-0412 and synthetic records that reproduce the reported counts and demonstrate workflow. It is not the original CRIMEATHON raw evidence archive.",
        "records": build_demo_records(),
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    (DATA_DIR / "evidence_catalog.json").write_text(json.dumps(evidence_catalog(), indent=2, ensure_ascii=False), encoding="utf-8")


def seed_demo(db_path=None, reset: bool = False) -> dict[str, Any]:
    write_fixtures()
    initialize(db_path)
    with database(db_path) as conn:
        current = conn.execute("SELECT COUNT(*) AS n FROM evidence_records").fetchone()["n"]
        if current and not reset:
            return {"seeded": False, "record_count": current, "message": "Database already contains evidence. Use reset to reload the example dataset."}
        if reset:
            conn.execute("DELETE FROM findings")
            conn.execute("DELETE FROM evidence_records")
            conn.execute("DELETE FROM import_batches")
        rows = build_demo_records()
        result = store_records(conn, "bundled-demo-fixture.json", rows)
        conn.execute("INSERT INTO audit_log(action,target_id,details_json) VALUES(?,?,?)",
                     ("demo_dataset_loaded", None, json.dumps({"records": result["imported"]})))
        return {"seeded": True, "record_count": result["imported"], "message": "Bundled example dataset loaded."}
