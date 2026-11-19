# Member 3 Findings — Support, HelpDeskr, and BlueVault

**Case:** CR-26-047  
**Assigned evidence:** E02 HelpDeskr audit log, E05 BlueVault access log, E13 support team chat export  
**Purpose:** Report observed support and storage activity and identify control concerns relevant to the team's integration investigation. These findings are limited to the assigned files. They do not establish who operated an integration credential or whether data was misused.

## Executive finding

The strongest finding is a likely exposed BlueVault access key followed by a distinct series of successful reads of finance files. In E13, a Support employee says a customer pasted storage key `bvk-7f3a` into ticket TKT-48213 on 25 June and that the same key had been configured for the customer's portal. E02 records the ticket being created, commented on, and subsequently viewed. E05 records principal `key:bvk-7f3a` reading customer POD documents from an internal IP for much of the period, then listing and reading sensitive finance folders and files on 14–16 August from three `198.18.7.*` addresses. This is consistent with a credential that remained usable beyond its intended customer/POD purpose, though authorization, key ownership, and source-IP attribution need confirmation.

E02 also records `tb-sync-svc` making ten successful HelpDeskr export-create/download cycles over about an hour on 11–12 August, deleting nine successfully and receiving an error on the last delete. This aligns with the chat's mention of many export jobs and complements E06's August HelpDeskr billing overage. Routine weekly Support exports are separately visible and provide an alternative explanation for some export activity.

## E13 — Chat context

The chat export is partial: it omits direct messages and edited/deleted messages, and its timezone is labeled only “local.” Key excerpts and their corroboration:

- **25 June, 11:12–11:36:** `s.iyer` says a Pune depot customer pasted configuration in TKT-48213; at 11:31 they identify an access key `bvk-7f3a` as the storage key set up for that portal. `a.nair` questions putting keys in tickets. `s.iyer` says secure-link tooling is not ready and they will tidy the ticket later. E02 records ticket TKT-48213 created at 11:11 and commented on at 11:32 by `s.iyer` from `172.16.8.64`. This supports that the conversation refers to a real ticket, but the audit log does not expose ticket contents or prove that the key was removed or rotated.
- **3 July:** `p.menon` mentions a reporting dashboard login-failure loop and a stuck script. This is possible operational context, not proof the later activity was normal.
- **10 July:** `a.kapoor` says TallyBridge updated and its nightly run starts earlier, version 3.5.0. This may be relevant to later integration behavior, but is not independently verified in these three assigned files.
- **22 July:** `f.dsouza` announces a vendor audit export. This is a plausible benign explanation for a large vendor export observed in Member 1's E01 analysis; confirm across teams.
- **28 July:** `s.iyer` says a weekly export was deleted by mistake. E02 records a weekly export create/download/delete on that date.
- **12 August:** `a.nair` observes many HelpDeskr export jobs and one stuck deletion; `s.iyer` speculates that TallyBridge caused them. E02 corroborates ten create/download cycles and one failed delete by `tb-sync-svc`; the speculation does not prove intended behavior.
- **13 August:** `p.menon` says an old kiosk login for a departed worker still works and they will raise a ticket. This is an unresolved access-control lead, not corroborated by E02/E05.
- **16 August:** `a.kapoor` reports three failed admin sign-ins, says MFA stopped them, and guesses it was a bot. These assigned logs do not confirm the events or source.
- **21–25 August:** Messages refer to a TallyBridge precaution notice and HelpDeskr export charges, followed by deferral until after close. These provide context only; other evidence owners should validate the notice and the alert.

## E02 — HelpDeskr audit log

E02 contains 25,390 events. Most are ordinary user ticket views, updates, comments, reads, and searches. There are 22 export creates, 22 downloads, and 11 deletes overall.

### Integration activity

`tb-sync-svc` appears in 1,402 events from 1 July through 31 August: 1,351 `ticket.read`, 21 `ticket.search`, and ten each of `export.create`, `export.download`, and `export.delete`. The export burst is:

| Local timestamp | Action | Export | Source IP | Result |
|---|---|---|---|---|
| 11 Aug 23:30–23:34 | create, download, delete | EXP-5410 | 198.18.7.41 | all ok |
| 11 Aug 23:38–23:42 | create, download, delete | EXP-5411 | 198.18.7.58 | all ok |
| 11 Aug 23:46–23:50 | create, download, delete | EXP-5412 | 198.18.7.41 | all ok |
| 11 Aug 23:54–23:58 | create, download, delete | EXP-5413 | 198.18.7.58 | all ok |
| 11 Aug 23:59–12 Aug 00:03 | create, download, delete | EXP-5414 | 198.18.7.41 | all ok |
| 12 Aug 00:06–00:10 | create, download, delete | EXP-5415 | 198.18.7.58 | all ok |
| 12 Aug 00:11–00:15 | create, download, delete | EXP-5416 | 198.18.7.41 | all ok |
| 12 Aug 00:16–00:20 | create, download, delete | EXP-5417 | 198.18.7.58 | all ok |
| 12 Aug 00:24–00:28 | create, download, delete | EXP-5418 | 198.18.7.41 | all ok |
| 12 Aug 00:29–00:33 | create, download, delete | EXP-5419 | 198.18.7.58 | create/download ok; delete error |

The same integration principal had 1,351 ticket reads across the period. On 11 August it issued 21 searches from `198.18.7.41`; search terms included `password`, `api_key`, `secret`, `token`, `bearer`, `private key`, `bluevault`, and `bvk-`. It then read TKT-48213 at 23:28:10, followed by the export burst. Search terms indicate secret-oriented searching but do not reveal what the integration found. The raw timestamp is `ts_local`; compare with E01 only after confirming the timezone. E02 and E01 both have Aug 11–12 activity from `198.18.7.41` and `.58`, but these logs use different systems/time conventions and have no shared request identifier in the supplied fields.

