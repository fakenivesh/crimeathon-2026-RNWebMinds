# CRIMEATHON '26 — RN WebMinds
## Case CR-26-047 | Tier 1–3 Investigation and Defense Project Guide

**Team:** RN WebMinds  
**Selected competition track:** DEFENCE  
**Organization investigated:** Harbor & Finch Freight Pvt. Ltd. (fictional)  
**Event:** CRIMEATHON '26, 19–20 November 2026  
**Case period:** 1 June–7 September 2026  
**Team size:** 4 members

> **Purpose of this README**  
> This document brings together the case background, all four members' evidence findings, the cross-system analysis, the team's conclusion, the proposed defense solution (TraceCheck), team responsibilities, testing plan and competition submission requirements. It is written so that a new team member can understand the case without having to reconstruct the investigation from separate reports.

---

# 1. Quick Summary

Harbor & Finch is a Chennai-based logistics company. It uses several internal systems to manage finance, customer support, file storage and staff access. It also relies on TallyBridge Connect, an external software integration that exchanges data between LedgerOne (finance) and HelpDeskr (customer support).

Our investigation found that important third-party credentials had broad permissions and lacked documented restrictions. The logs also show large data exports, searches for credential-related terms, finance-file access through a BlueVault key, and 71 API-linked vendor changes. One of those changes modified a vendor's bank-account details without an approval reference in the vendor change log.

The evidence establishes serious access-control, monitoring and governance weaknesses. It does **not**, by itself, prove who controlled the relevant credentials, that a cyberattack occurred, that the bank-account change was fraudulent, or that money was lost.

**Our selected problem:** Harbor & Finch cannot reliably correlate and assess sensitive actions performed through trusted third-party integrations across its separate systems.

**Our selected solution:** **TraceCheck** — a proposed defense tool that compares activity across systems, identifies unusual data exports, financial changes and possible security issues, and explains each alert using its supporting records.

**Our selected track is DEFENCE.** This replaces any earlier Offense-track planning in older notes or drafts. The team must submit and build for Defense.

---

# 2. The Case in Plain Language

## 2.1 What is Harbor & Finch?

Harbor & Finch Freight Pvt. Ltd. is a fictional logistics company founded in Chennai in 2009. It has about 420 employees, serves approximately 1,400 business customers and operates warehouses in Chennai, Coimbatore and Madurai.

It pays approximately 300 hauliers, fuel suppliers and packaging vendors twice a month, on the 8th and 23rd. Their payment instructions are stored in the finance system. This makes accurate vendor records especially important: a change to a vendor's bank details can affect where a payment is sent.

## 2.2 Main systems

| System | What it does | Why it matters to this case |
|---|---|---|
| **LedgerOne** | Finance system containing invoices, vendor records, payment instructions and payments | The key system for the vendor exports and bank-account change |
| **HelpDeskr** | Customer support ticket system containing conversations, attachments and pasted configuration details | The integration performed ticket searches, reads and export jobs; a storage key was reportedly pasted into a ticket |
| **BlueVault** | Shared file storage containing customer documents, finance statements and operations files | A BlueVault key later accessed finance-related files |
| **SSO** | Staff single sign-on and authentication records | Helps distinguish human staff sign-ins from software credentials |
| **TallyBridge Connect** | External integration synchronizing data between LedgerOne and HelpDeskr | Its permissions and activity are central to the investigation |
| **Private link** | Network connection between Harbor & Finch and the outside company | Provides network-flow context, but does not show the contents of traffic |

Other relevant facts:

- Several systems exchange data automatically overnight; no employee sign-in is necessarily involved.
- TallyBridge has been in place since June 2024.
- The CISO position has been vacant since September 2025; the IT Security Administrator is acting as security owner.
- Harbor & Finch has no central security monitoring system and no staff-laptop logs in the supplied case description.
- Different systems use different clocks and identity labels. Records must be correlated carefully.

## 2.3 Normal business activity to remember

Not every unusual-looking event is malicious. The case describes these normal activities:

- TallyBridge, backups and reporting tools run overnight; exact times can vary.
- Support exports ticket data every Tuesday for a weekly service review.
- Vendor payments are prepared before the 8th and 23rd of each month.
- Finance may perform vendor audits and month-end vendor-list cleanups, sometimes involving bulk exports and approved changes.
- The network contractor may sign in from different cities while travelling.

TraceCheck must distinguish these legitimate patterns from activity that needs investigation.

---

# 3. Our Selected Problem and Defense Approach

## 3.1 Problem statement

Harbor & Finch cannot reliably detect, correlate and independently verify sensitive activities performed through trusted third-party integrations. Its separate systems record API requests, ticket actions, file access, network flows and vendor changes, but the records are not routinely reviewed together. Broad integration permissions and previously identified monitoring gaps increase the risk that unusual or insufficiently approved activity will not be recognized promptly.

## 3.2 Why we selected this problem

This problem is supported by multiple independent evidence items:

- **E04:** Broad TallyBridge permissions and missing recorded IP restrictions and token lifetime.
- **E10 and E11:** Company policy requirements and previous audit findings about integration controls and export monitoring.
- **E01:** Large LedgerOne vendor exports and sensitive financial API activity.
- **E02:** HelpDeskr credential-related searches and repeated integration export jobs.
- **E05:** A BlueVault key successfully accessed finance-related files.
- **E18 and E19:** 71 API vendor changes linked by exact request IDs, including one bank-account change without a recorded approval reference.
- **E12, E16 and E20:** Vendor notices and public records that need to be compared with actual system logs and normal maintenance explanations.

## 3.3 Selected approach: DEFENCE

We are choosing Defense because the central challenge is to detect, explain and help control sensitive activity that is spread across separate systems. We are not trying to reproduce an attack. We are building a solution that identifies suspicious sequences, connects them to evidence and helps an investigator decide what should be reviewed or contained.

---

# 4. Evidence Catalogue: What Each File Contains and What We Looked For

