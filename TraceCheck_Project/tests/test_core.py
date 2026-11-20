from __future__ import annotations

import csv
import io
import json
from collections import Counter

from tracecheck.correlation import build_correlations
from tracecheck.demo_data import ANCHOR_CHANGE_ID, ANCHOR_REQUEST_ID, build_demo_records
from tracecheck.ingestion import parse_upload, store_records
from tracecheck.normalize import normalize_record, parse_timestamp
from tracecheck.rules import run_rules
from tracecheck.validation import run_validation
from tracecheck.db import initialize, database


def test_demo_dataset_reproduces_reported_counts_but_is_provenance_labelled():
    records = build_demo_records()
    api_records = [r for r in records if r["event_type"] == "api_request"]
    changes = [r for r in records if r["event_type"] == "vendor_change"]

    assert len(api_records) == 71
    assert len(changes) == 71
    assert Counter(r["vendor_field"] for r in api_records) == {
        "phone": 44, "email": 26, "bank_account": 1
    }
    assert all(r["record_origin"] == "synthetic-example" for r in api_records if r["request_id"] != ANCHOR_REQUEST_ID)
    assert all(r["record_origin"] == "synthetic-example" for r in changes if r["request_id"] != ANCHOR_REQUEST_ID)

    anchor = next(r for r in changes if r["request_id"] == ANCHOR_REQUEST_ID)
    assert anchor["record_id"] == ANCHOR_CHANGE_ID
    assert anchor["vendor_id"] == "V-0412"
    assert anchor["approval_ref"] == ""
    assert anchor["timestamp"] == "2026-09-03T01:44:30Z"


def test_exact_request_id_correlation_produces_71_unique_matches():
    result = build_correlations(build_demo_records())
    assert result["matched_request_count"] == 71
    assert len(result["pairs"]) == 71
    assert result["unmatched_count"] == 0

    anchor = next(pair for pair in result["pairs"] if pair["request_id"] == ANCHOR_REQUEST_ID)
    assert anchor["api"]["source_id"] == "E18"
    assert anchor["change"]["source_id"] == "E19"
    assert anchor["change"]["record_id"] == ANCHOR_CHANGE_ID


def test_rule_engine_flags_bank_change_without_claiming_approval_absence_elsewhere():
    findings = run_rules(build_demo_records())
    finding = next(f for f in findings if f["rule_id"] == "FINANCIAL_CHANGE_NO_APPROVAL")
    assert finding["entity"] == "V-0412"
    assert finding["request_id"] == ANCHOR_REQUEST_ID
    assert set(finding["source_evidence_ids"]) == {"E18", "E19"}
    assert "does not prove" in finding["explanation"].lower()


def test_timestamp_normalization_never_guesses_missing_timezone():
    utc, status = parse_timestamp("2026-09-03T01:44:30Z")
    assert utc == "2026-09-03T01:44:30Z"
    assert status == "known"

    utc, status = parse_timestamp("2026-09-03 01:44:30")
    assert utc is None
    assert status == "unknown"


def test_csv_boolean_string_for_ip_restriction_is_interpreted_correctly():
    raw = {
        "record_id": "csv-credential-1", "source_id": "E04", "event_type": "credential_inventory",
        "credential_id": "key-csv-1", "permissions": "read:write all-modules",
        "ip_restricted": "false", "token_expiry": "",
    }
    normalized = normalize_record(raw)
    # Rule reads the preserved original payload; CSV string false must not be treated as truthy.
    findings = run_rules([{**normalized, "id": normalized["record_id"]}])
    assert any(f["rule_id"] == "OVERPRIVILEGED_INTEGRATION_KEY" for f in findings)


def test_import_parser_accepts_csv_json_and_jsonl_and_rejects_unsupported():
    csv_text = "record_id,source_id,event_type,request_id\nr1,E18,api_request,req-1\n"
    assert parse_upload("records.csv", csv_text)[0]["record_id"] == "r1"
    assert parse_upload("records.json", json.dumps({"records": [{"event_type": "sync"}]}))[0]["event_type"] == "sync"
    assert parse_upload("records.jsonl", '{"event_type":"sync"}\n')[0]["event_type"] == "sync"

    try:
        parse_upload("records.txt", "abc")
    except ValueError as exc:
        assert "Only CSV, JSON and JSONL" in str(exc)
    else:
        raise AssertionError("Unsupported import extension should be rejected")


def test_store_records_is_idempotent_for_exact_duplicate_payload(tmp_path):
    db_path = tmp_path / "tracecheck.sqlite3"
    initialize(db_path)
    row = {"record_id": "dedupe-1", "source_id": "SYNTH", "event_type": "sync", "action": "scheduled"}
    with database(db_path) as conn:
        first = store_records(conn, "one.json", [row])
        second = store_records(conn, "two.json", [row])
        count = conn.execute("SELECT COUNT(*) AS n FROM evidence_records").fetchone()["n"]
    assert first["imported"] == 1
    assert second["imported"] == 0
    assert second["skipped_duplicates"] == 1
    assert count == 1


def test_validation_suite_is_regression_check_not_accuracy_claim():
    result = run_validation()
    assert result["status"] == "PASS"
    assert result["passed"] == result["total"] == 7
    assert "not measured precision/recall" in result["notice"].lower()