### Routine Support exports and ticket access

`s.iyer` performed a weekly export create/download from `172.16.8.12`, starting 9 June and continuing weekly through 11 August. The 28 July export EXP-5407 was deleted, matching the chat statement. The export events attributed to `tb-sync-svc` are separate from these weekly user events. This routine pattern is a credible alternative explanation for ordinary Support exports, but does not explain the ten integration export cycles or the sensitive BlueVault reads.

For TKT-48213, E02 records creation and comment by `s.iyer` on 25 June, then a view from `v.sethi` at 15:02:22 with source `198.18.30.103`, an update by `p.george` at 18:01:25, and another update by `s.iyer` the next day. The log does not show who could see the ticket beyond these recorded events, whether the key was redacted, or whether it was rotated.

## E05 — BlueVault access log

E05 contains 7,914 events, all marked `ok`: 4,859 reads, 1,726 lists, 1,012 writes, 184 shares, and 133 deletes. Principal `key:bvk-7f3a` accounts for 1,124 successful events: 1,118 reads and six lists, totaling 583,699,295 logged bytes. The logs span 3 June through 31 August.

### Use from the internal address

For most of its activity the key used source `172.16.9.40` and read customer PODs under `/customer-docs/` (including filenames such as `pod-0038.pdf`). This appears consistent with the portal/POD purpose described in the chat, subject to verifying the expected customer scope. The records do not show whether the key was restricted to that customer's documents.

### Finance-file access from other sources

On 14–16 August the same key principal used `198.18.7.23`, `198.18.7.24`, and `198.18.7.77` (and twice had a blank source IP) to list/read finance material:

- 14 Aug 21:07–21:12 UTC: list `/finance`, `/finance/bank-instructions`, and `/finance/statements`.
- Starting 14 Aug 21:16 UTC: read `vendor-bank-details-2026.xlsx`, `payment-run-template.xlsx`, and monthly statements such as `stmt-2026-05.pdf`.
- Similar reads continued into 16 Aug; the log includes repeated reads of the vendor bank details workbook and payment templates, plus statements for January–May.
- All these reads are `ok`. File sizes are in the hundreds of KB to several MB; each row's `bytes` value is recorded as a successful transfer.

This differs materially from the earlier POD reads in both source IP and data category. The same principal and no authentication transition field prevents attributing the requests to a particular human or device. The IPs' ownership and whether they belong to a sanctioned vendor egress network must be checked. A successful `read` log establishes access/transfer to the logged client, not what happened to copies afterward.

## Chronology (time basis as recorded)

| Date/time | Evidence | Event |
|---|---|---|
| 25 Jun 11:11–11:36 local | E02 + E13 | Ticket TKT-48213 created/commented; chat says customer pasted key `bvk-7f3a` and staff planned to tidy ticket later. |
| 3 Jun–31 Aug UTC | E05 | `key:bvk-7f3a` mostly reads customer PODs from `172.16.9.40`. |
| 11 Aug 23:12–23:28 local | E02 | `tb-sync-svc` searches for credentials/secrets and reads TKT-48213 from `198.18.7.41`. |
| 11 Aug 23:30–12 Aug 00:33 local | E02 | Ten export create/download cycles from `.41` and `.58`; nine delete successes and one delete error. |
| 14–16 Aug UTC | E05 | The same BlueVault key lists finance directories and reads bank-instruction, payment-run, and statement files from `.23`, `.24`, `.77`, plus blank-IP events. |

## Interpretation and limits

**Supported by assigned evidence:** A storage credential was reportedly placed in a Support ticket; that ticket was later read by the integration principal; the named key remained active in BlueVault and successfully accessed customer documents; that key later accessed finance records from a different set of source addresses; the HelpDeskr integration generated a short high-volume export sequence with one unsuccessful deletion.

**Not established:** whether the ticket key was visible to or extracted by the integration; whether the key was intended to permit all logged PODs or finance files; whether `198.18.7.*` addresses belong to TallyBridge or another approved service; whether exported files were used or retained; whether the HelpDeskr exports contain sensitive records; or whether any payment or customer harm occurred. E13 is partial, uses local time without a specified offset, and cannot settle intent. E05 lacks result failures and does not record downstream handling.

## Follow-up for the team

1. Confirm `bvk-7f3a` ownership, purpose, scope, creation/expiry/rotation history, and whether it was revoked after 25 June.
2. Check ticket redaction/deletion and audit history, including any direct or edited/deleted chat messages if available.
3. Establish ownership and approval of source IPs `198.18.7.23`, `.24`, `.41`, `.58`, and `.77`; compare with E01, E15, and external indicators without treating indicator matches as proof.
4. Determine what records each HelpDeskr export contained, why the integration created ten jobs, and whether downloads were retained; a delete event concerns the export object and does not itself prove downloaded files were erased.
5. Review BlueVault permissions for least privilege and confirm whether customer POD integrations should access `/finance` at all.
6. Correlate finance-file access with payment activity and Member 1's vendor-change timeline; normalize local timestamps and UTC before asserting sequence.
7. Preserve relevant logs and investigate the departed-worker kiosk account as a separate access-control lead.

## Evidence references

- **E02:** `Given/E02_helpdeskr_audit_log.csv` — 25,390 audit events, with `ts_local` timestamps.
- **E05:** `Given/E05_bluevault_access_log.csv` — 7,914 access events, with Unix epoch timestamps.
- **E13:** `Given/E13_support_team_chat_export.json` — 16 selected messages; partial local-time export.