The case file's Appendix D describes the structure of the 20 evidence items. The following sections combine that catalogue with the four members' actual findings. “What to check” describes the investigative purpose; “finding” summarizes what the member reports observed.

## E01 — LedgerOne API Access Log

**Contents:** 36,183 API request records, 3 June–31 August 2026. Fields include UTC timestamp, request ID, API key ID, caller IP, user agent, endpoint, method, records returned and status.

**What to check:** Which keys called which endpoints; the size and timing of exports; unusual source addresses; successful and failed operations; and links to E19 through request IDs.

**Finding:** `key-tb-07` made 1,876 requests, mostly from the private-link synchronization hosts. On 12 August it created and downloaded two large vendor exports from `198.18.7.41` and `198.18.7.58`, containing 9,840 and 9,835 records. On 17–19 August it repeatedly accessed vendor bank-detail endpoints. On 18 August it exported 4,210 payment records. The log records successful requests, but does not establish who controlled the source or what happened to downloaded copies.

**Limitation:** Older records had been purged; times are UTC.

## E02 — HelpDeskr Audit Log

**Contents:** 25,390 audit events, 3 June–31 August. Fields include local timestamp, event ID, actor, actor type, action, object ID, source IP, result and details.

**What to check:** Ticket searches and reads, integration activity, export creation/download/deletion, ticket access and whether activity matches normal weekly Support work.

**Finding:** `tb-sync-svc` appears in 1,402 events. On 11–12 August it searched terms such as `password`, `api_key`, `secret`, `token`, `bearer`, `private key`, `bluevault` and `bvk-`; it read ticket TKT-48213; and it performed ten export-create/download cycles. Nine deletion events succeeded; the tenth returned an error. These events were separate from the regular weekly exports performed by a Support employee.

**Limitation:** Tenant-local timestamps. Confirm the timezone before comparing with UTC logs.

## E03 — Single Sign-On Log

**Contents:** 26,893 sign-in events, 1 June–31 August. Fields include UTC timestamp, user, source IP, city, authentication method, MFA result, device ID, result and failure reason.

**What to check:** Successful and failed human sign-ins, MFA, unusual locations, staff identities and former-employee access.

**Finding:** 25,510 events succeeded and 1,383 failed; the successful human sign-ins were predominantly protected by MFA. Three consecutive failed sign-in attempts against IT Security Administrator `a.kapoor` occurred on 15 August from `198.18.7.77`; the sequence ended in an MFA failure and did not show a successful session. The roster and chat also raise a separate question about former employee Rohan Menon's kiosk access, but the reviewed SSO evidence does not establish a successful login by him.

**Limitation:** Device field blank before 20 June. The failed sequence is not proof of account compromise.

## E04 — Connected Software Register

**Contents:** Eight current integration entries, including integration name, credential ID, connected system, vendor, permission scope, owner, creation date, last review, IP restriction, token lifetime, last used and status.

**What to check:** Whether access is limited to the required system and actions; whether ownership and review dates are current; whether IP restrictions and credential lifetimes are configured; and whether old unused credentials remain active.

**Finding:** TallyBridge LedgerOne key `key-tb-07` was active with `read:write all-modules`, no IP restriction and no token lifetime; last review was 12 June 2024. TallyBridge HelpDeskr credential `tb-sync-svc` was active with `admin` scope and the same missing recorded restrictions and review date. Legacy key `key-tb-03` was still marked active despite last use on 11 January 2025. The register also shows other credentials with configured restrictions, indicating that such controls are available in the environment.

**Limitation:** Current-state export only; no historical change records.

## E05 — BlueVault Access Log

**Contents:** 7,914 file-access events, 3 June–31 August. Fields include epoch timestamp, event ID, principal, source IP, action, path, bytes and result.

**What to check:** Which keys and users accessed which folders; whether activity matched the documented purpose; data transferred; and whether sensitive finance files were accessed from unusual sources.

**Finding:** Principal `key:bvk-7f3a` performed 1,124 successful events. Earlier activity mostly read customer proof-of-delivery documents from `172.16.9.40`. On 14–16 August the same key listed and read `/finance`, `/finance/bank-instructions` and `/finance/statements`, including vendor bank details, payment templates and monthly statements, from `198.18.7.23`, `.24` and `.77`, plus some events with blank source IP.

**Limitation:** BlueVault clock is unsynchronized; some source IP values are missing. A successful read confirms logged access/transfer, not subsequent use of a copy.

## E06 — Billing Alert and Invoice

**Contents:** Alert email, internal forward and invoice extract.

**What to check:** The number of HelpDeskr export jobs, allowance, charges and whether billing aligns with audit events.

**Finding:** The notice reports 13 bulk-export jobs against an allowance of five. The invoice extract records 14 jobs used, nine above allowance, with ₹22,500 before GST in excess charges. July had four jobs and no overage. The alert and invoice counts differ by one; do not describe them as identical.

**Limitation:** Billing confirms export-job charges, not the contents of each export or that these were LedgerOne exports.

## E07 — Onboarding Review File

**Contents:** June 2024 third-party review, questions, answers and notes.

**What to check:** Security due diligence, requested access, assurance-report scope, reviewer sign-offs and annual review.

**Finding:** TallyBridge was approved as low risk on 5 June 2024 for invoice/vendor/payment and ticket synchronization. The SOC 2 report excluded parts of the vendor's corporate IT, source-code management and credential-vault environment. A penetration-test summary was available but not requested. Reviewer notes did not record Security sign-off or CISO review. An annual review was due in June 2025; completion is not documented in this file.

**Limitation:** Some answers were self-reported by the provider; one file cannot prove that no separate review took place.

## E08 — Contract Excerpt

**Contents:** Selected clauses from the June 2024 agreement.

**What to check:** Who is responsible for access restrictions, credential controls, incident notification, audits and subprocessors.

**Finding:** The excerpt says Harbor & Finch is responsible for configuring available restrictions, expiry and scope limits. Other clauses address encryption, incident notification and subprocessors. It does not provide a technical/on-site audit right in the supplied excerpt.

