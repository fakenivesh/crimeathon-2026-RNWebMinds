from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from typing import Any

RULE_CATALOG = [
    {"id": "FINANCIAL_CHANGE_NO_APPROVAL", "name": "Sensitive bank-detail change without recorded approval", "severity": "HIGH", "module": "ApprovalGuard"},
    {"id": "OVERPRIVILEGED_INTEGRATION_KEY", "name": "Overprivileged integration credential", "severity": "MEDIUM", "module": "PolicyGuard"},
    {"id": "SUPPORT_EXPORT_BURST", "name": "Additional support export cycles", "severity": "MEDIUM", "module": "ContextIQ"},
    {"id": "LARGE_VENDOR_EXPORT", "name": "Large vendor export requires context review", "severity": "HIGH", "module": "ContextIQ"},
    {"id": "FINANCE_PATH_INTEGRATION_ACCESS", "name": "Integration credential accessed a finance path", "severity": "HIGH", "module": "PolicyGuard"},
    {"id": "UNMATCHED_VENDOR_ACTIVITY", "name": "Vendor change has no exact API request match", "severity": "MEDIUM", "module": "ProofPath"},
]


def _payload(record: dict[str, Any]) -> dict[str, Any]:
    value = record.get("payload", {})
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return {}
    return value if isinstance(value, dict) else {}


def _source_id(record: dict[str, Any]) -> str | None:
    return record.get("source_id")


def _finding(rule_id: str, title: str, severity: str, confidence: str, summary: str,
             explanation: str, recommendation: str, records: list[dict[str, Any]],
             entity: str | None = None, request_id: str | None = None) -> dict[str, Any]:
    ids = sorted({str(r.get("id") or r.get("record_id") or "") for r in records if r.get("id") or r.get("record_id")})
    sources = sorted({str(_source_id(r)) for r in records if _source_id(r)})
    seed = rule_id + "|" + "|".join(ids)
    finding_id = "F-" + hashlib.sha256(seed.encode()).hexdigest()[:12].upper()
    return {
        "id": finding_id, "rule_id": rule_id, "title": title, "severity": severity,
        "confidence": confidence, "summary": summary, "explanation": explanation,
        "recommendation": recommendation, "evidence_record_ids": ids,
        "source_evidence_ids": sources, "entity": entity, "request_id": request_id,
    }


