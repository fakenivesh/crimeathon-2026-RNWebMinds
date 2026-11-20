# TraceCheck — Evidence-to-Action Security Intelligence

**Team:** RN WebMinds  
**Competition:** CRIMEATHON '26  
**Case:** CR-26-047 · Harbor & Finch  
**Track:** DEFENCE

TraceCheck is a locally executable **Python + Streamlit security investigation application**. It ingests authorized evidence files, validates and normalizes records, stores the original payloads in SQLite, correlates related events by exact identifiers, runs deterministic detection rules, presents evidence-backed explanations and supports human review.

It is built around the ten-slide RN WebMinds Tier 2 presentation. The application includes the case narrative, alternative explanations, six-step workflow, four-layer architecture, the five named modules, validation scenarios, known limitations and development roadmap.

> **Dataset provenance:** The bundled example dataset is a demonstration fixture, not the original CRIMEATHON raw evidence archive. It contains one case-summary fixture for the V-0412 anchor stated in the presentation and synthetic records used to reproduce the reported E18/E19 count and exercise the application. Every bundled record has a `record_origin` label. Do not describe synthetic records as original evidence. See [`data/README.md`](data/README.md).

## What is implemented

| Presentation concept | Working application behaviour |
|---|---|
| Collect | Import CSV, JSON and JSONL files through Streamlit; validate structure and basic required fields |
| Normalize | Standardize field aliases, parse timezone-aware timestamps, label missing/unknown time zones and preserve original payloads |
| Connect | ProofPath correlates API requests and vendor-change records using exact request IDs |
| Detect | Six deterministic rules identify sensitive bank changes, broad integration permissions, additional support exports, large exports, finance-path access and unmatched vendor changes |
| Explain | ExplainAI produces rule-based summaries, evidence references, uncertainty and recommended human checks |
| Recommend | Findings include practical next steps; no autonomous response or blocking |
| ContextIQ | Displays case alternatives and applies initial support-export / large-export review heuristics |
| ApprovalGuard | Reviews bank/account changes and missing approval references |
| PolicyGuard | Reviews broad credential permissions, missing recorded restrictions/expiry and finance-path access |
| Review queue | Persist finding status and analyst notes to SQLite; append local audit events |
| Timeline | Plot timezone-aware event timestamps by source and event type; retain unknown timestamps visibly |
| Validation lab | Run seven deterministic synthetic regression scenarios |
| Reports | Download evidence CSV, findings CSV and a JSON investigation report |
| Case materials | Evidence index E01–E20 and problem / uncertainty / architecture / roadmap views |

## The case anchor

The V-0412 finding is represented using the exact details stated in the presentation:

- Vendor: `V-0412`
- API request ID: `req-5f61b0de8`
- Vendor change ID: `chg-8b9888c39b`
- Timestamp: `2026-09-03 01:44:30 UTC`
- Field: `bank_account`
- Approval reference in the supplied E19 case summary: blank

The app explains this as an investigation priority. A blank approval field **does not prove** that separate approval is absent elsewhere, and the available evidence does not establish fraud, attacker identity, vendor compromise or financial loss.

## Example dataset

On first launch, the local SQLite database is initialized and the bundled fixture is loaded if no evidence exists. The fixture contains 160 records:

- 71 E18-style API request records: 44 phone updates, 26 email updates and 1 bank-account update.
- 71 E19-style vendor-change records connected by request ID.
- The V-0412 bank-change anchor from the presentation's case summary.
- An E04-style credential case-summary fixture for `key-tb-07`.
- Ten synthetic E02-style support export records.
- Synthetic E01-style large-export, E05-style finance-path access and supporting context records.

The 70 phone/email pairs, generated row identifiers, export sizes/counts, finance-path details and supporting system records are synthetic examples. They are not original raw evidence values. The source evidence register reflects only what the presentation says about E01–E20; it does not recreate missing source files.

## Quick start

Requires **Python 3.10 or later**.

### Linux / Arch Linux / macOS

```bash
cd TraceCheck_Project
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
streamlit run app.py
```

Open **http://localhost:8501**. Keep the terminal open while using the application. Press `Ctrl+C` to stop it.

You can also run:

```bash
./start.sh
```

Or use the package command:

```bash
python -m tracecheck serve
```

### Windows PowerShell

```powershell
cd TraceCheck_Project
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
streamlit run app.py
```

Or double-click `start_windows.bat`.

## Application navigation

