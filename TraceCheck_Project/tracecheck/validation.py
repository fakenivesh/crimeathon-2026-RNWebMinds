from __future__ import annotations

from typing import Any

from .rules import run_rules


def _record(record_id: str, event_type: str, source_id: str = "SYNTH-TEST", **fields) -> dict[str, Any]:
    return {"id": record_id, "source_id": source_id, "event_type": event_type,
            "record_origin": "synthetic-validation", "payload": fields, **fields}


def run_validation() -> dict[str, Any]:
    scenarios = [
        {
            "id": "normal-weekly-export", "name": "Normal weekly support export", "expected": "No alert",
            "records": [_record("test-weekly-01", "export", source_system="HelpDeskr support integration", description="Weekly support export", schedule="weekly", record_count=350)],
            "expected_rule": None,
        },
        {
            "id": "normal-nightly-sync", "name": "Scheduled nightly sync", "expected": "No alert",
            "records": [_record("test-sync-01", "sync", schedule="nightly", action="scheduled_sync")],
            "expected_rule": None,
        },
        {
            "id": "large-export", "name": "Large unusual export", "expected": "Review finding",
            "records": [_record("test-export-01", "export", record_count=15000, schedule="ad_hoc", description="Large vendor export")],
            "expected_rule": "LARGE_VENDOR_EXPORT",
        },
        {
            "id": "bank-change-no-approval", "name": "Bank edit with blank approval reference", "expected": "Review finding",
            "records": [
                _record("test-api-01", "api_request", request_id="req-test-bank", vendor_id="V-TEST", action="update_bank_account"),
                _record("test-change-01", "vendor_change", request_id="req-test-bank", vendor_id="V-TEST", vendor_field="bank_account", approval_ref=""),
            ],
            "expected_rule": "FINANCIAL_CHANGE_NO_APPROVAL",
        },
        {
            "id": "finance-path-access", "name": "Integration access to finance path", "expected": "Review finding",
            "records": [_record("test-storage-01", "storage_access", credential_id="service-key-test", actor="integration-service", resource_path="/finance/vendor-master/")],
            "expected_rule": "FINANCE_PATH_INTEGRATION_ACCESS",
        },
        {
            "id": "overprivileged-key", "name": "Broad integration key without recorded restrictions", "expected": "Review finding",
            "records": [_record("test-credential-01", "credential_inventory", credential_id="key-test-01", permissions="read:write all-modules", ip_restricted=False, token_expiry=None)],
            "expected_rule": "OVERPRIVILEGED_INTEGRATION_KEY",
        },
        {
            "id": "approved-bank-change", "name": "Bank edit with approval reference", "expected": "No alert",
            "records": [
                _record("test-api-approved-01", "api_request", request_id="req-test-approved", vendor_id="V-APPROVED", action="update_bank_account"),
                _record("test-change-approved-01", "vendor_change", request_id="req-test-approved", vendor_id="V-APPROVED", vendor_field="bank_account", approval_ref="APR-TEST-APPROVED"),
            ],
            "expected_rule": None,
        },
    ]
    results = []
    for scenario in scenarios:
        findings = run_rules(scenario["records"])
        rule_ids = sorted({finding["rule_id"] for finding in findings})
        if scenario["expected_rule"] is None:
            passed = len(findings) == 0
        else:
            passed = scenario["expected_rule"] in rule_ids
        results.append({
            "id": scenario["id"], "name": scenario["name"], "expected": scenario["expected"],
            "observed": "Review finding" if findings else "No alert", "passed": passed,
            "matched_rules": rule_ids, "finding_count": len(findings),
        })
    passed_count = sum(1 for result in results if result["passed"])
    return {
        "results": results, "passed": passed_count, "total": len(results),
        "status": "PASS" if passed_count == len(results) else "NEEDS ATTENTION",
        "notice": "These are deterministic regression checks on bundled synthetic scenarios. They are not measured precision/recall, and do not establish accuracy on the original case archive.",
    }