def run_rules(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    api_request_ids = {
        r.get("request_id") for r in records
        if r.get("request_id") and r.get("event_type") in {"api_request", "api_call", "vendor_api_request"}
    }

    # 1. Sensitive financial field changes require a verifiable approval reference.
    for record in records:
        event_type = str(record.get("event_type", "")).lower()
        field_name = str(record.get("vendor_field") or _payload(record).get("field") or "").lower()
        is_bank = "bank" in field_name or "account" in field_name or field_name in {"bank_account", "bank_details"}
        if event_type in {"vendor_change", "vendor_edit", "vendor_update"} and is_bank and not record.get("approval_ref"):
            related = [record]
            rid = record.get("request_id")
            if rid:
                related.extend(r for r in records if r.get("request_id") == rid and r.get("event_type") in {"api_request", "api_call", "vendor_api_request"})
            findings.append(_finding(
                "FINANCIAL_CHANGE_NO_APPROVAL", "Bank-detail change needs approval verification", "HIGH", "High evidence confidence",
                f"{record.get('vendor_id') or 'A vendor'} has a bank-detail change with no approval reference in the supplied change record.",
                "The change record is linked to an API request by an exact request ID. A blank approval field means approval is not recorded in this event; it does not prove that approval is absent elsewhere.",
                "Ask Finance to verify the approved vendor-change request and compare it with the vendor's independently verified details. Preserve the linked API and change records.",
                related, record.get("vendor_id"), rid,
            ))

    # 2. Integration credentials with broad rights and absent restrictions/expiry.
    for record in records:
        if record.get("event_type") not in {"credential_inventory", "credential_config", "integration_credential"}:
            continue
        p = _payload(record)
        permissions = str(p.get("permissions") or p.get("scope") or "").lower()
        all_modules = "all-modules" in permissions or "all_modules" in permissions or "*" in permissions
        read_write = "read:write" in permissions or "read_write" in permissions or "read/write" in permissions
        ip_restricted_raw = p.get("ip_restricted")
        if isinstance(ip_restricted_raw, bool):
            ip_restricted = ip_restricted_raw
        elif ip_restricted_raw is None or str(ip_restricted_raw).strip() == "":
            ip_restricted = False
        else:
            ip_restricted = str(ip_restricted_raw).strip().lower() in {"true", "yes", "1", "enabled", "restricted"}
        expiry = p.get("token_expiry") or p.get("expires_at") or p.get("expiry")
        if (all_modules or read_write) and not ip_restricted and not expiry:
            findings.append(_finding(
                "OVERPRIVILEGED_INTEGRATION_KEY", "Integration key has broad permissions and no recorded expiry", "MEDIUM", "High evidence confidence",
                f"Credential {record.get('credential_id') or 'unknown'} is recorded with broad permissions, no IP restriction and no token expiry in the supplied register.",
                "This is a control weakness, not proof that the credential was misused. The register does not establish who controlled the key at each event time.",
                "Confirm the business owner, reduce the scope to required operations, apply an appropriate expiry/rotation policy and review access logs.",
                [record], record.get("credential_id"), None,
            ))

    # 3. Ten or more unscheduled support export cycles in the imported evidence set.
    support_exports = [r for r in records if r.get("event_type") in {"export", "export_create", "export_download"}
                       and ("support" in str(r.get("description") or "").lower()
                            or "support" in str(r.get("source_system") or "").lower()
                            or r.get("source_id") == "E02")]
    unscheduled = [r for r in support_exports if str(r.get("schedule") or "").lower() not in {"weekly", "scheduled", "routine"}]
    if len(unscheduled) >= 10:
        findings.append(_finding(
            "SUPPORT_EXPORT_BURST", "Additional support export cycles need context review", "MEDIUM", "Moderate evidence confidence",
            f"{len(unscheduled)} support export records are present without a weekly/routine schedule label.",
            "The case notes describe ten additional support integration export cycles. Additional cycles can have legitimate operational causes, so count alone is not proof of data misuse.",
            "Compare the cycles with support tickets, vendor schedules, export recipients and retained-copy controls. Verify whether the runs were expected.",
            unscheduled, None, None,
        ))

    # 4. Large export threshold is explicitly a configurable heuristic for the demo.
    for record in records:
        if record.get("event_type") not in {"export", "export_create", "export_download"}:
            continue
        count = record.get("record_count")
        size = record.get("size_bytes")
        if (count is not None and float(count) >= 5000) or (size is not None and float(size) >= 25 * 1024 * 1024):
            findings.append(_finding(
                "LARGE_VENDOR_EXPORT", "Large export requires business-context review", "HIGH", "Moderate evidence confidence",
                f"An export records {int(count):,} rows." if count is not None else f"An export is approximately {size / (1024*1024):.1f} MB.",
                "The rule uses a configurable volume threshold as a review trigger. It does not determine whether the export was unauthorized or whether data left an approved environment.",
                "Check the export purpose, owner, schedule, destination, recipient list and relevant approval or ticket before taking action.",
                [record], record.get("credential_id"), record.get("request_id"),
            ))

    # 5. A service/integration credential reaches a finance-related path.
    for record in records:
        if record.get("event_type") not in {"storage_access", "object_access", "file_access"}:
            continue
        path = str(record.get("resource_path") or "").lower()
        actor = str(record.get("actor") or "").lower()
        credential = str(record.get("credential_id") or "").lower()
        is_integration = any(token in actor or token in credential for token in ("integration", "service"))
        if "finance" in path and is_integration:
            findings.append(_finding(
                "FINANCE_PATH_INTEGRATION_ACCESS", "Integration identity accessed a finance path", "HIGH", "Moderate evidence confidence",
                f"An integration/service identity accessed {record.get('resource_path')}.",
                "The supplied activity indicates access to a finance-related path. The record alone does not establish whether the access was expected, whether content was downloaded, or who controlled the credential.",
                "Verify the data owner, approved integration scope, access ticket and object-level activity. Confirm whether the access was read-only and whether it matched a documented workflow.",
                [record], record.get("credential_id") or record.get("actor"), record.get("request_id"),
            ))

    # 6. A vendor change without an API request in the imported records is incomplete evidence linkage.
    for record in records:
        if record.get("event_type") in {"vendor_change", "vendor_edit", "vendor_update"}:
            request_id = record.get("request_id")
            if request_id and request_id not in api_request_ids:
                findings.append(_finding(
                    "UNMATCHED_VENDOR_ACTIVITY", "Vendor change has no matching API request in this dataset", "MEDIUM", "High linkage confidence",
                    f"Change {record.get('id')} references request {request_id}, but that request was not imported.",
                    "The absence may reflect an incomplete import, a different source system or a missing upstream record. It is not proof of malicious activity.",
                    "Import the corresponding API log and verify the request ID, source coverage and time range before drawing a conclusion.",
                    [record], record.get("vendor_id"), request_id,
                ))

    return findings