**Limitation:** Selected clauses only, not the full contract. Legal conclusions require full agreement review.

## E09 — Risk Register Extract

**Contents:** Spreadsheet with “Risk Register” and “Rating Key” sheets; exported 2 September 2026.

**What to check:** Relevant open, accepted or overdue risks, owners, review dates and mitigation actions.

**Finding:** Relevant entries include R-018 (staff accounts not disabled after exit, open), R-025 (customer data leakage through support tickets, open), R-029 (customer-partner storage key rotation, not done/overdue), R-031 (TallyBridge connector compromise, accepted as low with review overdue) and R-015 (phishing/payment fraud risk, high). The TallyBridge low/accepted classification appears difficult to reconcile with E10's high-risk classification for vendors with financial write access or customer-data read access.

**Limitation:** Some entries were not recently reviewed. The register is not proof that every control was or was not operating.

## E10 — IT Security Policy v2.1

**Contents:** Official Third-Party and Integration Security Policy, effective 1 January 2025.

**What to check:** Minimum scope, IP restrictions, credential expiry and rotation, annual review, export monitoring, safe handling of keys and approved exceptions.

**Finding:** The policy requires least privilege; IP restrictions where supported; credentials to expire within 90 days and be rotated; annual high-risk reviews; alerts for bulk exports and export deletions; no keys pasted into tickets/chat; and written CISO exception approval for limited periods. Older integrations were required to meet credential and monitoring requirements by 1 January 2026.

**Limitation:** Policy states what should happen; it does not prove implementation. Check exception records and actual configurations.

## E11 — Internal Audit Report

**Contents:** September 2025 internal audit report IA-2025-09, with a findings table.

**What to check:** Prior weaknesses, severity, open/closed status, owners and follow-up evidence.

**Finding:** The audit recorded open findings for credentials pasted into support tickets, delayed employee offboarding, integration credentials without expiry and IP restrictions, unused active credentials, missing bulk-export/export-deletion alerts, and overdue vendor reviews. A March 2026 follow-up was scheduled, but the supplied evidence does not include its outcome.

**Limitation:** Status is as of the report date. Obtain the follow-up and remediation proof before claiming the findings definitely remained open in September 2026.

## E12 — External Email Notice

**Contents:** TallyBridge notice dated 21 August 2026.

**What to check:** What the provider said happened, when it happened, the scope, affected credentials, actions taken and who received the notice.

**Finding:** The notice says unusual activity affected a limited subset of customer connections and credentials were being rotated as a precaution. It was sent to Accounts, not directly to Security or IT.

**Limitation:** External, unverified statement.

## E13 — Support Team Chat Export

**Contents:** 16 selected messages, June–August 2026, with timestamp, channel, author and text.

**What to check:** Staff awareness, ticket-key handling, export concerns, software updates, business explanations and reported account issues.

**Finding:** On 25 June, staff discussed a customer sharing key `bvk-7f3a` in ticket TKT-48213 and said the ticket would be tidied later. On 10 July, staff mentioned a TallyBridge update and earlier nightly run. On 22 July, Finance announced a vendor audit export. On 12 August, staff discussed many integration export jobs and a stuck deletion. On 13 August, a former employee kiosk-login concern was raised.

**Limitation:** Partial export; direct messages and edited/deleted messages are excluded. Timestamp timezone is described only as local.

## E14 — Staff Roster

**Contents:** Approximately 420 employee records with username, name, department, role, status, manager and employment dates.

**What to check:** Whether identities in logs belong to current staff, former staff, contractors or service accounts.

**Finding:** Rohan Menon is recorded as terminated on 30 June 2026, but the roster status still shows active. This supports checking the reported kiosk-login issue, but does not by itself prove that he accessed the system after leaving. Network contractor Colin Lawson's travel context is consistent with some city changes in his sign-ins.

**Limitation:** Manually maintained roster with known errors.

## E15 — Private-Link Flow Log

**Contents:** 9,790 network flow records, 3 June–31 August, with UTC timestamp, flow ID, source IP/label, destination system/port, bytes in/out, tunnel ID and result.

**What to check:** Which hosts reached which systems, whether flows were allowed, data volumes, build-host access and correlation with API times.

**Finding:** 8,640 small monitoring flows, 1,080 synchronization flows from six hosts to LedgerOne and HelpDeskr, and 70 build-host flows from `tb-build-02` to LedgerOne, sandbox and HelpDeskr. All entries in this extract are marked allowed. The build host's purpose and whether LedgerOne destinations were production or test require confirmation.

**Limitation:** Flow metadata does not show application payload or request content. Host labels were supplied by the external company and are unverified.

## E16 — External Follow-up Email

**Contents:** TallyBridge follow-up dated 28 August 2026.

**What to check:** How the provider refined its incident explanation, stated time window, data categories, credential rotation and new integration features.

**Finding:** The provider says unauthorized requests used a customer connection credential on 11–12 August, were limited to support-ticket metadata, did not access finance records or stored files, and that temporary exports were removed. It says credentials were rotated on 24 August and contact email/phone synchronization would begin on 1 September. The claim that no finance/file access occurred needs comparison with E01, E05 and E18/E19.

**Limitation:** External, unverified statement; obtain the provider's incident method, scope and credential history.

## E17 — Indicator List

**Contents:** Five vendor-provided indicators with type, first/last seen, confidence and vendor note.

**What to check:** Whether indicators appear in independent system logs and whether their dates and meanings match.

**Finding:** `198.18.7.41` and `198.18.7.58` appear in relevant E01/E02 activity. `198.18.8.6` was not found as an exact source in the reviewed logs. `python-requests/2.31.0` was not an exact user-agent match in the reviewed LedgerOne records. `key-tb-03` is still marked active in E04 despite the vendor's “retired” claim being unverified.

**Limitation:** Prepared by the external company. E20 says the `198.18.0.0/16` space includes dynamic broadband/reseller allocations and addresses may be reassigned. An indicator match is not proof of a person or attacker.

## E18 — Continued LedgerOne API Log

**Contents:** 2,891 API records, 1–7 September, same fields as E01.

