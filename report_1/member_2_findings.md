# Member 2 Findings — Identity, Integration, and Network

**Case:** CR-26-047  
**Assigned evidence:** E03 SSO sign-in log, E04 connected software register, E07 onboarding review, E08 contract excerpt, E14 staff roster, E15 private-link flow log  
**Scope note:** The observations below come from these files. Member 1 and Member 3 reports contain related API, support, and storage findings; cross-evidence links are identified as leads and should be confirmed against their source records and time zones.

## Executive finding

The most direct weakness is an over-permissive and stale third-party integration configuration. E04 shows the TallyBridge LedgerOne credential `key-tb-07` active with `read:write all-modules`, no IP restriction, no token lifetime, and a last review on 12 June 2024. The TallyBridge HelpDeskr service credential `tb-sync-svc` is active with `admin` scope, also without IP restrictions or token lifetime, and with the same old review date. A legacy LedgerOne key `key-tb-03` remains marked active despite last use in January 2025. E07 says an annual review was due June 2025, with no record of completion in that file; the register says the current review dates remain in June 2024. E08 assigns Harbor & Finch responsibility for configuring restrictions offered by its own systems.

E15 corroborates sustained private-link access from six sync hosts into both LedgerOne and HelpDeskr, plus a build host reaching production systems. E03 shows most human sign-ins used MFA and succeeded, so the available identity data does not support a broad claim of account compromise. It does show three failed attempts against IT Security Administrator `a.kapoor` from `198.18.7.77` on 15 August (two bad-password failures followed by an MFA failure); no successful login from that IP appears in this targeted sequence. E14 confirms `a.kapoor` is active and lists Rohan Menon as terminated 30 June, despite the partial chat's report that his kiosk login still worked.

## E04 — Connected software register

The register was generated 2 September 2026 and explicitly says it is a current-state export with no history. Relevant entries:

| Integration / credential | Scope and status | Restrictions and review |
|---|---|---|
| TallyBridge-LedgerOne / `key-tb-07` | `read:write all-modules`, active, last used 2 Sep 2026 | No IP restriction; no token lifetime; last review 12 Jun 2024 |
| TallyBridge-HelpDeskr / `tb-sync-svc` | `admin`, active, last used 2 Sep 2026 | No IP restriction; no token lifetime; last review 12 Jun 2024 |
| TallyBridge-LedgerOne (legacy) / `key-tb-03` | `read:all`, active, last used 11 Jan 2025 | No IP restriction; no token lifetime; last review 12 Jun 2024 |
| Nightly Backup / `key-bk-02` | `read:all`, active | IP restriction on; 365-day lifetime; reviewed 4 Nov 2025 |
| Customer Portal / `key-app-11` | invoices and shipments read/write, active | IP restriction on; 180-day lifetime; reviewed 15 Jan 2026 |
| Payments Console / `key-app-12` | payments read/write, active; last used 2 Mar 2025 | No IP restriction or lifetime; last review 1 Feb 2024 |
| Reporting / `key-rpt-03` | invoices and shipments read, active | IP restriction on; 365-day lifetime; reviewed 15 Jan 2026 |
| Customer Document Portal / `bvk-7f3a` | BlueVault `read:all-folders`, active; last used 2 Sep 2026 | No IP restriction or lifetime; last review 18 Feb 2025 |

The internal restricted keys demonstrate that restrictions and limited scope/lifetimes are available and used in this environment. The TallyBridge settings depart from that baseline. The separate customer document portal credential is also broad for a customer/POD use case and should be checked against Member 3's BlueVault observations.

## E07 and E08 — Onboarding and contract comparison

E07 records a low-risk approval on 5 June 2024 for invoice/ticket sync with requested LedgerOne access covering invoices, vendors, and payments and HelpDeskr tickets. The file includes a SOC 2 Type 2 report whose scope excludes corporate IT, source code management, and the vendor's subprocessor-operated credential vault; the penetration-test summary was available but not requested. The questionnaire answers were accepted without follow-up. Reviewer notes say Security sign-off and CISO review were not recorded. The annual review was due June 2025, but the file has no record of completion.

