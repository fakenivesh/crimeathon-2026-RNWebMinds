# CRIMEATHON ’26 — RN WebMinds

**Case:** CR-26-047 · Harbor & Finch Freight Pvt. Ltd. (fictional)
**Track:** DEFENCE
**Project:** TraceCheck — evidence-to-action security investigation
**Competition:** 19–20 November 2026

RN WebMinds investigated third-party integration access and vendor-record changes across the supplied case materials, then built TraceCheck, a local application for importing evidence, correlating records, surfacing rule-based findings, and documenting human review.

> **Finding in brief:** The supplied records show an over-permissive, overdue-reviewed integration posture and successful integration-associated activity involving large exports and sensitive financial records. In the 1–7 September extracts, all 71 API-channel vendor changes in E19 have matching E18 request IDs: 44 phone updates, 26 email updates, and one bank-account update. The bank-account change for V-0412 has no approval reference in that record. These facts warrant investigation; they do not establish attacker identity, credential compromise, fraud, unauthorized payment, or financial loss.

## Project contents

| Path | Contents |
|---|---|
| `Given/` | The 20 supplied case evidence items, submission guide, and original case file. |
| `report_1/` | Four team members’ evidence findings and scoped analyses. |
| `doc.md` | Earlier investigation and competition planning notes. Some sections predate the selected Defense track; use this README and the current TraceCheck docs for the final project direction. |
| `TraceCheck_Project/` | The runnable local Streamlit application, source code, sample data, tests, and app documentation. |
| `LICENSE` | Apache License 2.0. |

## Investigation summary

### The environment

Harbor & Finch is a fictional Chennai-based logistics company. Its case systems include LedgerOne (finance), HelpDeskr (support), BlueVault (file storage), staff SSO, and TallyBridge Connect, an external integration between LedgerOne and HelpDeskr. Different systems use different clocks and identity labels, so timestamps and actors must be interpreted in their source context.

### Main evidence-backed control concerns

- **Integration configuration:** E04 lists LedgerOne key `key-tb-07` as active with `read:write all-modules`, no recorded IP restriction or token lifetime, and a last review dated 12 June 2024. HelpDeskr credential `tb-sync-svc` is active with `admin` scope and similarly absent restrictions and overdue review. Legacy key `key-tb-03` is still listed active despite last use in January 2025.
- **Exports and sensitive access:** E01 records two successful vendor export/download sequences on 12 August (9,840 and 9,835 records) using `key-tb-07`, followed by sensitive bank-detail and payment activity on 17–19 August. E02 records credential-term searches, a ticket read, and ten HelpDeskr export cycles on 11–12 August; nine export deletions succeeded and the final deletion returned an error. E05 records successful access by `bvk-7f3a` to finance-related paths on 14–16 August.
- **Vendor changes:** E18 and E19 contain 71 API vendor updates connected by exact request ID. The 3 September V-0412 bank-account change (`chg-8b9888c39b`, request `req-5f61b0de8`) followed reads of the vendor’s bank details and scheduled payments. E19 has a blank approval-reference field for this change; that field alone cannot rule out separate approval elsewhere.
- **Governance and monitoring:** E10 sets integration requirements for least privilege, restrictions, credential expiry, annual reviews, and alerts for bulk exports and export deletions. E11 records earlier open audit findings on credential controls, export monitoring, and vendor reviews. The supplied evidence does not establish whether later remediation or exceptions exist.

### Competing explanations and limits

Some activity may be legitimate. E16 announces contact-detail synchronization beginning 1 September, which may explain the phone and email updates. E20 describes build-host maintenance, release changes, and other unverified public context. Routine Support exports, Finance audits, and system maintenance also occur. These explanations need to be checked against source records, approvals, and change tickets.

The evidence does not identify who controlled the relevant credentials or IP addresses; prove that a cyberattack or credential compromise occurred; establish the contents or onward transfer of exported files; show that the changed bank details were used for a payment; or establish fraud or loss. Vendor notices (E12/E16), indicators (E17), and saved public records (E20) are leads to compare with internal logs, not independent proof of attribution.

For file-level observations, caveats, timelines, and follow-up questions, see [Member 1 findings](report_1/member_1_findings.md), [Member 2 findings](report_1/member_2_findings.md), [Member 3 findings](report_1/member_3_findings.md), and [Member 4 findings](report_1/member_4_findings.md).