1. **Overview** — record counts, source count, exact request joins, findings and V-0412 case anchor.
2. **Problem & Evidence** — E04, E18, E19, the 71/71 relationship, update distribution and E01–E20 evidence register.
3. **Investigation Context** — legitimate alternatives and questions that remain unresolved.
4. **Workflow & Architecture** — six processing steps, four architecture layers and case data sources.
5. **Feature Progress & Stack** — five modules, actual implementation status and technology stack.
6. **Evidence Explorer** — search/filter records and inspect normalized fields and original payload.
7. **ProofPath Correlations** — search a request ID and inspect exact API-to-change joins and unmatched rows.
8. **ContextIQ** — business-context notes and export-related findings.
9. **ApprovalGuard** — sensitive financial changes and approval-reference review.
10. **ExplainAI** — finding explanations and the difference between a generic alert and an evidence-backed review.
11. **PolicyGuard** — credential inventory, broad permissions and finance-path access.
12. **Review Queue** — statuses, analyst notes and audit history.
13. **Investigation Timeline** — cross-source event plot and original/normalized timestamp fields.
14. **Validation Lab** — seven normal/review regression scenarios.
15. **Data Ingestion** — upload, preview, import, duplicate handling and import history.
16. **Reports & Exports** — downloadable evidence CSV, findings CSV and JSON report.
17. **Limitations & Roadmap** — explicit known limitations and future work.
18. **System Settings** — database path, rule heuristics, re-analysis and destructive sample reset.

## Import format

Accepted file extensions: `.csv`, `.json`, `.jsonl` and `.ndjson`.

Useful fields include `record_id`, `source_id`, `source_system`, `event_type`, `timestamp`, `request_id`, `vendor_id`, `credential_id`, `actor`, `action`, `ip_address`, `approval_ref`, `vendor_field`, `resource_path`, `record_count`, `size_bytes` and `schedule`.

Example CSV:

```csv
record_id,source_id,source_system,event_type,timestamp,request_id,vendor_id,vendor_field,approval_ref
api-001,E18,TallyBridge API,api_request,2026-09-03T01:44:30Z,req-001,V-1001,bank_account,
change-001,E19,Vendor change log,vendor_change,2026-09-03T01:44:31Z,req-001,V-1001,bank_account,
```

Use a timezone suffix (`Z` or an explicit offset) when known. Timezone-naive values are retained as original text and labelled unknown; TraceCheck does not assume UTC. Original source fields are retained in `payload_json`.

## Initial detection rules

| Rule | Initial trigger | Interpretation |
|---|---|---|
| `FINANCIAL_CHANGE_NO_APPROVAL` | Bank/account field change with no approval reference in that change record | Requires verification; does not prove approval absent elsewhere |
| `OVERPRIVILEGED_INTEGRATION_KEY` | Broad read/write or all-modules access with no recorded IP restriction and no token expiry | Credential-control gap; does not prove misuse |
| `SUPPORT_EXPORT_BURST` | Ten or more support export records without weekly/routine schedule label | Context review; count alone is not proof of data misuse |
| `LARGE_VENDOR_EXPORT` | At least 5,000 rows or 25 MiB | Illustrative heuristic; not an original E01 threshold |
| `FINANCE_PATH_INTEGRATION_ACCESS` | Integration/service identity accesses a finance-related resource path | Verify owner, scope and ticket; does not establish intent or download |
| `UNMATCHED_VENDOR_ACTIVITY` | Vendor-change request ID has no matching imported API request | Could indicate incomplete evidence ingestion, not malicious activity |

Thresholds are initial demonstration heuristics, not tuned enterprise policy. Calibrate them against authorized baseline data before operational use.

## Testing

```bash
pytest -q
```

The tests cover fixture counts and provenance, 71 exact joins, V-0412 evidence logic, timestamp handling, CSV/JSON/JSONL import parsing, duplicate handling, detection rules, validation scenarios and report/review persistence.

The seven validation scenarios are deterministic regression checks. They do not establish statistically valid precision, recall or accuracy on the original CRIMEATHON raw evidence archive.

## Project structure

```text
TraceCheck_Project/
├── app.py                         # Streamlit user interface and navigation
├── requirements.txt
├── README.md
├── .streamlit/config.toml         # Local theme and server settings
├── tracecheck/
│   ├── db.py                      # SQLite schema and database connections
│   ├── ingestion.py               # CSV / JSON / JSONL parsing and persistence
│   ├── normalize.py               # Field aliases and timestamp normalization
│   ├── correlation.py             # Exact request-ID joins
│   ├── rules.py                   # Deterministic findings and explanations
│   ├── service.py                 # Queries, review updates, audit and exports
│   ├── demo_data.py               # Sample data and provenance catalogue
│   └── validation.py              # Seven synthetic regression scenarios
├── data/
│   ├── demo_records.json
│   ├── evidence_catalog.json
│   └── sample_imports/
├── tests/
└── docs/
```

## Safety and deployment boundaries

- The default server binds to localhost and is intended for local competition evaluation.
- The application processes supplied fictional evidence, user-authorized files and synthetic fixtures only.
- It does not access real Harbor & Finch, LedgerOne, HelpDeskr, BlueVault, SSO, TallyBridge, Private Link or any external company system.
- It performs no scanning, attacking, autonomous blocking, containment or credential modification.
- The local MVP does not include multi-user authentication or role-based access. Do not expose it to a public/shared network as-is.
- Do not import real secrets, credentials or personal/financial data. Use authorized and sanitized records only.

## Honest implementation status

The application is a working local investigation MVP. It includes file ingestion, SQLite persistence, exact request correlation, initial deterministic rules, five module workspaces, an analyst review queue, timeline, validation lab and exports. It is not a production SIEM. It does not have live enterprise connectors, trained AI, independent accuracy benchmarks, production authentication or autonomous response.
