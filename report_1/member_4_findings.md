# Member 4 Findings — Governance, Security, and External Evidence

**Case:** CR-26-047  
**Assigned evidence:** E09 risk register, E10 IT security policy v2.1, E11 internal audit report, E12 vendor notice, E16 vendor follow-up, E17 indicator list, E20 public records pack  
**Purpose:** Assess documented controls, prior findings, vendor claims, indicator support, and alternative explanations. E20 is a saved, unverified public-records pack; it is treated as a lead source, not authoritative attribution.

## Executive assessment

The governance record supports a substantial third-party integration control gap that was known before the August activity. E10 policy v2.1 requires high-risk third parties to use IP restrictions where supported, credentials to expire within 90 days, minimum scope, annual reviews, and monitoring for bulk exports and export deletion. E11's September 2025 audit rated missing integration expiry/IP controls, absent export monitoring, and stale vendor reviews as High findings, all still open at report date. E04 (Member 2) later shows TallyBridge's LedgerOne key with all-module read/write, HelpDeskr with admin scope, no IP restrictions or token lifetime, and June 2024 reviews; the documented policy requirements were not reflected in the register as of 2 September 2026. E09 separately records several related risks as open/overdue or accepted with overdue review.

The vendor's 21 August notice was vague and routed only to Accounts. The 28 August follow-up gives useful specifics but should not be treated as dispositive: it claims activity affected only support-ticket metadata, no finance/files, and no private-link systems; supplied logs reviewed by other members include bulk exports, finance-file reads, and a build host on the private link. However, the evidence also has important attribution limits: E20 says the `198.18.7.0/24` addresses are dynamic broadband/reseller allocations and can be reassigned, while the logs themselves do not identify the user of those addresses. The safest finding is a verified control weakness and multiple contradictory observations requiring reconciliation, not a settled claim about the actor or vendor environment.

## E09 — Risk register findings

The spreadsheet has two sheets: “Risk Register” and “Rating Key.” It was last exported 2 September 2026. Relevant rows:

| Risk | Status / rating | Review and note |
|---|---|---|
| R-018 Staff accounts not disabled after exit | Medium, Mitigate, Open | Next review due 5 Apr 2026; points to audit finding 3. |
| R-025 Customer data leak through support tickets | High, Mitigate, Open | Review overdue; training planned. |
| R-029 Misuse of storage access key issued to customer partner | Medium, Mitigate, Open | Rotation annually “not done”; next review due 30 Sep 2025. |
| R-031 Vendor connector compromise (TallyBridge) | Low, Accept, Accepted | Accepted at onboarding; next review due 30 Jun 2025 and overdue. |
| R-015 Phishing leading to payment fraud | High, Mitigate, Open | Dual approval on payment runs noted; next review due 18 Oct 2026. |

The rating key says review frequency is a guideline (High quarterly, Medium every six months, Low annually), and the register has multiple past-due reviews. The relevant integration risks were present in the register, but at least TallyBridge connector compromise was classified low/accepted despite policy E10 classifying any vendor with financial-system write access or customer-data read access as high risk. The register does not show documented closure evidence for the support-ticket or storage-key risks.

## E10 — Policy requirements and observed gaps

E10 policy TPS-POL-02 version 2.1 has been effective since 1 January 2025 and applies to third-party integrations handling financial or customer data. It requires:

- High risk for a vendor with financial-system write access or customer-data read access (section 1).
- Vendor IP restrictions where supported (2.1), expiry within 90 days and rotation (2.2), least privilege and written justification for `all modules`/`admin` scopes (2.3).
- Annual high-risk reviews that check assurance coverage of systems holding/protecting Harbor & Finch credentials (3.1).
- Alerts for bulk exports and integration-account export deletions (4.1).
- No credentials pasted into tickets/chat; secure submission link; report and rotate any key found in a ticket (5.1–5.2).
- Written CISO exception approval for no more than six months (6.1).
- Pre-2025 integrations to meet credential and monitoring requirements by 1 January 2026 (7.1).