## TraceCheck

TraceCheck is a local Python and Streamlit investigation MVP. It accepts CSV, JSON, JSONL, and NDJSON files, validates and normalizes records, stores evidence in SQLite, joins API and vendor-change records by exact request ID, runs six deterministic investigation rules, and presents findings with source records, uncertainty, and human review steps. Analysts can record a finding status and notes, view a timeline, run seven validation scenarios, and export evidence and findings as CSV or a JSON report.

Its five named workspaces are ProofPath, ContextIQ, ApprovalGuard, ExplainAI, and PolicyGuard. “ExplainAI” currently uses deterministic rule templates; it is not a trained AI model. TraceCheck does not connect to the named enterprise systems, block activity, or change credentials.

### Demonstration data provenance

The bundled 160-record dataset is a demonstration fixture, not the original CRIMEATHON raw evidence. It includes a V-0412 anchor based on details stated in the team presentation, plus synthetic records that exercise the reported 71/71 request-ID correlation and other rules. The other 70 API/change pairs and supporting E01/E02/E03/E04/E05/E15/E20 examples are synthetic or case-summary fixtures. Treat only imported, authorized source files as raw evidence. The app labels seeded records by origin; see [`TraceCheck_Project/data/README.md`](TraceCheck_Project/data/README.md) and [`TraceCheck_Project/docs/CRIMEATHON_ALIGNMENT.md`](TraceCheck_Project/docs/CRIMEATHON_ALIGNMENT.md).

**The 71/71 figure is a correlation count, not detection accuracy.** A successful validation scenario means the configured example behaved as expected; it does not establish real-world precision, recall, or readiness for production.

### Run the application

Requires Python 3.10 or later. From this repository:

```bash
cd TraceCheck_Project
python -m venv .venv
source .venv/bin/activate       # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

Then open <http://localhost:8501>. On Linux/macOS, `./start.sh` automates environment setup and launch; on Windows, run `start_windows.bat`. The app defaults to a local-only server. Keep the terminal open during use and stop it with Ctrl+C.

### Application features

- Import and preview local CSV/JSON/JSONL/NDJSON records; normalize common fields and preserve original payloads.
- Correlate API requests and vendor changes using exact request IDs.
- Review six deterministic rules for sensitive bank changes, broad integration access, support export bursts, large exports, finance-path access, and unmatched vendor activity.
- Track finding status and analyst notes in SQLite, with a local audit history.
- Explore records and correlations, plot an investigation timeline, run the synthetic validation lab, and export evidence/findings.
- Browse case evidence, investigation context, architecture, limitations, and development roadmap.

Rule thresholds are initial demonstration heuristics and need calibration against authorized baseline data before operational use. The MVP has no live enterprise connectors, production SIEM pipeline, multi-user authentication, role-based access, autonomous response, or independent accuracy benchmark. Do not expose it to a public/shared network or import real secrets or unsanitized personal/financial data.

## Verification record

The project’s recorded verification in `TraceCheck_Project/docs/VERIFICATION.md` reports Python compilation success, **13 passing automated tests**, all 18 navigation branches exercised with a lightweight UI stub, a temporary-SQLite backend integration check, 71 exact request joins, and 7/7 synthetic validation scenarios. The environment lacked Streamlit and could not reach the package index, so the real Streamlit server and browser layout were not verified in that environment. These results verify the recorded build checks, not production readiness or accuracy on the original raw evidence archive.

To rerun the tests from the app directory:

```bash
cd TraceCheck_Project
pytest -q
```

## Further documentation

- [TraceCheck application guide](TraceCheck_Project/README.md) — installation, navigation, imports, rules, and project structure.
- [Demo runbook](TraceCheck_Project/docs/PRESENTATION_DEMO_RUNBOOK.md) — suggested competition walkthrough and judge questions.
- [Presentation alignment](TraceCheck_Project/docs/CRIMEATHON_ALIGNMENT.md) — maps the Tier 2 concepts to implemented features and records provenance limits.
- [Verification record](TraceCheck_Project/docs/VERIFICATION.md) — checks run and environment limitations.
- [Submission guide](Given/CRIMEATHON26_Final_Submission_Guide.pdf) — official competition submission requirements.

## Team

RN WebMinds has four members. Their investigation assignments and individual findings are documented in `report_1/`.