E04's current `all-modules` LedgerOne scope and HelpDeskr `admin` scope exceed the narrower business description in E07. The onboarding file does request vendor/payment access, so the presence of those general areas is not itself proof of scope creep; however, `all-modules` grants no module-level limit and cannot be reconciled with least privilege based on this file alone. The register's review dates also indicate overdue review.

E08 clauses 5.1 and 5.3 say the vendor stores customer-provided credentials encrypted and the customer configures available restrictions, expiry, and scope limits. The lack of IP restrictions and token lifetimes therefore maps directly to customer-side configuration responsibilities under the supplied excerpt. Clause 7.2 requires notice of a confirmed incident affecting customer data without undue delay; clause 9 grants no technical/on-site audit right; clause 11.4 permits subprocessors without prior notice if protections are no less protective. These clauses make the missing assurance follow-up and subprocessor details important governance gaps. The excerpt is incomplete, so conclusions about the whole agreement should wait for full contract/legal review.

## E15 — Network/private-link flow analysis

E15 contains 9,790 flows from 3 June through 31 August 2026, all marked `allowed`:

- 8,640 monitoring flows from `tb-mon-01` / `10.20.4.10` to `TunnelGateway` through `tun-tb-01`; these are small 64-byte in/out heartbeat-like records.
- 1,080 sync flows from six hosts (`tb-sync-01` through `tb-sync-06`, IPs `10.20.4.11`–`.16`) through `tun-tb-01`: 540 to LedgerOne and 540 to HelpDeskr, all on port 443. Each host has 90 flows to each system spanning 90 dates from 3 June through 31 August.
- 70 flows from `tb-build-02` / `10.20.4.77` through the same tunnel: 55 to LedgerOne, 10 to LedgerOne-sandbox, and 5 to HelpDeskr, all on port 443. The records span 9 July to 19 August and are all allowed. The flow log does not label the LedgerOne flows as production or test, so their purpose must be confirmed.

This is consistent with a persistent private integration path and supports the need for source/host restrictions and environment separation. It is not by itself evidence of exfiltration: flow records show system, port, byte counts, and result, but not request content. There are no denied flows in this extract, so it cannot show attempted policy blocks.

## E03 — SSO sign-ins and identity checks

E03 records 26,893 events: 25,510 successes and 1,383 failures. Successful authentication was predominantly `password+totp` or passkey; 25,508 successes record MFA as passed. The `svc-reporting` account has 312 failed password attempts from `172.16.9.30` and no success in this extract; this should be treated as a separate service-account hygiene question, not mixed into the TallyBridge finding.

For `a.kapoor`, the roster identifies Aditi Kapoor as active IT Security Administrator. Three consecutive failures on 15 August from `198.18.7.77` occurred at 16:20, 16:22, and 16:24 UTC: two bad-password failures followed by an MFA failure. The failure sequence is consistent with a rejected sign-in attempt; the log shows no successful session for that sequence. Other `a.kapoor` successes in the period show normal-looking Chennai logins with passkey or password+TOTP. The IP overlap with BlueVault source `198.18.7.77` on 15 August is notable for cross-team triage but does not establish common operator or activity: the SSO events failed, E05 is a key principal rather than an employee session, and event timestamps/systems differ.

The chat (E13, owned by Member 3) mentions an old warehouse kiosk login for departed employee Rohan Menon. E14 shows `r.menon` terminated on 30 June 2026, status still displayed as `active`, role Accounts Payable Clerk. This is a roster status inconsistency and the reported kiosk access warrants validation. E03's fields do not show a targeted successful login for `r.menon` in the subset reviewed; the team should search the complete SSO log by that username and obtain endpoint/kiosk access records before drawing a conclusion.

The roster lists `c.lawson` as an active network contractor. E13 says he was working remotely in Bengaluru in mid-July; E03 shows successful Bengaluru/Mumbai logins for that account. Those records are compatible with the stated remote-work context and should not be treated as suspicious absent contrary evidence.

## Correlation with other team evidence (leads)