E04, E07, E11, E13, E02, E05, and E15 observations from other member reports indicate apparent gaps against these requirements: broad persistent credentials; no IP restriction or lifetime; no recorded annual review; missing monitoring despite bulk exports/deletes; and a customer storage key discussed as pasted into a support ticket, with no evidence in assigned files of reporting/rotation. Any final policy noncompliance conclusion should be verified against exception records, control implementation evidence, and the complete key/ticket history. The policy says the CISO position has been vacant since September 2025, with the IT Security Administrator acting; no exception approval should be presumed from that fact.

## E11 — Prior audit and remediation status

Internal Audit IA-2025-09 (report date 12 September 2025; audit period March–August 2025) reviewed LedgerOne, HelpDeskr, BlueVault, and integrations. It records:

- Finding 2 (High, Open): 11/50 sampled tickets contained pasted credentials/keys; Support routinely requested configuration in tickets; training and secure-link tool still pending.
- Finding 3 (Medium, Open): departed accounts not always disabled promptly; HR/IT monthly reconciliation target 31 October 2025.
- Finding 4 (High, Open): 5/8 integration credentials lacked expiry; the same five had no IP restriction; rotation deferred while compatibility with TallyBridge was checked.
- Finding 5 (Medium, Open): two unused integration credentials remained active.
- Finding 6 (High, Open): no bulk-export or export-deletion alerting for integration accounts; monitoring use cases awaited SIEM procurement.
- Finding 7 (Medium, Open): vendor assessments not repeated annually; two high-risk vendors had no review since onboarding.

The report schedules a March 2026 follow-up but does not record its status. E10 policy became effective January 2025 and set a 1 January 2026 transition deadline for older integrations. The supplied evidence does not contain that follow-up, proof of remediation, accepted exceptions, or current monitoring configuration. E04's September 2026 state and E09 overdue dates suggest the gaps persisted, but should be verified with change tickets and current system configuration.

## E12 and E16 — Vendor notices

**E12 (21 August, 19:32 IST):** TallyBridge says unusual activity affected a limited subset of customer connections and credentials were being rotated as a precaution. It says there was no evidence customer data was accessed in a way affecting operations and no customer action was required. It was sent only to `accounts@`, not Security or IT.

**E16 (28 August, 18:10 IST):** The follow-up says unauthorized requests used a customer connection credential on 11–12 August, were limited to support-ticket metadata, did not access finance records or stored files, temporary exports were removed, and activity originated entirely outside TallyBridge with no internal/private-link systems involved. It says credentials were rotated 24 August, attaches E17, and says vendor contact email/phone sync would begin 1 September using the existing connection. It calls the matter closed.

The notices are not necessarily inconsistent with each other: E12 is preliminary and E16 is a later conclusion. But E16's narrow scope and “no private link” statements conflict with or are not resolved by other supplied evidence:

- E02 records `tb-sync-svc` searching credential-related terms and reading ticket TKT-48213, then creating/downloading ten HelpDeskr exports on 11–12 August from listed addresses; nine deletions succeeded and the last delete returned an error. This supports ticket metadata access and export activity, but does not identify export contents or operator.
- E01 records successful TallyBridge-key LedgerOne vendor exports/downloads on 12 August and reads/exports from other addresses; it also records 17–19 August vendor bank-detail and payment-export activity from `10.20.4.77` (Member 1). These events challenge the blanket narrow account if tied to the same incident, but temporal/IP attribution and whether the activity was unauthorized need confirmation.
- E05 records BlueVault finance files read by `key:bvk-7f3a` from `198.18.7.23`, `.24`, and `.77` on 14–16 August (Member 3). This is later than the vendor's stated 11–12 August incident window, concerns a different credential, and does not alone disprove the vendor's incident window; it does challenge any broader inference that there was no finance/file access in the overall case.
- E15 records the private-link host `tb-build-02` reaching LedgerOne, sandbox, and HelpDeskr through `tun-tb-01` on 9 July–19 August (Member 2). The 16 August E20 status entry calls this host re-provisioning with no customer impact expected; those public records do not establish whether the activity was related to the reported incident.
- E16 announces new contact-detail synchronization from 1 September. E18/E19 show `key-tb-07` making 71 contact/bank-detail vendor changes from 1–7 September, including one bank-account change. The contact changes may be consistent with the announced feature; the bank-account edit is outside the stated contact fields and needs explanation and authorization.

