# TraceCheck live demonstration runbook

## Before the evaluation

1. Install dependencies and launch with `streamlit run app.py`.
2. Open the Overview page and confirm the sample dataset is loaded.
3. Confirm the 71 exact request joins are displayed.
4. Do not describe generated synthetic rows as original raw case evidence.
5. Keep the app running locally; no internet or external company connection is required after dependencies are installed.

## Suggested 5–7 minute walkthrough

### 1. Introduce the investigation (Overview — 30 seconds)

Explain that TraceCheck connects disconnected enterprise activity records and provides evidence-backed review guidance. Point out the local-only scope and synthetic dataset notice.

### 2. Show the evidence (Problem & Evidence — 60 seconds)

Show E04, E18 and E19. Explain 71 API requests and 71 vendor-change records, with 44 phone, 26 email and one bank-account update. State that 71/71 is an exact request-ID correlation result, not detection accuracy.

### 3. Investigate V-0412 (ProofPath + ApprovalGuard — 90 seconds)

Search `req-5f61b0de8`. Show API fixture `api-anchor-0412` and change `chg-8b9888c39b` for vendor `V-0412`. Point out that E19's approval reference is blank. Say this requires independent approval verification; it does not prove that no separate approval exists or that the event was fraudulent.

### 4. Explain business context (Investigation Context + ContextIQ — 60 seconds)

Explain that contact sync may account for the 70 phone/email changes, weekly support exports may be normal but ten additional cycles need checking, maintenance may explain build-host flows, and dynamic IPs do not establish identity.

### 5. Show the five modules (Feature Progress & Stack — 45 seconds)

Quickly cover ProofPath, ContextIQ, ApprovalGuard, ExplainAI and PolicyGuard. ExplainAI currently uses deterministic templates, not a trained model.

### 6. Demonstrate the review workflow (ExplainAI + Review Queue — 60 seconds)

Open the generated finding, show its linked source records and recommended next step. Add an analyst note and change its status to In Review. Explain that the action persists in SQLite and is recorded in the local audit history.

### 7. Validate and export (Validation Lab + Reports — 60 seconds)

Run the seven synthetic regression scenarios. State that all passing means the configured examples behave as expected, not that the application has production detection accuracy. Download a findings CSV or JSON report.

## Likely judge questions

**Does 71/71 mean 100% accuracy?**  
No. It is the exact request-ID relationship count between the represented E18 and E19 records. It is not precision, recall or detection accuracy.

**Was the bank change fraudulent?**  
The evidence does not establish that. E19 has a blank approval reference; separate approval may exist elsewhere. TraceCheck recommends verification with Finance and the vendor.

**Is ExplainAI a trained model?**  
No. The current implementation uses deterministic rule templates to explain findings and uncertainty.

**Does it connect to real LedgerOne / HelpDeskr / BlueVault?**  
No. The architecture names those case sources, but the competition application only processes supplied or authorized local files and synthetic fixtures.

**Can it automatically block the integration key?**  
No. It is a defensive investigation and review tool. Human reviewers decide what to do.

**Are the other 70 E18/E19 rows original evidence?**  
No. They are synthetic pairs used to exercise correlation and reproduce the 71/71 count shown in the team's presentation. The original raw E18/E19 files were not supplied in the PowerPoint.