- Member 1's E01/E18 analysis identifies `key-tb-07` and TallyBridge user-agent activity, including successful API calls from `10.20.4.77`; E04 identifies that address's labeled host in E15 as `tb-build-02`. This is a strong infrastructure lead, not proof of who operated the host or whether the activity was authorized.
- Member 3's E02/E05 analysis describes integration activity and BlueVault key use from `198.18.7.*` IPs. E15's listed private-link sources are internal `10.20.4.*`, while E03 uses `198.18.*` sources for some SSO events. The network extract does not explain public source addresses or prove that they belong to TallyBridge; correlate with E17 indicators and provider/VPN records.
- Compare E15 flows against API request times and bytes carefully. E15 is UTC; E03 is ISO UTC; E02/E13 local time. Convert all timestamps explicitly and avoid attributing matching IP ranges alone to a shared actor.

## Chronology and governance status

| Date | Evidence | Event |
|---|---|---|
| 5 Jun 2024 | E07 | TallyBridge approved low risk; requested invoice/vendor/payment and ticket sync; annual review set for June 2025. |
| 10 Jun 2024 | E08 | Services agreement effective; customer responsible for available access limits/expiry/scope controls under clause 5.3. |
| 12 Jun 2024 | E04 | Current TallyBridge credential review dates; both credentials later remain active without IP restriction or lifetime. |
| 9 Jul–19 Aug 2026 | E15 | Build host `tb-build-02` reaches LedgerOne, sandbox, and HelpDeskr through private link. |
| 15 Aug 2026 16:20–16:24 UTC | E03 | Three failed `a.kapoor` sign-ins from `198.18.7.77`, last fails MFA. |
| 2 Sep 2026 | E04 | Register snapshot still shows TallyBridge credentials active and last reviewed June 2024; legacy key also active though last used January 2025. |

## Conclusions and limits

**Supported:** TallyBridge credentials are materially broad, lack IP restrictions and expiry in the 2 September register, and have stale recorded review dates; the expected annual vendor review is not documented in E07; the private link routinely connects multiple sync hosts to both production systems and permits build-host flows; and contract excerpts place restriction configuration responsibility on Harbor & Finch. The SSO data mostly shows MFA success and does not independently establish human account compromise.

**Not established:** whether TallyBridge's public IPs are vendor-controlled or approved; whether `tb-build-02` flows carried data or represented authorized maintenance; the precise permissions enforced at each application endpoint; whether the keys were compromised; whether the June 2025 review occurred outside the supplied file; or whether any event caused data loss/payment diversion. E04 has no history, E07 is a single due-diligence file, E08 is an excerpt, and E15 lacks payload details.

## Recommended follow-up

1. Obtain credential history and current effective scopes, owners, rotation/expiry settings, approved IPs, and authorization records for `key-tb-07`, `tb-sync-svc`, `key-tb-03`, `key-app-12`, and `bvk-7f3a`.
2. Reconcile TallyBridge requested business functions to actual per-endpoint permissions; disable unused legacy credentials after confirming business need.
3. Confirm whether annual review, vendor security sign-off, penetration-test review, SOC scope/carve-out review, and subprocessor list were obtained elsewhere.
4. Identify owners and purpose for `tb-build-02` production-system flows and validate segmentation between build, sandbox, and production.
5. Resolve IP ownership/allowlisting for the `198.18.7.*` sources using authoritative network, VPN, and vendor records.
6. Investigate the 15 August admin sign-in failures and the terminated-user kiosk report; verify MFA, account disablement, and device session state.
7. Use the complete register/change history and full contract, since the supplied register is current-state only and E08 is partial.

## Evidence references

- **E03:** `Given/E03_sso_signin_log.csv` — 26,893 sign-in events.
- **E04:** `Given/E04_connected_software_register.json` — eight current integration entries; no history retained.
- **E07:** `Given/E07_onboarding_review_file.pdf` — TallyBridge due diligence and reviewer/renewal notes.
- **E08:** `Given/E08_contract_excerpt.pdf` — selected MSA clauses only.
- **E14:** `Given/E14_staff_roster.csv` — 420 staff records.
- **E15:** `Given/E15_network_link_flow_log.csv` — 9,790 private-link flow records, UTC.