**What to check:** Continued use of `key-tb-07`, vendor contact/bank endpoints, API request IDs and sequence of reads and edits.

**Finding:** 215 requests use `key-tb-07`; 71 API vendor changes are matched to E19 by exact request ID. The credential read V-0412 vendor/bank details and scheduled payments shortly before the 3 September bank-account update.

**Limitation:** API records show the credential and operation, not the human operator or business authorization.

## E19 — Vendor Record Change Log

**Contents:** 367 vendor record changes, 3 June–7 September, with UTC timestamp, change ID, vendor ID/name, field, old/new value, changed-by, channel, approval reference, source IP and request ID.

**What to check:** Sensitive field modifications, approval references, human vs API changes, request-ID matches and whether a change was part of an approved import or synchronization.

**Finding:** 284 changes were through the UI, 12 through import and 71 through the API. All 71 API changes match E18 requests and are attributed to `key-tb-07`; all have blank approval references. They comprise 44 phone changes, 26 email changes and one bank-account change. The bank-account change for V-0412 occurred on 3 September at 01:44:30 UTC; the masked account changed from `****4417` to `****9083`, with no approval reference in this record. Some human UI bank changes have approval references, and a July import had reference `BULK-0731`.

**Limitation:** A blank reference in the log is not absolute proof that no approval exists elsewhere. Payment records and Finance approvals must be checked.

## E20 — Public Records Pack

**Contents:** Seven categories of saved public information: security page, service status history, release notes, job advertisement, forum thread, domain records and address registration lookups.

**What to check:** Vendor security claims and assurance scope; service maintenance/release timing; build-host context; and whether address records support reliable attribution.

**Finding:** The status history describes build-host re-provisioning and maintenance; release notes describe version 3.5.0 and a change to the nightly sync start time; the security page makes claims about certifications and controls; the job advert describes security-engineering work; the forum contains unverified user posts; and address records warn that some IP ranges are dynamic/reassigned.

**Limitation:** Saved public material is unverified and may have changed. Treat it as context or a lead, not authoritative proof.

---

# 5. Findings by Team Member

## Member 1 — Finance and API Investigation

**Assigned evidence:** E01, E06, E18, E19.

**Main contribution:** Established the financial API activity and the matching vendor changes.

Key findings:

1. `key-tb-07` was responsible for 1,876 requests in E01, most from normal private-link synchronization hosts.
2. On 12 August, it downloaded two vendor exports containing 9,840 and 9,835 records from `198.18.7.41` and `.58`.
3. On 17–19 August, it accessed vendor bank details repeatedly; on 18 August it exported 4,210 payment records.
4. E18 records 2,891 requests from 1–7 September, including 71 API vendor-change requests.
5. Every one of those 71 API changes matches an E18 request ID in E19.
6. The changes include 44 phone updates, 26 email updates and one bank-account change.
7. The highest-priority record is change `chg-8b9888c39b` for V-0412 on 3 September at 01:44:30 UTC. It changed the masked bank account from `****4417` to `****9083`, through `key-tb-07`, source `10.20.4.77`, with a blank approval reference. The matching API request was `req-5f61b0de8`.

**Member 1's conclusion:** A sensitive bank-detail change occurred through the integration and has no approval reference in the supplied change record. Its authorization and payment impact remain unknown.

## Member 2 — Identity, Integration and Network Investigation

**Assigned evidence:** E03, E04, E07, E08, E14, E15.

**Main contribution:** Established the integration configuration weaknesses and network/identity context.

Key findings:

1. `key-tb-07` had `read:write all-modules` scope, no recorded IP restriction and no token lifetime; last review was 12 June 2024.
2. `tb-sync-svc` had `admin` scope and the same missing recorded restrictions and review date.
3. Legacy key `key-tb-03` remained active in the register despite last use on 11 January 2025.
4. E07 recorded low-risk onboarding, no recorded Security/CISO sign-off, and a due annual review with no completion recorded in that file.
5. E08 assigns Harbor & Finch responsibility for configuring available access restrictions, expiry and scope limits.
6. E15 recorded 9,790 allowed flows, including normal sync traffic and 70 build-host flows to company systems.
7. E03 shows most successful human logins used MFA. Three failed `a.kapoor` sign-in attempts from `198.18.7.77` on 15 August did not include a successful login in that sequence.
8. E14 lists Rohan Menon as terminated but still shows his status as active; the reported kiosk issue remains a separate lead.

**Member 2's conclusion:** The integration configuration is over-permissive and reviews are stale in the current-state register. Network flows do not prove data exfiltration or identify a human operator.

## Member 3 — Support and Storage Investigation

**Assigned evidence:** E02, E05, E13.

**Main contribution:** Identified the HelpDeskr export sequence and BlueVault key concern.

Key findings:

1. E13 indicates customer key `bvk-7f3a` was pasted into support ticket TKT-48213 on 25 June.
2. E02 records the ticket being created/commented on and later read by the integration principal.
3. On 11 August, `tb-sync-svc` searched for credential-related terms and read TKT-48213 before performing ten export-create/download cycles.
4. Nine export deletions succeeded and one failed.
5. E05 records 1,124 successful events by `key:bvk-7f3a`.
6. Earlier activity mainly involved customer POD documents; on 14–16 August the same key listed/read finance folders, bank instructions, vendor bank details, payment templates and statements from `198.18.7.*` addresses and some blank-source events.

**Member 3's conclusion:** The key's sharing in a ticket and later finance-file access are serious concerns. The logs do not prove that the integration extracted the key from the ticket or that downloaded copies were erased after export-object deletion.

## Member 4 — Governance, Policy and External Evidence

**Assigned evidence:** E09, E10, E11, E12, E16, E17, E20.

**Main contribution:** Established the policy and audit context and tested the external vendor's statements against internal records.

Key findings:

1. E09 includes open or overdue risks involving former-employee accounts, support-ticket data leakage, storage-key rotation and the TallyBridge connector.
2. E10 requires least privilege, IP restrictions where supported, credentials expiring within 90 days, annual high-risk reviews and monitoring of bulk exports/deletions.
3. E11's 2025 audit recorded open findings for pasted credentials, delayed offboarding, missing credential expiry/IP restrictions, unused active credentials, absent export monitoring and overdue vendor reviews.
4. E12 was a preliminary precaution notice sent to Accounts, not Security/IT.
5. E16 later claimed unauthorized requests were limited to support-ticket metadata and did not involve finance or stored files; E01/E05 contain finance-related activity that requires reconciliation.
6. E17 IP matches support that the listed addresses appear in relevant logs, but do not establish ownership or maliciousness.
7. E20 provides legitimate maintenance and software-release context for some activity and warns that some IPs may be reassigned.

**Member 4's conclusion:** The control weaknesses were known in prior governance material. The vendor's incident account is not fully reconciled with all supplied records, but attribution and scope remain uncertain.

---

# 6. Cross-System Correlation: How the Findings Fit Together

A single log does not explain the whole case. TraceCheck is intended to connect related records while preserving the limits of each source.

## 6.1 Integration permissions → financial API activity → vendor change

1. **E04** shows broad TallyBridge credentials and missing recorded IP restrictions/token lifetimes.
2. **E10/E11** show the company's policy requirements and prior audit findings about similar weaknesses.
3. **E01** records large vendor exports and repeated access to bank-detail endpoints using `key-tb-07`.
4. **E18** records the September API requests.
5. **E19** contains the resulting API-channel vendor changes, with every one of the 71 request IDs matching E18.
6. One of those changes modified V-0412's bank-account field without an approval reference in E19.

This is the strongest cross-system evidence chain for our selected defense problem.

## 6.2 Support ticket → integration ticket read → BlueVault key activity

1. **E13** says a customer key `bvk-7f3a` was pasted into TKT-48213.
2. **E02** confirms the ticket activity and later integration read, as well as credential-term searches by `tb-sync-svc`.
3. **E05** records the same BlueVault key later accessing finance-related paths.

This chain supports a credential-handling concern, but it does not prove how the key was obtained or who used it.

## 6.3 Vendor notices → internal logs → public-record context

1. **E12/E16** describe the vendor's reported incident and its claim that the activity was limited to support-ticket metadata.
2. **E01/E05** show finance-related access in the broader case period.
3. **E15/E20** provide private-link and maintenance context, including a build host.
4. **E17/E20** help validate whether indicators appear in logs while warning against unsupported IP attribution.

The time windows and credentials differ across these records. Do not merge them into one confirmed attack without further evidence.

---

# 7. Reconstructed Timeline

| Date | Evidence | Event |
|---|---|---|
| 5 June 2024 | E07 | TallyBridge approved as low risk for invoice/vendor/payment and ticket synchronization |
| 10 June 2024 | E08 | Contract excerpt dated June 2024; customer responsibilities include configuring available restrictions |
| 12 June 2024 | E04 | TallyBridge credential review date shown in current register |
| 12 September 2025 | E11 | Internal audit report records integration, export-monitoring and other findings as open at report date |
| 25 June 2026 | E02/E13 | Customer BlueVault key reportedly pasted into support ticket TKT-48213 |
| 9 July–19 August 2026 | E15/E20 | Private-link/build-host flows and maintenance/release context |
| 10 July 2026 | E13/E20 | TallyBridge version 3.5.0 and earlier nightly sync start discussed/released |
| 11–12 August 2026 | E01/E02 | Large LedgerOne vendor exports and ten HelpDeskr integration export cycles |
| 14–16 August 2026 | E05 | `bvk-7f3a` accesses finance folders and files |
| 17–19 August 2026 | E01 | `key-tb-07` repeatedly accesses vendor bank details and payment records |
| 21 August 2026 | E12 | Vendor sends precaution notice |
| 24 August 2026 | E06 | HelpDeskr billing alert/invoice reports export overage |
| 28 August 2026 | E16 | Vendor sends follow-up explanation |
| 2 September 2026 | E04/E20 | Connected-software register and saved public-records pack dated/exported |
| 1–7 September 2026 | E18/E19 | 71 API vendor changes linked by request ID |
| 3 September 2026 | E18/E19 | V-0412 bank-account field changed through `key-tb-07` without a recorded approval reference |
| 7 September 2026 | Case file | General Manager requests investigation |

**Time handling:** E01, E03, E15, E18 and E19 use UTC. E02 and E13 use tenant/local time. E05 uses epoch timestamps and an unsynchronized clock. Convert time zones and record uncertainty before asserting exact cross-system sequence.

---

# 8. What We Know, What We Infer and What Remains Unknown

## 8.1 Supported by the supplied records

- TallyBridge credentials were broad and had no recorded IP restriction or token lifetime in E04.
- Their recorded reviews were outdated.
- E10 required stronger controls; E11 previously identified similar open findings.
- `key-tb-07` made large vendor exports and accessed sensitive financial endpoints.
- E18/E19 show 71 exact request-ID matches between API requests and vendor changes.
- One API-linked bank-account change for V-0412 has no approval reference in E19.
- `tb-sync-svc` performed credential-related searches, read TKT-48213 and generated ten export cycles.
- The BlueVault key reportedly appeared in the ticket and later accessed finance-related files.
- The vendor's narrow incident statement requires reconciliation with other system records.

## 8.2 Reasonable inferences (not proven facts)

- Broad integration permissions and missing monitoring may have made it harder to prevent or detect sensitive operations.
- The BlueVault key may have remained usable beyond its intended customer/POD purpose.
- The bank-account change may have been part of legitimate synchronization or may have been unauthorized; the supplied record alone cannot decide.
- Some August activity may be related across systems, but there may also be multiple separate issues.

## 8.3 Not established

- The identity of any attacker or operator.
- That TallyBridge itself was compromised.
- That the source IPs belonged to a specific person or company.
- That the 3 September bank-account change was fraudulent.
- That a payment was made to the changed account or that financial loss occurred.
- What the downloaded export files contained or whether copies were retained.
- That the HelpDeskr integration extracted the BlueVault key from the ticket.
- That every unusual event was part of one incident.
- Whether audit findings were remediated through records not included in the supplied package.

