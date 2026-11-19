# CRIMEATHON'26 – OFFENSE TRACK
## Case File CR-26-047 | Investigation and Project Plan

**Project:** Third-Party Integration Access and Financial Record Investigation  
**Competition:** CRIMEATHON'26  
**Track:** OFFENSE  
**Team Size:** 4 Members

---

# 1. EVIDENCE FILE INVESTIGATION GUIDE

Each member must examine their assigned evidence files, understand what they contain, identify important records and report their findings.

| Evidence | Actual contents |
|---|---|
| E01 | LedgerOne API access log – approximately 36,000 records |
| E02 | HelpDeskr audit log – approximately 25,000 records |
| E03 | Single Sign-On log – approximately 27,000 records |
| E04 | Connected software register – 8 integration entries |
| E05 | BlueVault access log – approximately 8,000 records |
| E06 | Billing alert, internal email and invoice extract |
| E07 | Third-party onboarding review file |
| E08 | Selected contract clauses |
| E09 | Finance and IT risk register – 2 spreadsheet sheets |
| E10 | Official IT security policy, version 2.1 |
| E11 | September 2025 internal audit report |
| E12 | External company email notice dated 21 August |
| E13 | Support team chat export – 16 messages |
| E14 | Staff roster – approximately 420 records |
| E15 | Private-link flow log – approximately 9,800 records |
| E16 | External company follow-up email dated 28 August |
| E17 | External company indicator list – 5 indicators |
| E18 | Continued LedgerOne API log – approximately 2,900 records |
| E19 | Vendor record change log – approximately 370 records |
| E20 | Saved public records pack – seven categories |

**Important:** The evidence guide describes the supplied files, not the conclusions. All findings must be verified against the actual records.

---

# 2. CURRENT INVESTIGATION PROBLEM

## Working hypothesis

We are investigating whether third-party software integration access to Harbor & Finch's systems was insufficiently controlled and whether this access was associated with unusual activity or unauthorized changes to financial vendor records.

LedgerOne stores vendor payment instructions and allows outside software to connect through API credentials.

Our objective is to establish whether the API logs, connected software register, network records and vendor change log reveal a particular control weakness.

This is a hypothesis, not a confirmed incident.

## Why we selected this problem

- Vendor payment instructions are important financial assets.
- External software has access to internal systems.
- API access can occur without a person signing in.
- Several evidence files can be correlated using request IDs, timestamps, identities and IP addresses.
- The weakness can potentially be demonstrated safely using a simulated environment.

---

# 3. DIVISION OF WORK – FOUR TEAM MEMBERS

## TEAMMATE 1 – FINANCE AND API INVESTIGATION

**Main responsibility:** Investigate LedgerOne API activity and financial vendor changes.

### Assigned evidence files

- E01 – LedgerOne API Access Log
- E06 – Billing Alert and Invoice
- E18 – Continued LedgerOne API Access Log
- E19 – Vendor Record Change Log

### What to do

1. Examine API request patterns in E01.
2. Identify API key IDs, caller IPs and accessed endpoints.
3. Investigate continued activity in E18.
4. Examine all important vendor changes in E19.
5. Match API request IDs with vendor change records.
6. Examine old and new vendor values.
7. Check approval references.
8. Compare unusual financial changes with normal Finance activities.
9. Identify unusual API access and record changes.
10. Prepare a chronological financial activity timeline.

### Deliverables

- API activity analysis.
- Vendor change analysis.
- Request ID correlation report.
- Important evidence extracts.
- Financial activity timeline.

---

## TEAMMATE 2 – IDENTITY, NETWORK AND INTEGRATION INVESTIGATION

**Main responsibility:** Investigate external software access, employee identities and network activity.

### Assigned evidence files

- E03 – Single Sign-On Log
- E04 – Connected Software Register
- E07 – Onboarding Review File
- E08 – Contract Excerpt
- E14 – Staff Roster
- E15 – Private-Link Flow Log

### What to do

1. Identify all connected software integrations.
2. Investigate API credential ownership and permissions.
3. Examine integration review dates and restrictions.
4. Compare onboarding claims with actual integration settings.
5. Examine relevant contract requirements.
6. Investigate employee sign-in activity.
7. Compare employee identities with staff records.
8. Investigate private-link connections.
9. Match network activity with relevant API events.
10. Identify possible identity or integration control weaknesses.

### Deliverables

- Integration access report.
- Identity investigation report.
- Network activity analysis.
- Onboarding and contract comparison.
- Identity and network timeline.

---

## TEAMMATE 3 – SUPPORT, STORAGE AND TECHNICAL DEVELOPMENT

**Main responsibility:** Investigate support and storage activity and develop the offline simulation.

### Assigned evidence files

- E02 – HelpDeskr Audit Log
- E05 – BlueVault Access Log
- E13 – Support Team Chat Export

### What to do