The vendor's credential rotation assertion needs an internal credential change record and evidence identifying exactly which credentials were rotated. E04's 2 September current-state entry lists TallyBridge credentials as active and last used 2 September, but that does not by itself prove rotation did or did not occur; the ID can persist across rotation. Request a dated credential/version history and incident scope/methodology.

## E17 — Indicator validation against supplied logs

E17 contains five vendor-provided indicators. Validation below is against the case files reviewed across team reports. “Observed” means a string or source value appears in a log; it does not validate vendor attribution or maliciousness.

| Indicator | Vendor claim | Supplied-log observation | Assessment |
|---|---|---|---|
| `198.18.7.41` | High-confidence unauthorized source, 11–12 Aug | Appears in E01 as `key-tb-07` source for export job 9931 (9,840 records), its download, and deletion; E02 records `tb-sync-svc` searches, a ticket read, and export cycles from this IP. | Strongly corroborated as a source of relevant successful activity; unauthorized status remains vendor claim and IP ownership/user is unproven. |
| `198.18.7.58` | High-confidence unauthorized source, 12 Aug | Appears in E01 for a 9,835-record vendor export/download and in E02 for integration export cycles. | Strongly corroborated as a source of relevant activity, with same attribution caveat. |
| `198.18.8.6` | Medium confidence, seen near unauthorized requests | Not found as an exact source in E01/E02/E03/E05/E15 reviewed. | Not independently corroborated in supplied logs. Confirm full evidence coverage and whether “near” means network adjacency or timestamp proximity. |
| `python-requests/2.31.0` | High-confidence scripted client | No exact user-agent match in E01; relevant E01 rows identify TallyBridge Sync/3.4.1 or 3.5.0. E02 has no user-agent field. | Not independently corroborated in assigned/reviewed records; absence is not disproof because sources may not log user-agent. |
| `key-tb-03` | Low-confidence legacy credential, retired by vendor | E04 lists `key-tb-03` active, last used 11 Jan 2025; E01 has no sampled activity found for it. | Credential exists in current-state register and appears inactive in logs, but “retired by vendor” is not verified; current internal status conflicts with that claim. Verify credential history/disablement. |

E20's address registration section cautions that `198.18.0.0/16` is dynamic residential/small-business broadband and addresses may be reassigned; `198.18.7.0/24` includes a reseller allocation. Thus exact indicator matches validate log-source coincidence, not a particular vendor employee, attacker, or vendor network. Do not automatically trust the vendor's confidence labels.

## E20 — Public records and alternative explanations

E20 was collected by Finance IT on 2 September 2026; its own cover says pages may have changed and nothing has been verified. Items useful as leads:

- **Public security page:** claims annual SOC 2, ISO 27001 certification since Feb 2025, credential encryption, MFA for production, isolated release pipeline, and subprocessors CloudNine, VaultWorks, and Gitly. E07's 2024 review said ISO certification was not yet complete and identified the credential-vault subprocessor as outside the SOC report scope. These claims could reflect improvements after 2024; request current certificates, report periods/scope, and subprocessor assurance.
- **Status history:** records a 16 August 18:00–21:00 UTC re-provisioning of `tb-build-02` with no expected customer impact; 10 July release 3.5.0 rollout; and 9 July sandbox maintenance. E15 records flows from `tb-build-02` on 9 July and 17–19 August. This gives plausible legitimate maintenance context for those particular flows, but does not prove authorization or explain every destination/request.
- **Release notes:** version 3.5.0 on 10 July moved nightly sync start to 01:30 UTC and changed the client user-agent to `TallyBridge-Sync/3.5.0`; 3.4.x was retired with that release. E13's 10 July chat message aligns with the start-time change. E01 later records 3.5.0 activity. The status/release notes provide a benign explanation for schedule/version changes, not for broad exports or finance-file reads.
- **Job advert:** a 12 June 2026 security-engineer advert lists build servers, source control, key management, and goals to institute access reviews, scan pipelines for secrets, and reduce long-lived credentials. This may indicate work was planned or underway, but it is not evidence that a vulnerability existed or was exploited.
- **Forum thread:** includes third-party reports of overnight export jobs and unfamiliar key-source IP activity. These are unverified user posts; they may add context but cannot substantiate this case's attribution.
- **Domains and address lookups:** `tallybridge-support.example` was registered 19 August with privacy-protected registrant and low-cost nameserver, whereas the vendor's main domains were registered earlier. This is a lead only; the saved pack does not show malicious content or control. Dynamic address registration materially limits attribution from `198.18.7.*` alone.