---

# 9. Alternative Explanations We Must Test

| Possible explanation | What it may explain | What it does not yet explain / how to test |
|---|---|---|
| **Normal contact synchronization** | The vendor announced contact email/phone sync from 1 September; this may explain 70 contact changes | Does not explain the bank-account change. Check feature specification and vendor change tickets |
| **Routine Support exports** | Weekly Tuesday Support export activity | Does not automatically explain ten integration export cycles. Match export IDs, purpose and contents |
| **Finance vendor audit** | Finance may perform large vendor-list exports and approved cleanups | A named employee's 22 July export is a comparator, not authorization for TallyBridge exports. Check Finance approvals |
| **Software release or maintenance** | E20 gives context for version 3.5.0, schedule changes and some build-host flows | Does not explain every financial access or vendor change. Check deployment/change tickets and destination purpose |
| **Authorized bank update** | Finance may have approved the vendor's new bank details through a separate channel | Obtain vendor request, Finance approval, change ticket and payment/settlement records |
| **Dynamic/shared source IPs** | May explain why an IP appears in a vendor indicator list without identifying an attacker | Does not explain the recorded API/file actions themselves. Obtain authoritative IP assignment and VPN/vendor records |
| **Separate incidents** | BlueVault key exposure, HelpDeskr exports and LedgerOne changes may have different causes | Preserve separate credential and time-window analysis; do not assume one actor |

We do not reject legitimate explanations without checking them. TraceCheck should flag activity for review with reasons, not label every anomaly as an attack.

---

# 10. Proposed Defense Solution: TraceCheck

## 10.1 What TraceCheck is

We propose **TraceCheck**, a tool that compares activity across systems to identify unusual data exports, financial changes and possible security issues.

Instead of simply displaying alerts, TraceCheck will explain why an activity was flagged and show the records supporting it. We will test it using normal and suspicious activity to measure how accurately it detects problems and how often it raises false alarms.

## 10.2 Main objectives

1. Bring relevant events from different supplied evidence sources into a common analysis view.
2. Correlate identities, API key IDs, request IDs, vendor IDs, ticket IDs, source IPs and timestamps where a reliable link exists.
3. Identify unusual exports, repeated sensitive reads, credential-related searches and high-risk vendor changes.
4. Compare events with normal business schedules and known authorized activity.
5. Explain every alert with the exact evidence records that caused it.
6. Separate a confirmed record match from an inference or an unverified indicator.
7. Measure correct detections, false alarms and missed events.

## 10.3 Proposed architecture

```text
Supplied case evidence / synthetic test data
        |
        v
Input readers
(CSV, JSON, PDF-derived structured notes where applicable)
        |
        v
Normalization layer
(timestamp handling, identity mapping, field standardization)
        |
        v
Correlation engine
(request IDs, credential IDs, vendor IDs, ticket IDs, IPs, time windows)
        |
        v
Detection and context checks
(exports, sensitive reads, vendor changes, credential patterns,
known business schedules, approvals, policy requirements)
        |
        v
Evidence explanation
(reason, severity, linked records, uncertainty, alternative explanation)
        |
        v
TraceCheck report / review queue
(alerts, supporting evidence, false-positive review, test metrics)
```

## 10.4 Proposed detection scenarios

- Large vendor-data exports from a third-party credential, especially when the source or timing differs from its established baseline.
- Sensitive financial reads followed by vendor bank-detail modification.
- API-linked bank-account changes with no approval reference in the supplied change record.
- Repeated HelpDeskr exports, credential-term searches and ticket reads in a short period.
- A storage credential used outside its documented customer/POD purpose, where scope evidence supports that comparison.
- Integration credential activity that conflicts with current policy configuration or recorded review status.

These are candidate detection scenarios. Thresholds and final rules must be calibrated on the evidence and then tested on unseen variations. A missing approval field is a review signal, not automatic proof of fraud.

## 10.5 What makes TraceCheck different

A simple dashboard can show an IP, a large export or a bank-field update separately. TraceCheck's value is in showing the relationship between records and explaining the reason for the alert. It should also recognize normal activity, such as weekly Support exports, announced contact synchronization and known maintenance windows, so that ordinary operations are not automatically flagged as attacks.

## 10.6 Planned response workflow

1. TraceCheck ingests the authorized evidence or synthetic test events.
2. It normalizes timestamps while preserving the original timestamp and source clock.
3. It links records only when supported by a reliable identifier or documented correlation method.
4. It checks sensitive activity against policy, permissions, expected business activity and recorded approvals.
5. It creates an alert with the reason and supporting evidence IDs/records.
6. A reviewer confirms, dismisses or escalates the alert and records why.
7. For a simulated high-risk vendor bank change, the team may demonstrate a hold-for-review decision until an approval is verified. This is a proposed control workflow, not an existing capability.

---

# 11. Four-Member Team Responsibilities

The four members retain their evidence allocations. Each person must share evidence IDs, record-level examples, limitations and conclusions with the whole team.

## Member 1 — Finance and API Analysis

**Files:** E01, E06, E18, E19

**Responsibilities:**
- Analyze LedgerOne API activity and export records.
- Examine `key-tb-07` activity and sensitive endpoints.
- Correlate E18 request IDs with E19 vendor changes.
- Investigate the V-0412 bank-account change and approval reference.
- Check Finance authorizations and, if supplied, payment/settlement records.
- Provide normal export examples and suspicious test cases to TraceCheck.

**Deliverables:** API analysis, vendor-change correlation table, key event extracts, financial timeline and test cases.

## Member 2 — Identity, Integration and Network Analysis

**Files:** E03, E04, E07, E08, E14, E15

**Responsibilities:**
- Analyze credential scopes, owners, restrictions and review dates.
- Compare E04 configurations with E07 onboarding and E08 contract clauses.
- Review E03 sign-in activity and E14 staff identities.
- Analyze E15 private-link flows and build-host context.
- Identify reliable identity/network joins and uncertain attributions.
- Help define TraceCheck's identity mapping and normalization requirements.

