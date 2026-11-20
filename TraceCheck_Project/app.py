from __future__ import annotations

import json
import html
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from tracecheck.config import DB_PATH, DATA_DIR, MAX_IMPORT_BYTES, MAX_IMPORT_RECORDS
from tracecheck.correlation import build_correlations
from tracecheck.db import database, initialize
from tracecheck.demo_data import (
    ANCHOR_CHANGE_ID,
    ANCHOR_REQUEST_ID,
    build_demo_records,
    evidence_catalog,
    seed_demo,
)
from tracecheck.ingestion import parse_upload, store_records
from tracecheck.rules import RULE_CATALOG
from tracecheck.service import (
    analyze_database,
    csv_export,
    get_audit_log,
    get_correlation,
    get_findings,
    get_import_batches,
    get_records,
    get_summary,
    update_finding,
)
from tracecheck.validation import run_validation


# -----------------------------------------------------------------------------
# Page setup and visual identity
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="TraceCheck | RN WebMinds",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

PALETTE = {
    "forest": "#173D36",
    "forest_2": "#24564C",
    "beige": "#F4F0E5",
    "paper": "#FBFAF6",
    "orange": "#C96F4D",
    "orange_light": "#F3DED2",
    "sage": "#DCE7DC",
    "ink": "#1E302D",
    "muted": "#6F7A73",
    "line": "#E4E0D6",
    "red": "#B94A48",
    "yellow": "#B98232",
    "green": "#3B7C60",
}