def test_full_seed_analysis_generates_five_review_findings_and_persists(tmp_path):
    from tracecheck.service import analyze_database, get_findings, get_summary

    db_path = tmp_path / "tracecheck-full.sqlite3"
    seed_result = __import__("tracecheck.demo_data", fromlist=["seed_demo"]).seed_demo(db_path)
    assert seed_result["record_count"] == 160
    with database(db_path) as conn:
        analysis = analyze_database(conn)
        summary = get_summary(conn)
        findings = get_findings(conn)
    assert analysis["records_analyzed"] == 160
    assert analysis["findings_generated"] == 5
    assert summary["matched_request_count"] == 71
    assert summary["unmatched_count"] == 0
    assert {f["rule_id"] for f in findings} == {
        "FINANCIAL_CHANGE_NO_APPROVAL",
        "OVERPRIVILEGED_INTEGRATION_KEY",
        "SUPPORT_EXPORT_BURST",
        "LARGE_VENDOR_EXPORT",
        "FINANCE_PATH_INTEGRATION_ACCESS",
    }


def test_analyst_review_note_status_and_audit_are_persisted(tmp_path):
    from tracecheck.service import analyze_database, get_audit_log, get_findings, update_finding
    from tracecheck.demo_data import seed_demo

    db_path = tmp_path / "tracecheck-review.sqlite3"
    seed_demo(db_path)
    with database(db_path) as conn:
        analyze_database(conn)
        finding = get_findings(conn)[0]
        updated = update_finding(conn, finding["id"], "In Review", "Verify approval with Finance.")
        audit = get_audit_log(conn)
    assert updated["status"] == "In Review"
    assert updated["analyst_note"] == "Verify approval with Finance."
    assert any(event["action"] == "finding_updated" for event in audit)


def test_unmatched_vendor_change_is_flagged_as_evidence_gap_not_malicious(tmp_path):
    from tracecheck.rules import run_rules

    record = {
        "id": "missing-api-change", "source_id": "E19", "event_type": "vendor_change",
        "request_id": "req-not-imported", "vendor_id": "V-9090", "payload": {},
    }
    findings = run_rules([record])
    unmatched = next(item for item in findings if item["rule_id"] == "UNMATCHED_VENDOR_ACTIVITY")
    assert "not proof of malicious activity" in unmatched["explanation"].lower()


def test_streamlit_application_has_all_ppt_workspaces_and_compiles():
    from pathlib import Path

    project_root = Path(__file__).resolve().parents[1]
    app_path = project_root / "app.py"
    source = app_path.read_text(encoding="utf-8")
    compile(source, str(app_path), "exec")
    expected = [
        "Overview", "Problem & Evidence", "Investigation Context", "Workflow & Architecture",
        "Feature Progress & Stack", "Evidence Explorer", "ProofPath Correlations", "ContextIQ",
        "ApprovalGuard", "ExplainAI", "PolicyGuard", "Review Queue", "Investigation Timeline",
        "Validation Lab", "Data Ingestion", "Reports & Exports", "Limitations & Roadmap",
        "System Settings",
    ]
    for page in expected:
        assert f'"{page}"' in source


def test_streamlit_app_page_branches_render_with_lightweight_ui_stub(tmp_path, monkeypatch):
    import runpy
    import sys
    from pathlib import Path
    import tracecheck.config as config_module
    import tracecheck.db as db_module

    project_root = Path(__file__).resolve().parents[1]
    db_path = tmp_path / "streamlit-smoke.sqlite3"
    monkeypatch.setattr(config_module, "DB_PATH", db_path)
    monkeypatch.setattr(db_module, "DB_PATH", db_path)

    class FakeContext:
        def __init__(self, owner=None):
            self.owner = owner
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def __getattr__(self, name):
            return lambda *args, **kwargs: self.owner._call(name, *args, **kwargs) if self.owner else None

    class FakeStreamlit:
        def __init__(self):
            self.selected_page = "Overview"
            self.session_state = {}
            self.sidebar = FakeContext(self)
        def __getattr__(self, name):
            return lambda *args, **kwargs: self._call(name, *args, **kwargs)
        def _call(self, name, *args, **kwargs):
            if name in {
                "set_page_config", "markdown", "caption", "title", "write", "info", "success",
                "warning", "error", "metric", "subheader", "header", "dataframe", "plotly_chart",
                "json", "code", "divider", "download_button", "rerun", "toast", "progress",
            }:
                return None
            if name == "radio":
                return self.selected_page
            if name == "columns":
                spec = args[0]
                return [FakeContext(self) for _ in range(spec if isinstance(spec, int) else len(spec))]
            if name in {"container", "expander", "form"}:
                return FakeContext(self)
            if name in {"button", "form_submit_button", "checkbox"}:
                return False
            if name == "file_uploader":
                return None
            if name == "text_input":
                return kwargs.get("value", "")
            if name == "text_area":
                return kwargs.get("value", "")
            if name == "selectbox":
                options = args[1] if len(args) > 1 else kwargs.get("options", [])
                index = kwargs.get("index", 0)
                return options[index] if options else None
            return None

    fake = FakeStreamlit()
    monkeypatch.setitem(sys.modules, "streamlit", fake)
    monkeypatch.syspath_prepend(str(project_root))
    expected_pages = [
        "Overview", "Problem & Evidence", "Investigation Context", "Workflow & Architecture",
        "Feature Progress & Stack", "Evidence Explorer", "ProofPath Correlations", "ContextIQ",
        "ApprovalGuard", "ExplainAI", "PolicyGuard", "Review Queue", "Investigation Timeline",
        "Validation Lab", "Data Ingestion", "Reports & Exports", "Limitations & Roadmap",
        "System Settings",
    ]
    for index, page in enumerate(expected_pages):
        fake.selected_page = page
        runpy.run_path(str(project_root / "app.py"), run_name=f"tracecheck_streamlit_page_{index}")