### Alternative explanations considered

1. **Authorized release or sync change:** The 10 July release explains earlier nightly runs and 3.5.0 user-agent changes; it does not explain an August 12 bulk export sequence or the later September bank-account change. Validate deployment tickets and feature specification.
2. **Legitimate maintenance/build-host activity:** E20 labels 9 July sandbox maintenance and 16 August build-host re-provisioning. This plausibly explains some `tb-build-02` flows in E15, but the actual application actions and production destinations require internal/vendor change records.
3. **Routine Support/Finance exports:** E13/E02 show weekly Support exports and an announced Finance vendor audit export on 22 July. These explain some large exports and deletions, but not automatically the TallyBridge principal's repeated August export cycles. Export object metadata and contents are needed.
4. **Announced vendor contact synchronization:** E16 and E20 release notes explain the 1–7 September contact email/phone updates under `key-tb-07`. They do not explain the single bank-account change in E19; seek change approvals, API feature scope, and vendor records.
5. **Dynamic/shared IP use:** E20 says `198.18.*` addresses can be reassigned. A match can be a residential/VPN/reseller host and cannot by itself identify a person or company. Preserve timestamped ISP/VPN assignment records if available.
6. **Benign integration operation or testing:** the integration owner may have intended reads/exports, and the build host may have been used for maintenance. This remains possible but is weakened by the broad access, stale reviews, missing restrictions, credential searches, and lack of documented alerts/approval. Obtain written authorizations and job tickets.

## Combined assessment for Tier 1 drafting

**Evidence-backed problem to consider:** Harbor & Finch did not demonstrate that third-party credentials and integrations were configured and monitored to its own policy standard. The strongest verified issue is an overbroad, long-lived, unrestricted integration posture combined with previously documented open audit findings and missing export monitoring. Supplied system logs also show credential-associated activity that is inconsistent with a simple “ticket metadata only/no finance or private link” account, although actor attribution and incident scope remain unresolved.

**What remains uncertain:** who controlled the source addresses and credentials; whether August exports and storage reads were authorized or connected to TallyBridge's reported activity; what the exports contained and where copies went; whether the vendor rotated the relevant credentials on 24 August; whether the Sep contact updates were the announced feature and why a bank account was changed; whether payments were affected; and whether open audit findings were remediated outside the supplied file set.

**Evidence that could change the conclusion:** complete credential rotation/revocation and scope history; approved IP lists and authoritative address assignment records; export job metadata/content and deletion/retention records; vendor incident root-cause evidence and affected-customer scope; change tickets and Finance approvals for vendor updates; payment settlement records; March 2026 audit follow-up and exception approvals; complete MSA and current vendor assurance/subprocessor documents.

## Evidence references

- **E09:** `Given/E09_risk_register_extract.xlsx` — Risk Register and Rating Key sheets, export 2 Sep 2026.
- **E10:** `Given/E10_it_security_policy_v2_1.pdf` — Third-Party and Integration Security Policy, v2.1.
- **E11:** `Given/E11_internal_audit_report_IA_2025_09.pdf` — audit report IA-2025-09.
- **E12:** `Given/E12_email_notice.pdf` — TallyBridge notice dated 21 Aug 2026.
- **E16:** `Given/E16_followup_email_notice.pdf` — TallyBridge follow-up dated 28 Aug 2026.
- **E17:** `Given/E17_indicator_list.csv` — five vendor-provided indicators.
- **E20:** `Given/E20_public_records_pack.pdf` — saved, unverified public information pack dated 2 Sep 2026.