st.markdown(
    f"""
    <style>
      html, body, [class*="css"] {{ font-family: 'Aptos', 'Segoe UI', sans-serif; }}
      .stApp {{ background: {PALETTE['beige']}; color: {PALETTE['ink']}; }}
      [data-testid="stSidebar"] {{ background: {PALETTE['forest']}; border-right: 1px solid #315D53; }}
      [data-testid="stSidebar"] * {{ color: #F8F5EC !important; }}
      [data-testid="stSidebar"] [data-testid="stRadio"] label {{ padding: 0.32rem 0.5rem; border-radius: 7px; }}
      [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {{ background: rgba(255,255,255,.09); }}
      [data-testid="stSidebar"] hr {{ border-color: rgba(255,255,255,.18); }}
      h1, h2, h3 {{ font-family: 'Aptos Display', 'Segoe UI', sans-serif !important; letter-spacing: -0.025em; color: {PALETTE['forest']}; }}
      h1 {{ font-weight: 800 !important; }}
      h2, h3 {{ font-weight: 700 !important; }}
      [data-testid="stMetric"] {{ background: {PALETTE['paper']}; border: 1px solid {PALETTE['line']}; padding: 15px 17px; border-radius: 12px; }}
      [data-testid="stMetricLabel"] {{ color: {PALETTE['muted']} !important; font-weight: 600; }}
      [data-testid="stMetricValue"] {{ color: {PALETTE['forest']} !important; font-family: 'Aptos Display', 'Segoe UI', sans-serif; }}
      .tc-eyebrow {{ color: {PALETTE['orange']}; text-transform: uppercase; font-size: .72rem; font-weight: 800; letter-spacing: .12em; margin-bottom: .25rem; }}
      .tc-subtitle {{ color: {PALETTE['muted']}; font-size: .96rem; margin-top: -.4rem; }}
      .tc-panel {{ background: {PALETTE['paper']}; border: 1px solid {PALETTE['line']}; border-radius: 13px; padding: 17px 19px; height: 100%; }}
      .tc-panel h3 {{ margin: 0 0 .45rem 0; font-size: 1.02rem; }}
      .tc-panel p {{ color: {PALETTE['muted']}; margin: .15rem 0; font-size: .9rem; }}
      .tc-tag {{ display:inline-block; font-size:.7rem; font-weight:800; letter-spacing:.04em; padding:4px 8px; border-radius:100px; background:{PALETTE['sage']}; color:{PALETTE['forest']}; margin-bottom:8px; }}
      .tc-callout {{ background:{PALETTE['forest']}; color:#F8F5EC; border-radius:12px; padding:16px 18px; }}
      .tc-callout strong {{ color:#FFFFFF; }}
      .tc-callout p {{ color:#E9EEE7; margin:.25rem 0 0 0; }}
      .tc-risk {{ border-left:4px solid {PALETTE['orange']}; background:#FFF8F3; padding:12px 14px; border-radius:7px; margin:.45rem 0; }}
      .tc-ok {{ border-left:4px solid {PALETTE['green']}; background:#F2F7F1; padding:12px 14px; border-radius:7px; margin:.45rem 0; }}
      .tc-muted {{ color:{PALETTE['muted']}; font-size:.83rem; }}
      .stButton > button {{ border-radius:8px; border:1px solid {PALETTE['forest']}; background:{PALETTE['forest']}; color:#fff; font-weight:700; }}
      .stButton > button:hover {{ background:{PALETTE['forest_2']}; color:#fff; border-color:{PALETTE['forest_2']}; }}
      .stDownloadButton > button {{ border-radius:8px; border:1px solid {PALETTE['forest']}; color:{PALETTE['forest']}; background:{PALETTE['paper']}; font-weight:700; }}
      div[data-testid="stDataFrame"] {{ border:1px solid {PALETTE['line']}; border-radius:10px; overflow:hidden; }}
      div[data-testid="stExpander"] {{ background:{PALETTE['paper']}; border:1px solid {PALETTE['line']}; border-radius:10px; }}
      .block-container {{ padding-top: 1.5rem; padding-bottom: 2.5rem; max-width: 1500px; }}
      footer {{ visibility:hidden; }}
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# Initialization and shared data helpers
# -----------------------------------------------------------------------------
def ensure_database() -> None:
    initialize()
    should_analyze = False
    with database() as conn:
        count = conn.execute("SELECT COUNT(*) AS n FROM evidence_records").fetchone()["n"]
        prior_analysis = conn.execute("SELECT id FROM audit_log WHERE action='analysis_run' ORDER BY id DESC LIMIT 1").fetchone()
    if count == 0:
        seed_demo(reset=False)
        should_analyze = True
    elif prior_analysis is None:
        should_analyze = True
    # Streamlit reruns the script on every interaction. Only run a bootstrap
    # analysis when required; explicit analysis/import/reset actions handle the rest.
    if should_analyze:
        with database() as conn:
            analyze_database(conn)


ensure_database()


def read_summary() -> dict[str, Any]:
    with database() as conn:
        return get_summary(conn)


def read_records(query: str = "", source_id: str = "", event_type: str = "", limit: int = 5000) -> list[dict[str, Any]]:
    with database() as conn:
        return get_records(conn, query=query, source_id=source_id, event_type=event_type, limit=limit)


def read_findings(status: str = "", severity: str = "") -> list[dict[str, Any]]:
    with database() as conn:
        return get_findings(conn, status=status, severity=severity)


def run_analysis() -> dict[str, Any]:
    with database() as conn:
        return analyze_database(conn)


def source_record_frame(records: list[dict[str, Any]]) -> pd.DataFrame:
    columns = [
        "id", "source_id", "source_system", "event_type", "timestamp_original", "timestamp_utc",
        "timezone_status", "request_id", "vendor_id", "credential_id", "actor", "action",
        "ip_address", "approval_ref", "vendor_field", "resource_path", "record_count", "schedule",
        "record_origin", "description",
    ]
    if not records:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame([{key: rec.get(key) for key in columns} for rec in records])


def finding_frame(findings: list[dict[str, Any]]) -> pd.DataFrame:
    columns = ["id", "severity", "status", "title", "rule_id", "entity", "request_id", "source_evidence_ids"]
    if not findings:
        return pd.DataFrame(columns=columns)
    rows = []
    for item in findings:
        rows.append({
            "id": item.get("id"), "severity": item.get("severity"), "status": item.get("status"),
            "title": item.get("title"), "rule_id": item.get("rule_id"), "entity": item.get("entity"),
            "request_id": item.get("request_id"), "source_evidence_ids": ", ".join(item.get("source_evidence_ids", [])),
        })
    return pd.DataFrame(rows, columns=columns)


def page_heading(eyebrow: str, title: str, subtitle: str = "") -> None:
    st.markdown(f'<div class="tc-eyebrow">{eyebrow}</div>', unsafe_allow_html=True)
    st.title(title)
    if subtitle:
        st.markdown(f'<div class="tc-subtitle">{subtitle}</div>', unsafe_allow_html=True)
    st.write("")


def panel(tag: str, title: str, body: str) -> None:
    st.markdown(
        f'<div class="tc-panel"><span class="tc-tag">{tag}</span><h3>{title}</h3><p>{body}</p></div>',
        unsafe_allow_html=True,
    )


def dataset_notice() -> None:
    st.info(
        "Demo environment: the bundled records are labelled case-summary fixtures and synthetic examples. "
        "They are not the original CRIMEATHON raw evidence archive. Imported records retain their own provenance.",
        icon="ℹ️",
    )


def get_record_by_id(record_id: str) -> dict[str, Any] | None:
    rows = read_records(query=record_id, limit=100)
    return next((row for row in rows if row.get("id") == record_id), None)


def finding_module(rule_id: str) -> str:
    match = next((rule for rule in RULE_CATALOG if rule["id"] == rule_id), None)
    return match["module"] if match else "General Review"


def severity_color(value: str) -> str:
    return {"CRITICAL": PALETTE["red"], "HIGH": PALETTE["orange"], "MEDIUM": PALETTE["yellow"], "LOW": PALETTE["green"]}.get(value.upper(), PALETTE["muted"])


def render_finding_detail(finding: dict[str, Any]) -> None:
    sev = finding.get("severity", "MEDIUM")
    st.markdown(
        f'<div class="tc-panel"><span class="tc-tag">{html.escape(finding_module(finding.get("rule_id", "")))}</span>'
        f'<h3>{html.escape(str(finding.get("title", "Finding")))}</h3>'
        f'<p><b style="color:{severity_color(sev)}">{html.escape(str(sev))}</b> &nbsp;·&nbsp; {html.escape(str(finding.get("id", "")))}</p>'
        f'<p>{html.escape(str(finding.get("summary", "")))}</p></div>',
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Why it was flagged**")
        st.write(finding.get("explanation", ""))
    with col2:
        st.markdown("**Recommended human next step**")
        st.write(finding.get("recommendation", ""))
    st.markdown("**Supporting evidence**")
    records = [get_record_by_id(record_id) for record_id in finding.get("evidence_record_ids", [])]
    records = [record for record in records if record]
    if records:
        st.dataframe(source_record_frame(records), use_container_width=True, hide_index=True)
    else:
        st.caption("No linked evidence records are currently available in the imported dataset.")
    st.caption("Source evidence IDs: " + (", ".join(finding.get("source_evidence_ids", [])) or "Not supplied"))
    if finding.get("entity"):
        st.caption(f"Entity: {finding['entity']}")
    if finding.get("request_id"):
        st.caption(f"Request ID: {finding['request_id']}")


# -----------------------------------------------------------------------------
# Navigation
# -----------------------------------------------------------------------------
PAGES = [
    "Overview",
    "Problem & Evidence",
    "Investigation Context",
    "Workflow & Architecture",
    "Feature Progress & Stack",
    "Evidence Explorer",
    "ProofPath Correlations",
    "ContextIQ",
    "ApprovalGuard",
    "ExplainAI",
    "PolicyGuard",
    "Review Queue",
    "Investigation Timeline",
    "Validation Lab",
    "Data Ingestion",
    "Reports & Exports",
    "Limitations & Roadmap",
    "System Settings",
]

with st.sidebar:
    st.markdown(
        """
        <div style="padding:.3rem .1rem 1rem .1rem">
          <div style="font-size:.72rem;letter-spacing:.16em;font-weight:800;color:#E7A184">RN WEBMINDS · DEFENCE</div>
          <div style="font-family:'Aptos Display','Segoe UI',sans-serif;font-size:1.75rem;font-weight:800;color:#FFFFFF;margin-top:.2rem">TraceCheck</div>
          <div style="font-size:.78rem;color:#D4E1D7">Evidence-to-Action Security Intelligence</div>
          <div style="height:3px;background:#C96F4D;width:64px;margin-top:13px;border-radius:4px"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("CASE CR-26-047 · HARBOR & FINCH")
    selected_page = st.radio("Workspace", PAGES, label_visibility="collapsed")
    st.divider()
    st.markdown("**Environment**")
    st.markdown("<span style='background:#315D53;padding:5px 9px;border-radius:20px;font-size:.72rem'>LOCAL · READ-ONLY EVIDENCE</span>", unsafe_allow_html=True)
    st.caption("No live enterprise connectors. No autonomous blocking.")
    st.divider()
    st.caption("Build: local investigation MVP · SQLite")


# -----------------------------------------------------------------------------
# PAGE 1 — Overview
# -----------------------------------------------------------------------------
if selected_page == "Overview":
    page_heading("SECURITY INTELLIGENCE WORKSPACE", "Investigation overview", "A single workspace for connected evidence, explainable findings and human review.")
    summary = read_summary()
    records = read_records(limit=10000)
    findings = read_findings()
    api_count = sum(1 for r in records if r.get("source_id") == "E18" and r.get("event_type") == "api_request")
    change_count = sum(1 for r in records if r.get("source_id") == "E19" and r.get("event_type") == "vendor_change")
    high_count = sum(1 for f in findings if f.get("severity") in {"HIGH", "CRITICAL"} and f.get("status") not in {"Resolved", "False Positive"})

    dataset_notice()
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Evidence records", f"{summary['total_records']:,}")
    k2.metric("Evidence sources", summary["source_count"])
    k3.metric("Exact request joins", f"{summary['matched_request_count']:,}")
    k4.metric("Open findings", summary["open_findings"])
    k5.metric("High-priority review", high_count)

    left, right = st.columns([1.35, 1])
    with left:
        st.subheader("Activity across evidence sources")
        event_counts = summary.get("event_counts", {})
        if event_counts:
            df = pd.DataFrame([{"Event type": k.replace("_", " ").title(), "Records": v} for k, v in event_counts.items()])
            fig = px.bar(df.sort_values("Records", ascending=False), x="Event type", y="Records", color="Records", color_continuous_scale=["#DCE7DC", PALETTE["forest"]])
            fig.update_layout(height=330, margin=dict(l=10, r=10, t=20, b=10), plot_bgcolor=PALETTE["paper"], paper_bgcolor=PALETTE["paper"], coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Import evidence to populate activity charts.")
    with right:
        st.subheader("Findings by severity")
        sev_counts = summary.get("severity_counts", {})
        if sev_counts:
            df = pd.DataFrame([{"Severity": k, "Findings": v} for k, v in sev_counts.items()])
            fig = px.pie(df, names="Severity", values="Findings", hole=.62, color="Severity", color_discrete_map={"HIGH": PALETTE["orange"], "MEDIUM": "#C59A4D", "LOW": PALETTE["green"], "CRITICAL": PALETTE["red"]})
            fig.update_layout(height=330, margin=dict(l=10, r=10, t=20, b=10), paper_bgcolor=PALETTE["paper"], legend_title_text="")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.success("No findings are currently open.")

    st.subheader("Case anchor · V-0412 bank-detail change")
    anchor = get_record_by_id(ANCHOR_CHANGE_ID)
    api_anchor = next((r for r in records if r.get("request_id") == ANCHOR_REQUEST_ID and r.get("event_type") == "api_request"), None)
    a1, a2, a3 = st.columns([1, 1, 1.4])
    a1.metric("Vendor", "V-0412")
    a2.metric("API ↔ change", "Exact ID match" if api_anchor and anchor else "Not fully linked")
    a3.metric("Approval reference", "Blank in supplied change record")
    st.markdown(
        '<div class="tc-risk"><b>Review interpretation:</b> The API request and vendor-change record share an exact request ID. The approval reference is blank in E19. This is a verification requirement, not proof that separate approval was absent or that fraud occurred.</div>',
        unsafe_allow_html=True,
    )
    if anchor:
        with st.expander("Inspect the V-0412 evidence records"):
            cols = st.columns(2)
            with cols[0]:
                st.markdown("**E18 · API request**")
                st.json(api_anchor or {})
            with cols[1]:
                st.markdown("**E19 · Vendor change**")
                st.json(anchor)

    st.subheader("Latest findings")
    if findings:
        st.dataframe(finding_frame(findings[:6]), use_container_width=True, hide_index=True)
    else:
        st.success("No review findings generated from the current dataset.")
    if st.button("Re-run analysis", type="primary"):
        result = run_analysis()
        st.success(f"Analysis complete: {result['records_analyzed']} records examined, {result['findings_generated']} findings generated.")
        st.rerun()


# -----------------------------------------------------------------------------
# PAGE 2 — Problem and proof
# -----------------------------------------------------------------------------
elif selected_page == "Problem & Evidence":
    page_heading("CASE ANALYSIS · PROBLEM AND PROOF", "Harbor & Finch has a visibility gap", "The systems recorded related activities, but investigators need one place to connect and verify them.")
    dataset_notice()
    e04, e18, e19 = st.columns(3)
    with e04:
        panel("E04 · CREDENTIAL", "Powerful integration access", "TallyBridge key key-tb-07 is summarized as read:write all-modules. No IP restriction or token lifetime is recorded in the case summary.")
    with e18:
        panel("E18 · API LOG", "71 vendor-change requests", "The September API log records 44 phone updates, 26 email updates and one bank-account update.")
    with e19:
        panel("E19 · CHANGE LOG", "71 linked vendor edits", "The case analysis connects 71 API requests to 71 vendor-change records through exact request IDs.")

    summary = read_summary()
    records = read_records(limit=10000)
    api_rows = [r for r in records if r.get("source_id") == "E18" and r.get("event_type") == "api_request"]
    change_rows = [r for r in records if r.get("source_id") == "E19" and r.get("event_type") == "vendor_change"]
    fields = {"phone": 0, "email": 0, "bank_account": 0}
    for row in api_rows:
        key = str(row.get("vendor_field") or "").lower()
        if key in fields:
            fields[key] += 1
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("E18 API requests", len(api_rows))
    m2.metric("E19 vendor changes", len(change_rows))
    m3.metric("Exact request matches", summary["matched_request_count"])
    m4.metric("Unmatched records", summary["unmatched_count"])
    dist = pd.DataFrame([{"Change field": name.replace("_", " ").title(), "Count": value} for name, value in fields.items()])
    left, right = st.columns([1, 1.2])
    with left:
        st.markdown("**Reported change distribution**")
        st.dataframe(dist, hide_index=True, use_container_width=True)
    with right:
        fig = px.bar(dist, x="Change field", y="Count", color="Change field", color_discrete_sequence=[PALETTE["forest"], "#8FAE9B", PALETTE["orange"]])
        fig.update_layout(height=250, margin=dict(l=10, r=10, t=15, b=10), showlegend=False, plot_bgcolor=PALETTE["paper"], paper_bgcolor=PALETTE["paper"])
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("The event that requires independent verification")
    st.markdown(
        f"""
        <div class="tc-callout">
          <div style="font-size:.72rem;font-weight:800;letter-spacing:.12em;color:#E6A184">HIGH-PRIORITY INVESTIGATION</div>
          <div style="font-family:'Aptos Display','Segoe UI',sans-serif;font-size:1.35rem;font-weight:800;margin:.25rem 0">V-0412 · Bank-account field changed</div>
          <p>3 September 2026 · 01:44:30 UTC</p>
          <p>Request <strong>{ANCHOR_REQUEST_ID}</strong> → change <strong>{ANCHOR_CHANGE_ID}</strong></p>
          <p>Approval reference in E19: <strong>blank</strong></p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("**What we can say**")
    st.write("The supplied case summary connects the API request to the vendor change using the exact request ID. The E19 approval-reference field is blank.")
    st.markdown("**What we cannot conclude**")
    st.write("The records do not prove fraud, absence of separate approval, attacker identity, compromise of TallyBridge or financial loss.")
    st.caption("Dataset note: this application has one case-summary fixture for the V-0412 anchor and synthetic rows to reproduce the presentation's 71/71 count; the original raw E18/E19 files were not included in the PPT upload.")
    with st.expander("Open the 20-item case evidence register"):
        catalog_df = pd.DataFrame(evidence_catalog())
        st.dataframe(catalog_df, use_container_width=True, hide_index=True)
        st.caption("The register describes what the presentation says about each evidence item. It is not a replacement for the original raw evidence files.")


# -----------------------------------------------------------------------------
# PAGE 3 — Investigation reasoning
# -----------------------------------------------------------------------------
elif selected_page == "Investigation Context":
    page_heading("INVESTIGATION REASONING · CONTEXTIQ", "Unusual activity can have normal causes", "TraceCheck should test business context before raising or escalating an alert.")
    rows = [
        ("Weekly support exports", "Ten additional support export create/download cycles are described in E02.", "Compare with support schedules, tickets, recipients and retained-copy controls."),
        ("Contact sync after 1 September", "The vendor announced contact email/phone synchronization; it may explain 70 contact updates.", "Check vendor release notes and sync scope. This does not by itself explain a bank-account change."),
        ("Vendor release or maintenance", "E20 provides maintenance/build-host context.", "Check approved maintenance windows and change tickets before interpreting build-host flows."),
        ("Finance-approved bank update", "Finance may conduct vendor audits and approve vendor updates; approvals may exist outside E19.", "Obtain the original vendor request and independent Finance approval records."),
        ("Dynamic or reassigned IPs", "E20 warns that IP addresses may be reassigned.", "Verify who controlled the credential at the relevant time; do not attribute an event from IP alone."),
    ]
    df = pd.DataFrame(rows, columns=["Possible explanation", "Case context", "What to verify"])
    st.dataframe(df, use_container_width=True, hide_index=True, height=300)
    st.subheader("Unresolved questions")
    u1, u2, u3 = st.columns(3)
    with u1:
        panel("IDENTITY", "Operator identity", "The supplied records do not establish who controlled the integration credential during the requests.")
    with u2:
        panel("APPROVAL", "Separate approvals", "Approval may be stored in systems or documents outside the supplied change log.")
    with u3:
        panel("IMPACT", "Retained copies and loss", "The case summary does not establish retained copies or financial impact.")
    st.markdown(
        '<div class="tc-callout"><strong>Investigation principle</strong><p>Unusual is not automatically malicious. TraceCheck records the alternative explanation, the evidence still needed and the uncertainty that remains.</p></div>',
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# PAGE 4 — Workflow and architecture
# -----------------------------------------------------------------------------
elif selected_page == "Workflow & Architecture":
    page_heading("TECHNICAL ARCHITECTURE", "Four layers, one investigation view", "The system turns authorized evidence into reviewable findings while preserving original records.")
    workflow = [
        ("01", "Collect", "Read authorized CSV, JSON or JSONL evidence."),
        ("02", "Normalize", "Validate fields, align known timestamps and preserve originals."),
        ("03", "Connect", "Join exact request IDs, vendor IDs and related evidence."),
        ("04", "Detect", "Run deterministic rules and business-context checks."),
        ("05", "Explain", "Show record-level evidence, limitations and uncertainty."),
        ("06", "Recommend", "Suggest appropriate human verification steps."),
    ]
    cols = st.columns(3)
    for idx, (num, title, desc) in enumerate(workflow):
        with cols[idx % 3]:
            st.markdown(f'<div class="tc-panel"><span class="tc-tag">STEP {num}</span><h3>{title}</h3><p>{desc}</p></div>', unsafe_allow_html=True)
    st.write("")
    st.subheader("Four-layer architecture")
    layers = [
        ("INPUT", "LedgerOne · HelpDeskr · BlueVault · SSO · Private Link · TallyBridge register · Vendor master changes", "#DCE7DC"),
        ("PROCESS", "Import · Validate · Preserve original timestamps · Normalize fields · Store in SQLite", "#EEF0E8"),
        ("INTELLIGENCE", "Exact-ID joins · Anomaly rules · Business context · Evidence-linked explanations", "#E8E9DE"),
        ("OUTPUT", "Review queue · Evidence timeline · Alerts · Analyst notes · Exportable reports", "#F3DED2"),
    ]
    for label, text, colour in layers:
        st.markdown(
            f'<div style="background:{colour};border:1px solid {PALETTE["line"]};border-radius:10px;padding:15px 18px;margin:8px 0">'
            f'<div style="font-size:.72rem;font-weight:800;letter-spacing:.12em;color:{PALETTE["orange"]}">{label}</div>'
            f'<div style="font-weight:700;color:{PALETTE["forest"]};margin-top:4px">{text}</div></div>',
            unsafe_allow_html=True,
        )
    st.subheader("Evidence sources represented in the case")
    source_rows = [
        ("E01", "LedgerOne", "Vendor export activity"),
        ("E02", "HelpDeskr", "Support integration exports"),
        ("E03", "SSO", "Authentication and identity context"),
        ("E04", "TallyBridge register", "Integration key permissions and controls"),
        ("E05", "BlueVault", "Storage access and finance path"),
        ("E10–E11", "Policy and audit controls", "Control and audit gaps"),
        ("E15", "Private Link", "Network flow context"),
        ("E18", "API log", "Vendor-change API requests"),
        ("E19", "Vendor master", "Vendor-change records"),
        ("E20", "Maintenance context", "Release/build-host context and IP caveat"),
    ]
    st.dataframe(pd.DataFrame(source_rows, columns=["Evidence ID", "Source", "Role in investigation"]), hide_index=True, use_container_width=True)
    st.info("The current app processes local imported files and bundled fixtures. The named enterprise systems are case-source categories; no live connectors to those systems are implemented or accessed.")


# -----------------------------------------------------------------------------
# PAGE 5 — Feature progress and implementation stack
# -----------------------------------------------------------------------------
elif selected_page == "Feature Progress & Stack":
    page_heading("IMPLEMENTATION STATUS", "Five modules. One shared evidence trail", "The application implements the core local workflow proposed in the Tier 2 concept.")
    modules = [
        ("ProofPath", "Connects related records by exact request ID and displays linked source records.", "Working initial implementation"),
        ("ContextIQ", "Shows normal business explanations and applies initial support-export and large-export review rules.", "Working initial implementation"),
        ("ApprovalGuard", "Flags bank/account changes when the supplied change event has no approval reference.", "Working initial implementation"),
        ("ExplainAI", "Generates finding explanations, evidence links, uncertainty and human next steps using templates.", "Rule/template based; no trained model"),
        ("PolicyGuard", "Reviews broad integration permissions, missing recorded restrictions/expiry and finance-path access.", "Working initial implementation"),
    ]
    for start in range(0, len(modules), 2):
        cols = st.columns(2)
        for col, item in zip(cols, modules[start:start + 2]):
            with col:
                st.markdown(f'<div class="tc-panel" style="margin-bottom:10px"><span class="tc-tag">{item[0]}</span><h3>{item[1]}</h3><p><b>{item[2]}</b></p></div>', unsafe_allow_html=True)
    st.subheader("What the team has established")
    done1, done2, done3 = st.columns(3)
    done1.metric("Case evidence items reviewed", "20", help="Team case-analysis result; not the number of raw evidence files imported into this app.")
    done2.metric("Exact API-to-change joins", "71 / 71", help="Case-analysis relationship count represented by synthetic fixtures plus the V-0412 case-summary anchor.")
    done3.metric("Regression scenarios", "7", help="Bundled deterministic synthetic scenarios; not precision/recall measurement.")
    st.subheader("Implementation stack")
    stack = [
        ("DATA + LOGIC", "Python · Pandas · SQLite", "Parse CSV/JSON/JSONL, normalize events, correlate and store records."),
        ("INVESTIGATION VIEW", "Streamlit · Plotly", "Provide the investigator workspace, review screens, charts and timelines."),
        ("TEST + TEAMWORK", "Pytest · GitHub", "Run labelled scenarios, inspect false alarms and manage source revisions."),
    ]
    for label, tech, desc in stack:
        st.markdown(f'<div class="tc-panel" style="margin-bottom:10px"><span class="tc-tag">{label}</span><h3>{tech}</h3><p>{desc}</p></div>', unsafe_allow_html=True)
    st.subheader("What remains future work")
    future = [
        "Live connectors to LedgerOne, HelpDeskr, BlueVault, SSO, TallyBridge or Private Link; the competition build uses authorized local files only.",
        "Broader validation against independently labelled normal, suspicious and unseen datasets before reporting precision or recall.",
        "Production authentication, role-based access, encrypted storage, backups and deployment hardening.",
        "Any trained AI model or generative explanation service; current ExplainAI uses deterministic templates.",
    ]
    for item in future:
        st.markdown(f"- {item}")


# -----------------------------------------------------------------------------
# PAGE 6 — Evidence explorer
# -----------------------------------------------------------------------------
elif selected_page == "Evidence Explorer":
    page_heading("EVIDENCE WORKSPACE", "Evidence explorer", "Search, filter and inspect the normalized record while retaining the original imported payload.")
    records = read_records(limit=10000)
    if not records:
        st.warning("No evidence loaded. Use Data Ingestion to import records.")
    else:
        df = source_record_frame(records)
        f1, f2, f3 = st.columns([1.5, 1, 1])
        with f1:
            query = st.text_input("Search evidence", placeholder="Evidence ID, request ID, vendor, credential or description")
        with f2:
            source_opts = ["All sources"] + sorted(df["source_id"].dropna().astype(str).unique().tolist())
            source_choice = st.selectbox("Evidence source", source_opts)
        with f3:
            type_opts = ["All event types"] + sorted(df["event_type"].dropna().astype(str).unique().tolist())
            type_choice = st.selectbox("Event type", type_opts)
        filtered = df.copy()
        if query:
            mask = filtered.astype(str).apply(lambda col: col.str.contains(query, case=False, na=False)).any(axis=1)
            filtered = filtered[mask]
        if source_choice != "All sources":
            filtered = filtered[filtered["source_id"] == source_choice]
        if type_choice != "All event types":
            filtered = filtered[filtered["event_type"] == type_choice]
        st.caption(f"Showing {len(filtered):,} of {len(df):,} evidence records")
        st.dataframe(filtered, use_container_width=True, hide_index=True, height=390)
        record_options = filtered["id"].dropna().astype(str).tolist()
        if record_options:
            selected_id = st.selectbox("Inspect full evidence record", record_options)
            record = get_record_by_id(selected_id)
            if record:
                left, right = st.columns(2)
                with left:
                    st.markdown("**Normalized fields**")
                    st.json({k: v for k, v in record.items() if k != "payload"})
                with right:
                    st.markdown("**Preserved original payload**")
                    st.json(record.get("payload", {}))
                st.caption(f"Provenance: {record.get('record_origin')} · Timezone status: {record.get('timezone_status')}")


# -----------------------------------------------------------------------------
# PAGE 6 — ProofPath correlations
# -----------------------------------------------------------------------------
elif selected_page == "ProofPath Correlations":
    page_heading("MODULE 01 · PROOFPATH", "Cross-system evidence correlation", "Connect API requests to vendor changes using exact request identifiers.")
    with st.container(border=True):
        st.markdown("**Exact request-ID lookup**")
        request_query = st.text_input("Request ID", value=ANCHOR_REQUEST_ID, placeholder="Enter a request ID")
        with database() as conn:
            result = get_correlation(conn, request_query.strip())
        if result["pairs"]:
            for pair in result["pairs"]:
                api = pair["api"]
                change = pair["change"]
                st.markdown(
                    f'<div class="tc-callout"><div style="font-size:.7rem;font-weight:800;letter-spacing:.12em;color:#E6A184">EXACT IDENTIFIER MATCH</div>'
                    f'<div style="font-weight:800;font-size:1.12rem;margin:.25rem 0">{html.escape(str(pair["request_id"]))}</div>'
                    f'<p>E18 / API request: <b>{html.escape(str(api.get("id")))}</b> &nbsp; → &nbsp; E19 / Change: <b>{html.escape(str(change.get("id")))}</b></p>'
                    f'<p>Vendor: <b>{html.escape(str(change.get("vendor_id") or "Unknown"))}</b> · Field: <b>{html.escape(str(change.get("vendor_field") or "Not recorded"))}</b> · Approval ref: <b>{html.escape(str(change.get("approval_ref") or "Blank / not recorded"))}</b></p></div>',
                    unsafe_allow_html=True,
                )
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**API source record**")
                    st.json(api)
                with c2:
                    st.markdown("**Vendor change record**")
                    st.json(change)
        else:
            st.warning("No exact API-to-change pair found for that request ID in the currently imported evidence.")
    st.subheader("Correlation coverage")
    with database() as conn:
        overall = get_correlation(conn)
    a, b, c = st.columns(3)
    a.metric("Matched request IDs", overall["matched_request_count"])
    b.metric("Unmatched records", overall["unmatched_count"])
    c.metric("Exact pairs", len(overall["pairs"]))
    if overall["pairs"]:
        pair_rows = [{
            "Request ID": p["request_id"], "API record": p["api"].get("id"),
            "Change record": p["change"].get("id"), "Vendor": p["change"].get("vendor_id"),
            "Changed field": p["change"].get("vendor_field"), "Provenance": p["change"].get("record_origin"),
        } for p in overall["pairs"]]
        st.dataframe(pd.DataFrame(pair_rows), use_container_width=True, hide_index=True, height=350)
    st.caption("The 71/71 count is an investigation/correlation result. It is not a detection-accuracy score. Bundled sample data includes synthetic pairs to reproduce this count.")


# -----------------------------------------------------------------------------
# PAGE 7 — ContextIQ
# -----------------------------------------------------------------------------
elif selected_page == "ContextIQ":
    page_heading("MODULE 02 · CONTEXTIQ", "Business-aware activity review", "Check whether unusual patterns have legitimate operational explanations before escalation.")
    records = read_records(limit=10000)
    changes = [r for r in records if r.get("event_type") == "api_request" and r.get("source_id") == "E18"]
    field_counts: dict[str, int] = {}
    for rec in changes:
        key = rec.get("vendor_field") or "unknown"
        field_counts[key] = field_counts.get(key, 0) + 1
    m1, m2, m3 = st.columns(3)
    m1.metric("Phone updates", field_counts.get("phone", 0))
    m2.metric("Email updates", field_counts.get("email", 0))
    m3.metric("Bank-account updates", field_counts.get("bank_account", 0))
    st.markdown("**Business explanations considered in the case**")
    context = [
        ("Contact synchronization", "Vendor-announced sync may explain phone and email updates.", "Does not by itself explain a bank-account change."),
        ("Routine support exports", "Weekly exports can be legitimate business activity.", "E02 notes ten additional create/download cycles that need schedule and ticket verification."),
        ("Maintenance or release", "E20 provides maintenance/build-host context.", "Confirm approved change tickets and time window."),
        ("Finance-approved update", "A vendor bank update could have been approved outside the E19 log.", "Obtain the original request and independent approval evidence."),
        ("Dynamic IP assignment", "IP addresses can be reassigned.", "Do not infer operator identity from an IP alone."),
    ]
    for title, explanation, caution in context:
        with st.expander(title, expanded=(title == "Contact synchronization")):
            st.write(explanation)
            st.warning(caution)
    st.subheader("Context-related findings generated from the current dataset")
    context_rules = {rule["id"] for rule in RULE_CATALOG if rule["module"] == "ContextIQ"}
    relevant = [f for f in read_findings() if f["rule_id"] in context_rules]
    if relevant:
        st.dataframe(finding_frame(relevant), use_container_width=True, hide_index=True)
        for f in relevant:
            with st.expander(f"{f['severity']} · {f['title']}"):
                render_finding_detail(f)
    else:
        st.info("No ContextIQ rules triggered in the current dataset.")
    st.info("ContextIQ currently uses deterministic initial rules and explicit case-context notes. It does not infer business intent or automatically whitelist activity.")


# -----------------------------------------------------------------------------
# PAGE 8 — ApprovalGuard
# -----------------------------------------------------------------------------
elif selected_page == "ApprovalGuard":
    page_heading("MODULE 03 · APPROVALGUARD", "Sensitive financial change review", "Identify financial-field changes and show whether an approval reference is present in the supplied change record.")
    records = read_records(limit=10000)
    bank_changes = [r for r in records if r.get("event_type") in {"vendor_change", "vendor_edit", "vendor_update"} and any(t in str(r.get("vendor_field") or "").lower() for t in ("bank", "account"))]
    if bank_changes:
        bank_df = source_record_frame(bank_changes)
        st.dataframe(bank_df, use_container_width=True, hide_index=True)
        for record in bank_changes:
            with st.expander(f"{record.get('vendor_id') or 'Vendor unknown'} · {record.get('id')} · {record.get('vendor_field')}"):
                st.json(record)
                if not record.get("approval_ref"):
                    st.error("No approval reference is recorded in this change event.")
                    st.write("Recommended action: verify the vendor request and Finance approval independently.")
                else:
                    st.success(f"Approval reference present: {record['approval_ref']}")
    else:
        st.info("No bank/account change records found in the current evidence set.")
    st.markdown(
        '<div class="tc-risk"><b>Interpretation safeguard:</b> A blank approval_ref field is evidence that approval is not recorded in that event. It does not establish that a separate approval record does not exist.</div>',
        unsafe_allow_html=True,
    )
    ag = [f for f in read_findings() if f["rule_id"] == "FINANCIAL_CHANGE_NO_APPROVAL"]
    st.subheader("Approval verification findings")
    if ag:
        for f in ag:
            with st.expander(f"{f['severity']} · {f['title']}", expanded=True):
                render_finding_detail(f)


# -----------------------------------------------------------------------------
# PAGE 9 — ExplainAI
# -----------------------------------------------------------------------------
elif selected_page == "ExplainAI":
    page_heading("MODULE 04 · EXPLAINAI", "Evidence-backed finding explanations", "Convert technical rules into clear investigation narratives, supported by records and explicit uncertainty.")
    st.markdown(
        '<div class="tc-callout"><strong>ExplainAI design principle</strong><p>Every finding should explain what happened, why it was flagged, which records support it, what remains uncertain and what a reviewer should verify next.</p></div>',
        unsafe_allow_html=True,
    )
    st.caption("Current implementation: deterministic rule templates. No trained model or external AI service is claimed.")
    basic, trace = st.columns(2)
    with basic:
        panel("BASIC MONITORING", "Bank account was updated", "A simple event notification gives an investigator little context by itself.")
    with trace:
        panel("TRACECHECK REVIEW", "V-0412 bank details changed", "E18 request matches E19 change · approval reference blank in E19 · next check: Finance/vendor approval.")
    findings = read_findings()
    if findings:
        selected_finding = st.selectbox("Choose a finding", findings, format_func=lambda f: f"{f['severity']} · {f['title']} · {f['id']}")
        render_finding_detail(selected_finding)
        with st.expander("Inspect structured explanation payload"):
            st.json({
                "finding_id": selected_finding["id"], "rule_id": selected_finding["rule_id"],
                "known_facts": selected_finding["summary"], "reason": selected_finding["explanation"],
                "evidence_record_ids": selected_finding["evidence_record_ids"],
                "source_evidence_ids": selected_finding["source_evidence_ids"],
                "uncertainty": "The finding is a review trigger and does not establish malicious intent or attribution.",
                "recommended_action": selected_finding["recommendation"],
            })
    else:
        st.info("No findings are available. Import evidence or run the analysis engine.")


# -----------------------------------------------------------------------------
# PAGE 10 — PolicyGuard
# -----------------------------------------------------------------------------
elif selected_page == "PolicyGuard":
    page_heading("MODULE 05 · POLICYGUARD", "Credential and access-control review", "Identify broad integration permissions and access patterns that need a policy or ownership review.")
    records = read_records(limit=10000)
    creds = [r for r in records if r.get("event_type") in {"credential_inventory", "credential_config", "integration_credential"}]
    accesses = [r for r in records if r.get("event_type") in {"storage_access", "object_access", "file_access"}]
    l, r = st.columns(2)
    with l:
        st.subheader("Integration credential inventory")
        if creds:
            for rec in creds:
                with st.expander(f"{rec.get('credential_id') or 'Credential'} · {rec.get('source_id')}", expanded=True):
                    st.json(rec.get("payload", rec))
                    st.write("Review broad scope, IP restriction, expiry and business owner.")
        else:
            st.info("No credential inventory records imported.")
    with r:
        st.subheader("Finance-path access")
        if accesses:
            st.dataframe(source_record_frame(accesses), use_container_width=True, hide_index=True)
            for rec in accesses:
                if "finance" in str(rec.get("resource_path") or "").lower():
                    st.warning(f"Finance-related path: {rec.get('resource_path')} · Credential: {rec.get('credential_id')}")
        else:
            st.info("No storage-access records imported.")
    pg_rules = {rule["id"] for rule in RULE_CATALOG if rule["module"] == "PolicyGuard"}
    pg_findings = [f for f in read_findings() if f["rule_id"] in pg_rules]
    st.subheader("PolicyGuard findings")
    if pg_findings:
        st.dataframe(finding_frame(pg_findings), use_container_width=True, hide_index=True)
        for f in pg_findings:
            with st.expander(f"{f['severity']} · {f['title']}"):
                render_finding_detail(f)
    st.caption("Recommendations are review guidance only. TraceCheck does not rotate keys, change permissions or access external systems.")


# -----------------------------------------------------------------------------
# PAGE 11 — Review queue
# -----------------------------------------------------------------------------
elif selected_page == "Review Queue":
    page_heading("INVESTIGATOR WORKSPACE", "Finding review queue", "Review findings, record analyst decisions and preserve a local audit history.")
    f1, f2 = st.columns(2)
    with f1:
        status_filter = st.selectbox("Status filter", ["All", "Open", "In Review", "Resolved", "False Positive"])
    with f2:
        severity_filter = st.selectbox("Severity filter", ["All", "HIGH", "MEDIUM", "LOW", "CRITICAL"])
    findings = read_findings("" if status_filter == "All" else status_filter, "" if severity_filter == "All" else severity_filter)
    if not findings:
        st.success("No findings match the selected filters.")
    else:
        st.dataframe(finding_frame(findings), use_container_width=True, hide_index=True)
        selected = st.selectbox("Select finding to review", findings, format_func=lambda f: f"{f['severity']} · {f['title']} · {f['id']}")
        render_finding_detail(selected)
        st.markdown("### Analyst decision")
        with st.form(key=f"review_{selected['id']}"):
            new_status = st.selectbox("Review status", ["Open", "In Review", "Resolved", "False Positive"], index=["Open", "In Review", "Resolved", "False Positive"].index(selected.get("status", "Open")) if selected.get("status", "Open") in ["Open", "In Review", "Resolved", "False Positive"] else 0)
            note = st.text_area("Analyst notes", value=selected.get("analyst_note", ""), max_chars=2000, help="Record verification steps, supporting records or a reason for resolution.")
            submitted = st.form_submit_button("Save review decision", type="primary")
        if submitted:
            try:
                with database() as conn:
                    updated = update_finding(conn, selected["id"], new_status, note)
                if updated:
                    st.success("Review decision saved to SQLite and added to the local audit log.")
                    st.rerun()
            except ValueError as exc:
                st.error(str(exc))
    with st.expander("Recent analyst/system audit events"):
        with database() as conn:
            audit = get_audit_log(conn, 50)
        if audit:
            audit_rows = []
            for event in audit:
                try:
                    details = json.loads(event.get("details_json") or "{}")
                except Exception:
                    details = {}
                audit_rows.append({"Time": event.get("created_at"), "Action": event.get("action"), "Target": event.get("target_id"), "Details": json.dumps(details, ensure_ascii=False)})
            st.dataframe(pd.DataFrame(audit_rows), use_container_width=True, hide_index=True)
        else:
            st.caption("No audit events yet.")


# -----------------------------------------------------------------------------
# PAGE 12 — Investigation timeline
# -----------------------------------------------------------------------------
elif selected_page == "Investigation Timeline":
    page_heading("INVESTIGATION WORKSPACE", "Cross-source event timeline", "Review event order without hiding original timestamps, missing time zones or uncertain identity context.")
    records = read_records(limit=10000)
    df = source_record_frame(records)
    if df.empty:
        st.info("No evidence records available.")
    else:
        source_filter = st.selectbox("Filter source", ["All"] + sorted(df["source_id"].dropna().astype(str).unique().tolist()))
        timeline = df.copy()
        if source_filter != "All":
            timeline = timeline[timeline["source_id"] == source_filter]
        timeline["Parsed UTC"] = pd.to_datetime(timeline["timestamp_utc"], utc=True, errors="coerce")
        valid = timeline.dropna(subset=["Parsed UTC"])
        if not valid.empty:
            fig = px.scatter(
                valid, x="Parsed UTC", y="source_id", color="event_type", hover_name="id",
                hover_data={"request_id": True, "vendor_id": True, "credential_id": True, "Parsed UTC": True},
                color_discrete_sequence=[PALETTE["forest"], PALETTE["orange"], "#739B82", "#B58C54", "#557F9C"],
            )
            fig.update_traces(marker=dict(size=11, line=dict(width=1, color="#FFFFFF")))
            fig.update_layout(height=420, margin=dict(l=10, r=10, t=20, b=10), plot_bgcolor=PALETTE["paper"], paper_bgcolor=PALETTE["paper"], legend_title_text="Event type")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No records have a timezone-aware, parseable timestamp. Original timestamp strings remain available below.")
        st.markdown("**Timeline records**")
        st.dataframe(timeline[["id", "source_id", "event_type", "timestamp_original", "timestamp_utc", "timezone_status", "request_id", "vendor_id", "actor"]], use_container_width=True, hide_index=True, height=350)
        unknown = int((timeline["timezone_status"] != "known").sum())
        if unknown:
            st.warning(f"{unknown} visible record(s) have missing, unknown or unparseable timezone information. TraceCheck does not guess a timezone.")


# -----------------------------------------------------------------------------
# PAGE 13 — Validation lab
# -----------------------------------------------------------------------------
elif selected_page == "Validation Lab":
    page_heading("VALIDATION · FALSE-ALARM CHECKS", "Validation laboratory", "Exercise normal, suspicious and control-gap scenarios against the deterministic rule set.")
    st.markdown("The test suite is a repeatable regression check. It is not a statistically valid accuracy measurement on the original raw archive.")
    result = run_validation()
    total, passed, failed = st.columns(3)
    total.metric("Scenarios", result["total"])
    passed.metric("Passed", result["passed"])
    failed.metric("Needs attention", result["total"] - result["passed"])
    if result["status"] == "PASS":
        st.success("All bundled validation scenarios produced their expected rule behaviour.")
    else:
        st.error("One or more validation scenarios need investigation.")
    if st.button("Run validation again", type="primary"):
        st.session_state["validation_last_run"] = datetime.now(timezone.utc).isoformat()
        st.rerun()
    validation_df = pd.DataFrame(result["results"])
    if not validation_df.empty:
        validation_df["Result"] = validation_df["passed"].map({True: "PASS", False: "FAIL"})
        st.dataframe(validation_df[["name", "expected", "observed", "matched_rules", "Result"]], use_container_width=True, hide_index=True)
    st.subheader("Scenarios represented in the Tier 2 plan")
    cases = [
        ("NORMAL", "Weekly Support export", "No unnecessary alert"),
        ("NORMAL", "Scheduled nightly sync", "Recognize normal pattern"),
        ("REVIEW", "Large unusual export", "Flag with source records"),
        ("REVIEW", "Bank edit with blank approval reference", "Join API + change and request approval verification"),
        ("REVIEW", "Finance path accessed by key", "Explain access-scope concern"),
    ]
    st.dataframe(pd.DataFrame(cases, columns=["Class", "Scenario", "Expected behaviour"]), use_container_width=True, hide_index=True)
    st.info(result["notice"])
    st.warning("Do not report 71/71 as precision, recall or detection accuracy. It is the count of exact E18/E19 request-ID relationships represented in the case analysis and bundled fixture.")


# -----------------------------------------------------------------------------
# PAGE 14 — Data ingestion
# -----------------------------------------------------------------------------
elif selected_page == "Data Ingestion":
    page_heading("COLLECT · VALIDATE · NORMALIZE", "Evidence ingestion", "Import authorized evidence files into the local SQLite store. Original payloads are retained for traceability.")
    st.markdown(f"Supported files: **CSV, JSON, JSONL** · Maximum size: **{MAX_IMPORT_BYTES // (1024 * 1024)} MB** · Maximum records: **{MAX_IMPORT_RECORDS:,}**")
    dataset_notice()
    uploaded = st.file_uploader("Choose evidence file", type=["csv", "json", "jsonl", "ndjson"], accept_multiple_files=False)
    if uploaded is not None:
        try:
            text = uploaded.getvalue().decode("utf-8-sig")
            parsed = parse_upload(uploaded.name, text)
            st.success(f"File parsed successfully: {len(parsed):,} record(s).")
            st.markdown("**Pre-import preview**")
            st.dataframe(pd.DataFrame(parsed).head(15), use_container_width=True, hide_index=True)
            st.caption("Review the preview before importing. Records with no recognized event_type/type are rejected by the importer.")
            if st.button("Import records and run analysis", type="primary"):
                with database() as conn:
                    import_result = store_records(conn, uploaded.name, parsed)
                    analysis_result = analyze_database(conn)
                st.success(
                    f"Import complete · {import_result['imported']} added · "
                    f"{import_result['skipped_duplicates']} duplicate(s) skipped · "
                    f"{len(import_result['errors'])} row error(s). "
                    f"Analysis generated {analysis_result['findings_generated']} finding(s)."
                )
                if import_result["errors"]:
                    st.dataframe(pd.DataFrame(import_result["errors"]), use_container_width=True, hide_index=True)
                st.rerun()
        except Exception as exc:
            st.error(f"Could not read this file: {exc}")
    st.subheader("Import history")
    with database() as conn:
        batches = get_import_batches(conn, 100)
    if batches:
        st.dataframe(pd.DataFrame(batches), use_container_width=True, hide_index=True)
    else:
        st.caption("No import batches recorded.")
    st.markdown("**Expected common fields**")
    st.code("record_id, source_id, source_system, event_type, timestamp, request_id, vendor_id, credential_id, vendor_field, approval_ref", language="text")
    st.caption("Timestamps without an explicit timezone are retained as original text and labelled unknown; the system does not silently assume UTC.")


# -----------------------------------------------------------------------------
# PAGE 15 — Reports and exports
# -----------------------------------------------------------------------------
elif selected_page == "Reports & Exports":
    page_heading("REPORTING", "Investigation reports & exports", "Export the evidence trail, correlated findings and analyst review history for further examination.")
    with database() as conn:
        summary = get_summary(conn)
        findings = get_findings(conn)
        records = get_records(conn, limit=10000)
        correlation = get_correlation(conn)
        audit = get_audit_log(conn, 200)
    report = {
        "report_title": "TraceCheck Evidence-Based Investigation Report",
        "team": "RN WebMinds",
        "competition": "CRIMEATHON '26",
        "case_id": "CR-26-047",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "summary": summary,
        "findings": findings,
        "correlation_summary": {
            "matched_request_count": correlation["matched_request_count"],
            "unmatched_count": correlation["unmatched_count"],
            "pair_count": len(correlation["pairs"]),
        },
        "v0412_request_id": ANCHOR_REQUEST_ID,
        "v0412_change_id": ANCHOR_CHANGE_ID,
        "dataset_notice": "Bundled sample rows are synthetic or case-summary fixtures, not the original CRIMEATHON raw evidence archive.",
        "interpretation_guardrail": "A blank approval reference in E19 does not prove separate approval was absent elsewhere. Findings are review triggers, not incident verdicts.",
        "audit_events": audit,
    }
    st.markdown("**Available exports**")
    e1, e2, e3 = st.columns(3)
    with e1:
        with database() as conn:
            evidence_csv = csv_export(conn, "evidence")
        st.download_button("Download evidence CSV", evidence_csv, file_name="tracecheck-evidence.csv", mime="text/csv", use_container_width=True)
    with e2:
        with database() as conn:
            findings_csv = csv_export(conn, "findings")
        st.download_button("Download findings CSV", findings_csv, file_name="tracecheck-findings.csv", mime="text/csv", use_container_width=True)
    with e3:
        st.download_button("Download investigation JSON", json.dumps(report, indent=2, ensure_ascii=False), file_name="tracecheck-investigation-report.json", mime="application/json", use_container_width=True)
    st.subheader("Report preview")
    st.json({k: v for k, v in report.items() if k not in {"findings", "audit_events"}})
    st.subheader("Finding summary")
    st.dataframe(finding_frame(findings), use_container_width=True, hide_index=True)


# -----------------------------------------------------------------------------
# PAGE 16 — Limitations and roadmap
# -----------------------------------------------------------------------------
elif selected_page == "Limitations & Roadmap":
    page_heading("LIMITATIONS · ROADMAP", "What we know, and what comes next", "The application makes uncertainty visible and separates current functionality from future integrations.")
    left, right = st.columns(2)
    with left:
        st.subheader("What TraceCheck must handle")
        limits = [
            "Different clocks and time zones across systems.",
            "Missing IP addresses or operator identities.",
            "Normal activity that resembles unusual behaviour.",
            "Approvals stored outside the supplied change log.",
            "Unknown variations and false alarms.",
            "Reassigned IP addresses that cannot establish attribution.",
            "Evidence gaps that may reflect incomplete imports.",
        ]
        for item in limits:
            st.markdown(f"- {item}")
    with right:
        st.subheader("Development roadmap")
        roadmap = [
            ("01", "Ingest and normalize evidence", "Working local CSV / JSON / JSONL ingestion and timestamp labelling."),
            ("02", "Add cross-system joins and rules", "Working exact request-ID joins and initial deterministic detection rules."),
            ("03", "Build review screen and timeline", "Working local review queue, analyst notes, timeline and exports."),
            ("04", "Test normal, suspicious and unseen cases", "Seven bundled regression scenarios; broader unseen-variation testing remains future work."),
            ("05", "Authorized source connectors", "Future only; no live enterprise connectors are included in this competition build."),
        ]
        for num, title, desc in roadmap:
            st.markdown(f'<div class="tc-panel" style="margin-bottom:9px"><span class="tc-tag">{num}</span><h3>{title}</h3><p>{desc}</p></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="tc-callout"><strong>Expected benefit</strong><p>TraceCheck makes investigation of third-party integration activity easier to review by connecting records, explaining potential risks and identifying the evidence still needed.</p></div>',
        unsafe_allow_html=True,
    )
    st.warning("The current build is a local defensive investigation MVP. It is not a production SIEM, has no live enterprise connectors and does not autonomously block or contain activity.")


# -----------------------------------------------------------------------------
# PAGE 17 — Settings
# -----------------------------------------------------------------------------
elif selected_page == "System Settings":
    page_heading("SYSTEM ADMINISTRATION", "Local environment settings", "Inspect the local database, review import history and manage the temporary sample dataset.")
    summary = read_summary()
    m1, m2, m3 = st.columns(3)
    m1.metric("Stored records", summary["total_records"])
    m2.metric("Evidence sources", summary["source_count"])
    m3.metric("Generated findings", summary["finding_count"])
    st.markdown("**Database location**")
    st.code(str(DB_PATH), language="text")
    st.markdown("**Rule thresholds currently used by the initial MVP**")
    thresholds = pd.DataFrame([
        ("Large export", "5,000 rows or 25 MiB", "Illustrative heuristic; calibrate to a real baseline."),
        ("Additional support export cycles", "10 or more unscheduled support export records", "Case-context review trigger; count alone is not proof of misuse."),
        ("Sensitive bank change", "Bank/account field with blank approval reference", "Review trigger only; separate approval may exist elsewhere."),
        ("Broad integration key", "Broad read/write or all-modules with no recorded IP restriction or expiry", "Credential-control concern; does not prove misuse."),
    ], columns=["Rule", "Current trigger", "Interpretation"])
    st.dataframe(thresholds, use_container_width=True, hide_index=True)
    st.subheader("Analysis controls")
    if st.button("Run analysis engine", type="primary"):
        result = run_analysis()
        st.success(f"Processed {result['records_analyzed']} records and generated {result['findings_generated']} findings.")
        st.rerun()
    st.subheader("Temporary sample dataset")
    st.warning("Resetting the sample dataset deletes imported records, findings and analyst notes from this local database, then reloads the bundled example data. This action cannot be undone.")
    confirm = st.checkbox("I understand this will delete current local evidence and review notes.", key="confirm_reset_data")
    if st.button("Reset database to bundled example dataset", disabled=not confirm):
        result = seed_demo(reset=True)
        with database() as conn:
            analysis = analyze_database(conn)
        st.success(f"Sample dataset restored: {result['record_count']} records. {analysis['findings_generated']} findings generated.")
        st.rerun()
    st.subheader("Recent audit history")
    with database() as conn:
        audit = get_audit_log(conn, 100)
    if audit:
        st.dataframe(pd.DataFrame(audit), use_container_width=True, hide_index=True)
    else:
        st.caption("No audit events yet.")


# Footer
st.markdown("---")
st.caption("TraceCheck · RN WebMinds · CRIMEATHON ’26 · DEFENCE · Local evidence-processing environment · Findings support human review and do not establish attribution or fraud.")
