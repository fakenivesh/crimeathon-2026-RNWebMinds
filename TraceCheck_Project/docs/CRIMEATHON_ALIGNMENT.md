# CRIMEATHON Tier 2 presentation alignment

This document maps the ten-slide RN WebMinds Tier 2 concept to the Streamlit application.

| Slide | Presentation content | Application page / feature |
|---|---|---|
| 1 | TraceCheck identity, case and DEFENCE track | Sidebar identity and app header |
| 2 | Visibility gap; E04, E18, E19; 71/71; V-0412 | Problem & Evidence, Overview, ProofPath |
| 3 | Alternative explanations and unknowns | Investigation Context / ContextIQ |
| 4 | Collect, Normalize, Connect, Detect, Explain, Recommend | Workflow & Architecture and ingestion / detection / explanation / review workflow |
| 5 | Input, Process, Intelligence, Output layers | Workflow & Architecture |
| 6 | Python, Pandas, SQLite, Streamlit, Plotly, Pytest, GitHub | Feature Progress & Stack |
| 7 | Basic alert vs evidence-backed review | ExplainAI and ApprovalGuard |
| 8 | ProofPath, ContextIQ, ApprovalGuard, ExplainAI, PolicyGuard | Five module workspaces and Feature Progress & Stack |
| 9 | Normal and review scenarios; false alarm validation | Validation Lab |
| 10 | Limitations, roadmap and final message | Limitations & Roadmap |

## Verified versus illustrative information

The application uses the V-0412 request/change identifiers and event details shown in the presentation. It also represents the 71/71 correlation count with 70 synthetic contact-update pairs plus the one V-0412 case-summary anchor. The original raw E18 and E19 files were not supplied in the PowerPoint, so the app must not describe the synthetic rows as imported originals.

The E04 credential record, E02 support export rows, E01 export volume, E05 path detail and E03/E15/E20 example context rows are fixtures derived from high-level presentation statements; they are not reconstructed original raw records.

## Implemented locally

- Streamlit application UI.
- Local CSV/JSON/JSONL upload and validation.
- Normalization with original payload preservation and unknown-timezone labelling.
- SQLite evidence storage and duplicate protection.
- Exact request-ID correlation.
- Six deterministic investigation rules.
- Five named module workspaces.
- Evidence-backed rule explanations and human next-step recommendations.
- Analyst review status, notes and local audit records.
- Timeline chart, validation lab and CSV/JSON export.

## Not implemented / not claimed

- Live integration to any enterprise system named in the architecture.
- Production SIEM or streaming ingestion.
- Trained ExplainAI model or external AI calls.
- Automated prevention, containment or account modification.
- A statistically valid precision/recall benchmark on the original evidence archive.
- Multi-user authentication, role-based authorization or hardened shared deployment.

The 71/71 result is a correlation relationship count, not a detection accuracy result. A blank approval reference in E19 is a verification gap, not proof that separate approval was absent.