**Deliverables:** Integration permissions report, identity/network analysis, onboarding/contract comparison and correlation notes.

## Member 3 — Support, Storage and TraceCheck Development

**Files:** E02, E05, E13

**Responsibilities:**
- Analyze HelpDeskr ticket reads, credential searches and export cycles.
- Review BlueVault access to customer and finance paths.
- Correlate the TKT-48213 chat and audit records.
- Build the TraceCheck prototype and input readers/correlation workflow with the team.
- Generate clear alert explanations and report outputs.

**Deliverables:** Support/storage report, prototype, sample alerts and reproducible outputs.

## Member 4 — Governance, External Evidence and Documentation

**Files:** E09, E10, E11, E12, E16, E17, E20

**Responsibilities:**
- Compare risks, policy requirements and previous audit findings.
- Analyze vendor notices and test them against internal evidence.
- Validate vendor indicators without assuming attribution.
- Record normal maintenance/release explanations from E20.
- Help design policy/approval context checks and alternative-explanation handling.
- Coordinate report quality, limitations and submission checklist.

**Deliverables:** Governance report, vendor notice/indicator assessment, alternative-explanation matrix, project documentation and submission review.

## Shared responsibilities

All four members must review the final problem statement, validate evidence references, test TraceCheck, inspect false positives and missed detections, prepare the demonstration, and be able to explain the team's conclusions.

---

# 12. TraceCheck Testing and Evaluation Plan

Defense teams are evaluated on how well they detect and contain a reference attack, whether the solution still works against an unseen variation, whether ordinary events are avoided as false alarms, the team's defense of its reasoning, and innovation/real-world value.

## 12.1 Build a labeled test set

Create test scenarios from supplied records and additional fictional/synthetic variations. Label each case as:

- **Expected/normal:** documented weekly exports, ordinary synchronization, approved maintenance or an authorized vendor update.
- **Needs review:** unusual volume, unexplained source, missing approval reference or cross-system sequence requiring investigation.
- **Confirmed test-positive:** a controlled synthetic scenario designed to represent the selected risk and with ground-truth labels known to the team.

Do not label an event “malicious” solely because an external indicator matches or an approval field is blank.

## 12.2 Measure performance

Report at minimum:

- **True positives:** relevant test events correctly flagged.
- **False positives:** normal events incorrectly flagged.
- **False negatives / missed detections:** relevant test events not flagged.
- **Precision:** true positives divided by all positive alerts.
- **Recall:** true positives divided by all actual positive cases.
- **False-positive rate:** false positives divided by all actual normal cases.
- **Explanation completeness:** whether each alert includes the supporting record IDs, correlation reason and uncertainty.

Use an explicit ground-truth label for each test. Report counts and rates; do not invent results before testing.

## 12.3 Test normal activity and unseen variations

The team should test:

1. Normal weekly Support export.
2. Routine overnight TallyBridge synchronization.
3. Announced contact email/phone synchronization.
4. Authorized Finance vendor export or approved vendor update.
5. Unusual large export from a credential.
6. Sensitive bank-detail read followed by a bank-account change without a recorded approval reference.
7. A separate BlueVault credential accessing a path outside its expected purpose.
8. A variation with different timestamps, IPs, event order, record volume or identity label.

Keep some scenarios out of threshold/rule tuning and use them only for final evaluation, so the test is meaningful.

## 12.4 Required test report

For every test run, record:

- Input dataset and version.
- Scenario and expected outcome.
- TraceCheck result.
- Alert reason and supporting records.
- Whether the result was correct.
- False positives and missed detections.
- Any changes made to the detection logic.
- Known limitations.

---

# 13. Technologies and Project Structure

The case and submission guide allow tools, scripts, libraries and AI assistance, but the team must verify its work and acknowledge external tools/components where relevant. The exact stack should be selected by the team based on what it can implement and explain reliably.

A suggested repository structure:

```text
RNwebMinds-TraceCheck/
├── README.md
├── data/
│   ├── supplied/          # original evidence; keep unchanged
│   └── synthetic/         # fictional test scenarios
├── src/
│   ├── ingest/            # input readers
│   ├── normalize/         # timestamps and field standardization
│   ├── correlate/         # cross-system record linking
│   ├── detect/            # detection logic
│   ├── explain/           # evidence-backed explanations
│   └── reports/           # output generation
├── tests/
│   ├── normal/
│   ├── suspicious/
│   └── variations/
├── results/               # measured test outputs
├── docs/                  # architecture, decisions and limitations
└── requirements.txt       # or equivalent dependency manifest
```

This is a suggested layout, not an assertion that these components have already been implemented. Do not place real secrets, personal information or credentials in the repository.

---

# 14. Competition Evaluation and Submission Requirements

## 14.1 Overall stage weights

| Tier | What is assessed | Contribution to overall score |
|---|---|---:|
| Tier 1 | Evidence-based problem statement and reasoning | 10% |
| Tier 2 | Technical concept, originality, fit and development plan | 30% |
| Tier 3 | Working solution, testing, accuracy and defense of conclusions | 60% |

## 14.2 Tier 1 — Case Analysis

**Required format:** One-page Problem Statement / Case Analysis in PDF.  
**Submission:** Official Tier 1 Google Form.

It must cover:
1. What the team believes happened.
2. Key findings with evidence IDs and relevant records.
3. Uncertainty and information that would resolve it.
4. Alternative explanations and why they were accepted or ruled out.
5. The specific selected problem and why it was chosen.
6. The obvious/conventional approach and why the team is not taking it.
7. What evidence could change the team's conclusion.
8. Selected track: DEFENCE.

**Tier 1 scoring (500 points):**

| Criterion | Points |
|---|---:|
| Problem backed by evidence from different items | 200 |
| Honest reasoning, alternatives, uncertainty and ordinary events set aside | 200 |
| Originality: explain the obvious approach and why ours differs | 50 |
| Clarity and completeness of the one-page statement | 50 |