1. Investigate HelpDeskr export activity.
2. Examine customer support ticket access.
3. Investigate BlueVault file access and data transfers.
4. Compare suspicious activities with normal Support operations.
5. Check whether customer documents or financial files were accessed unexpectedly.
6. Compare support activity with API and network findings from other members.
7. Develop the offline simulator using fictional data.
8. Create a mock financial system with dummy vendor records.
9. Generate controlled simulated activity.
10. Build a footprint recorder to capture simulated requests, changes and timestamps.
11. Generate an activity report from the simulation.

### Deliverables

- HelpDeskr activity analysis.
- BlueVault access analysis.
- Support activity report.
- Working offline simulator.
- Footprint recorder.
- Simulation results.

---

## TEAMMATE 4 – GOVERNANCE, SECURITY AND EXTERNAL EVIDENCE

**Main responsibility:** Investigate company security controls, previous audit findings and external company information.

### Assigned evidence files

- E09 – Risk Register
- E10 – IT Security Policy
- E11 – Internal Audit Report
- E12 – External Email Notice
- E16 – Follow-up Email
- E17 – Indicator List
- E20 – Public Records Pack

### What to do

1. Examine risks recorded by Finance and IT.
2. Identify unresolved third-party integration risks.
3. Review the official IT security policy.
4. Identify requirements for software access, credentials and employee account management.
5. Examine previous internal audit findings.
6. Check whether previous security weaknesses were resolved.
7. Analyse the external company's security notices.
8. Compare the original notice with the follow-up email.
9. Examine all five supplied indicators.
10. Check whether indicators are independently supported by the supplied logs.
11. Examine public records, service status and product release notes.
12. Identify governance and third-party security gaps.
13. Prepare the alternative-explanation analysis.
14. Help prepare the final Tier 1 problem statement and evidence summary.

### Deliverables

- Risk and governance report.
- Security policy comparison.
- Internal audit findings summary.
- External notice analysis.
- Indicator validation report.
- Public records summary.
- Alternative explanations report.
- Tier 1 problem statement draft.

---

# 4. HOW ALL FOUR MEMBERS WILL WORK TOGETHER

Each member investigates their assigned evidence independently.

After completing the initial analysis, all four members must share their results.

### Combined workflow

**Member 1:** Financial and API findings  
↓  
**Member 2:** Identity, integration and network findings  
↓  
**Member 3:** Support and storage findings, plus simulator development  
↓  
**Member 4:** Governance, external evidence and alternative explanations  
↓  
**ALL FOUR MEMBERS:** Combine findings, verify the incident hypothesis and select the final problem.

### Collaboration responsibilities

- Member 1 provides the financial activity patterns required for simulation.
- Member 2 provides the integration identities and network context.
- Member 3 builds the controlled simulator using the verified findings.
- Member 4 checks the conclusions against security policies, previous audits and external evidence.

Everyone must review the final problem statement before submission.

---

# 5. OUR PROPOSED PROJECT

## Third-Party Integration Access and Financial Change Footprint Simulator

We propose developing an offline tool that demonstrates how a verified third-party integration control weakness could produce observable system activity.

### Main components

1. **Integration identity module:** Represents fictional software identities and permissions.
2. **Mock financial system:** Contains dummy vendor records.
3. **Activity simulator:** Generates controlled test events.
4. **Footprint recorder:** Records requests, identities, timestamps and simulated changes.
5. **Report generator:** Produces an activity report showing the generated records.

### Development responsibilities

| Component | Responsible member |
|---|---|
| Financial test data and API activity requirements | Member 1 |
| Integration identities and network test requirements | Member 2 |
| Simulator development and footprint recorder | Member 3 |
| Governance validation and documentation | Member 4 |

All four members will participate in testing and final demonstrations.

The final simulation scenarios must be based on a weakness verified from the supplied evidence.

---

# 6. TIER 1 SUBMISSION CHECKLIST

Our one-page Problem Statement must include:

1. What we believe happened.
2. Specific evidence IDs and important records.
3. What remains uncertain.
4. Alternative explanations considered.
5. The particular problem we selected.
6. Why we selected this problem.
7. The conventional approach and why ours is different.
8. What evidence could change our conclusion.
9. Selected competition track: OFFENSE.

**Submission format:** One-page PDF.

**Submission method:** Official Tier 1 Google Form.

---

# 7. TEAM RULES

- Every important conclusion must have supporting evidence.
- Do not present assumptions as confirmed facts.
- Check timestamps and time zones before comparing events.
- Do not automatically trust external notices or indicators.
- Preserve the original evidence files.
- Do not fabricate or manipulate evidence.
- Keep all testing inside an authorized simulated environment.
- Record mistakes and limitations.
- All four members must understand and explain the final project.

---

# 8. FINAL TEAM OBJECTIVE

Our objective is to identify a specific weakness using multiple evidence sources, demonstrate that weakness using a controlled offline simulation, and accurately document the footprint generated by our method.

**Our guiding principle:**

"Evidence first. Investigation second. Demonstration third."

**Team size: 4 members | Selected approach: OFFENSE**