## 14.3 Tier 2 — Technical Concept Presentation

**Required format:** Up to 10 PowerPoint slides, PPTX or PDF as specified in the form.  
**Submission:** Official Tier 2 Google Form.

The presentation must explain:
- Selected problem and evidence IDs.
- Alternative explanations considered.
- Proposed solution and objectives.
- System architecture, components and workflow.
- Technologies, tools and libraries.
- What is innovative or different.
- What has been built and what works so far.
- Testing method and preliminary results, if available.
- Known limitations and risks.
- Next development steps and expected outcomes.

**Tier 2 scoring (500 points):**

| Criterion | Points |
|---|---:|
| Technical concept and soundness | 100 |
| Originality and real-world value | 150 |
| Fit to the evidence-backed problem | 100 |
| Plan and progress | 100 |
| Communication | 50 |

## 14.4 Tier 3 — Final Solution

The official guide requires shortlisted teams to submit:

1. One-page final project presentation (PPT/PDF).
2. Complete working solution ready for live demonstration.
3. Working GitHub repository link with README, dependencies, configuration and setup/run instructions.
4. Accessible demo video link.
5. Proof pack: reproduction steps, required inputs, results, supporting evidence IDs, errors, false alarms, missed detections and limitations.
6. Approximately two-page final technical report with timeline, assumptions, alternatives and conclusions.

**Defense Tier 3 scoring areas (100 points each, per the case table):**

- Main test against reference: how well the defense detects and contains the reference activity.
- Hidden variation: whether the defense still works on an unseen variation.
- Accuracy check: whether normal events are avoided as false alarms.
- Defense of the case: ability to explain and defend the reasoning.
- Innovation and real-world value.

---

# 15. Submission and Safety Checklist

## Submission checks

- [ ] Use the correct official Google Form for each tier.
- [ ] Enter the correct team name: **RN WebMinds**.
- [ ] Enter the official team ID; do not invent one.
- [ ] Enter the four members' correct names and representative details.
- [ ] Submit Tier 1 as a one-page PDF.
- [ ] Keep Tier 2 to a maximum of 10 slides.
- [ ] For Tier 3, test all shared links and repository access.
- [ ] Ensure the README has setup, dependencies, configuration and step-by-step run instructions.
- [ ] Set Drive/video link permissions so judges can access them.
- [ ] Save the Google Form submission confirmation.
- [ ] Follow the deadline announced by the organizers.

## Safety and integrity checks

- [ ] Use only supplied fictional evidence or an authorized simulated environment.
- [ ] Do not scan, attack, test or interfere with real systems, organizations, accounts, networks or services.
- [ ] Preserve supplied evidence unchanged.
- [ ] Do not fabricate, alter or misrepresent records or results.
- [ ] Clearly label facts, inferences, assumptions and unverified claims.
- [ ] Acknowledge relevant external tools, open-source components and AI assistance.
- [ ] Do not expose credentials, API keys, passwords or personal data in GitHub or the demo.
- [ ] Do not report test metrics until the tests have actually been run.

---

# 16. Questions the Judges May Ask

The team should be ready to answer these questions clearly:

1. Why did RN WebMinds choose the Defense track?
2. Which evidence items most strongly support the selected problem?
3. How do you know the 71 vendor changes match the API requests?
4. Why is the 3 September bank-account change important?
5. Does a blank approval reference prove that a change was unauthorized?
6. What legitimate business activity could explain the exports or synchronization?
7. Why do you not attribute the source IP addresses directly to an attacker?
8. How does TraceCheck correlate events across systems with different clocks and identity formats?
9. How does TraceCheck avoid flagging normal weekly exports and scheduled synchronization?
10. What are the measured true positives, false positives and missed detections?
11. What happens when TraceCheck is tested against an unseen variation?
12. What limitations remain, and what additional records would improve the investigation?

A strong answer should refer to the evidence, explain the reasoning and state uncertainty honestly.

---

# 17. Final Team Position

RN WebMinds' investigation identifies a significant weakness in Harbor & Finch's management and monitoring of third-party integration activity. The TallyBridge credentials were broad and lacked documented restrictions; relevant policy and audit material had already identified similar control concerns; and the supplied logs show large exports, sensitive file access and API-linked vendor changes. The clearest high-risk event is the 3 September bank-account modification for V-0412, linked to `key-tb-07` and a matching E18 request, with no approval reference in E19.

The records do not establish a named attacker, credential compromise, fraudulent intent, payment diversion or financial loss. Normal synchronization, maintenance, Finance activity and separate incidents remain possible explanations that must be tested.

**Our Defense project, TraceCheck, will address the evidence-backed detection and correlation gap. It will connect activity across systems, explain why events are flagged, show the records behind each alert, and be evaluated against normal activity, suspicious scenarios and unseen variations.**

**RN WebMinds | CR-26-047 | Selected Approach: DEFENCE**

---

# 18. Source Documents and Team Reports

This README is consolidated from the following supplied materials:

- `Case_File_CR-26-047_Participant_Final.pdf` — case narrative, company systems, normal operations, evidence catalogue, competition rules, scoring criteria and appendices.
- `CRIMEATHON26_Final_Submission_Guide.pdf` — Tier 1, Tier 2 and Tier 3 deliverables, formats, submission instructions and safety requirements.
- `member_1_findings.md` — Finance and LedgerOne API findings (E01, E06, E18, E19).
- `member_2_findings.md` — Identity, integration and network findings (E03, E04, E07, E08, E14, E15).
- `member_3_findings.md` — HelpDeskr, BlueVault and Support findings (E02, E05, E13).
- `member_4_findings.md` — Governance, security policy, audit and external evidence findings (E09, E10, E11, E12, E16, E17, E20).

**Important:** This README is a team working reference. The official Tier 1 submission is still a separate one-page PDF, Tier 2 is a presentation of up to 10 slides, and Tier 3 requires a complete working defense solution and supporting materials.
