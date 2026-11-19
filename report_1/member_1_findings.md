# Member 1 Findings — Finance and LedgerOne API

**Case:** CR-26-047  
**Scope:** E01 LedgerOne API log, E06 billing alert/invoice, E18 continued API log, E19 vendor master change log  
**Evidence handling:** The supplied case materials identify the records as synthetic. Times below are UTC as recorded in the logs. Findings are limited to these four assigned files; cross-team identity, network, contract, and governance context remains to be confirmed by other members.

## Executive finding

There is strong evidence of a third-party integration credential (`key-tb-07`, user agent `TallyBridge-Sync`) being used for high-volume exports and sensitive vendor data access, followed by a cluster of vendor record updates through the same credential. In E18, all 71 API-channel vendor changes in E19 match a LedgerOne API request by request ID. Seventy changes update contact information; one changes a vendor bank account and has no approval reference. This supports an integration access-control and auditability concern. The logs alone do not establish who controlled the credential, why the changes were made, whether the bank detail was used for a payment, or whether data was misused.

## API activity (E01)

E01 contains 36,183 requests from 3 June through 31 August 2026. Most activity is routine-looking application, reporting, backup, and user traffic. The integration credential `key-tb-07` accounts for 1,876 requests, primarily from `10.20.4.11`–`10.20.4.16`, with `TallyBridge-Sync/3.4.1` and ordinary invoice/vendor/payment endpoints.

Notable exceptions associated with `key-tb-07`:

- **12 August:** From `198.18.7.41`, it created vendor export job 9931 for 9,840 records (`req-c35c2ccaff`) and downloaded the same quantity (`req-d877f18b6c`). From `198.18.7.58`, it created job 9932 for 9,835 records (`req-51b30fba51`) and downloaded them (`req-507360d11e`). Job 9931 was deleted afterward (`req-2cb75d3eac`). The log records successful requests; deletion does not establish that downloaded copies were deleted.
- **17–19 August:** `10.20.4.77`, using `TallyBridge-Sync/3.5.0`, made 9 requests to `/v2/vendors/bank-details`, returning 640, 210, and 190 records each day (1,040 recorded rows/day), and 45 payment-search requests. On 18 August it exported 4,210 payment records (`req-fe4bd4fe93`); the export record was then deleted (`req-ab03db20b8`).
- The different IP ranges and user-agent versions are observable changes in source context, but the assigned evidence does not establish their ownership or authorization.

There are also non-integration exports: on 22 July employee `f.dsouza` created/downloaded an 8,800-record vendor export (`req-6247db07f1`, `req-13f4413535`) and deleted it (`req-330450f7ff`). That is useful context showing that large exports can occur through a named employee account; it does not explain or authorize the TallyBridge exports.

## Continued activity and vendor changes (E18 + E19)

E18 records 2,891 requests from 1–7 September. Of these, 215 use `key-tb-07`; 71 are `PATCH` requests to vendor contact or bank-detail endpoints. E19 has 367 vendor changes overall: 284 UI, 12 import, and 71 API. All 71 API changes are attributed to `key-tb-07`, have blank approval references, and match a request ID in E18 exactly.

The 71 API changes comprise:

- 44 `contact_phone` changes;
- 26 `contact_email` changes;
- 1 `bank_account` change.

The events are clustered at roughly 01:30–01:45 UTC each day, with 10 changes on 1 September, 10 on 2 September, 11 on 3 September, and 10 each on 4–7 September. Request-ID matching is a strong linkage between the API calls and recorded edits, but does not prove the business purpose or actor behind the key.

**Highest-priority record:** On 3 September at 01:44:30 UTC, E19 change `chg-8b9888c39b` records vendor V-0412, Coastal Packaging Ltd, bank account changing from `****4417` to `****9083`. It is attributed to `key-tb-07`, channel `API`, source `10.20.4.77`, with blank `approval_ref` and request ID `req-5f61b0de8`. E18 contains that same successful request (`PATCH /v2/vendors/V-0412/bank-details`, status 200). E18 also shows the same source/key reading the vendor and its bank details at 01:41:10 and 01:41:50 UTC, and reading scheduled payments at 01:42:45 UTC before the update. This sequence warrants urgent validation against approved vendor instructions and payment records. It does not by itself prove fraudulent intent or a payment diversion.

The rest of E19 includes human UI changes and bulk imports. Many UI bank changes include approval references, and a 31 July batch of 12 bank changes is recorded as an import with reference `BULK-0731`. These are useful comparators. Approval references are not uniformly populated on every UI change, so a blank reference alone is not proof of wrongdoing; the API pattern, credential, field sensitivity, matching request, and bank change together make this event exceptional.

## Billing and financial context (E06)

The 24 August HelpDeskr notice says 13 bulk-export jobs had been used against an allowance of 5 and charges are counted when a job is created even if the file is not later downloaded or is deleted. The invoice extract states 14 jobs used for August, 9 above allowance at INR 2,500 each (INR 22,500 before GST), total invoice INR 274,350. July had 4 jobs and no overage. Finance Manager Madhavi Sundar’s internal forward says Support ordinarily needs one export a week and asks for an accrual explanation.

This is evidence of an unusual increase in export-job volume and associated cost, not proof that the jobs were LedgerOne exports. E06 concerns HelpDeskr and should be correlated by other evidence before linking its billing to the LedgerOne activity. The E01 exports on 12 and 18 August are a separate, concrete LedgerOne pattern.

## Chronology (UTC)

| Date/time | Record | Finding |
|---|---|---|
| 22 Jul 06:10–06:21 | E01, three requests | Named user `f.dsouza` creates/downloads 8,800 vendor records, then deletes export job. |
| 9 Aug 03:37 | E01 `req-1c4bd03e6b` | `key-tb-07` checks exports endpoint from `198.18.7.41`. |
| 12 Aug 03:41–04:02 | E01 export requests | Two exports/downloads of 9,840 and 9,835 records from two `198.18.7.*` addresses; job 9931 deleted. |
| 17–19 Aug ~12:36–13:01 | E01 | Repeated bulk reads of bank details from `10.20.4.77`; 18 Aug payment export of 4,210 records, then export record deleted. |
| 24 Aug 14:05 IST | E06 billing notice | HelpDeskr reports 13 bulk-export jobs used, allowance 5. |
| 1–7 Sep ~01:30–01:45 | E18 + E19 | 71 matched API vendor edits under `key-tb-07`; includes one bank-account change on 3 Sep. |

## Interpretation, limits, and follow-up

**Supported:** The `key-tb-07` integration credential made successful large exports and sensitive reads in August. In September, it made 71 vendor changes recorded in E19, with every request ID matching E18. One was a bank account update with no approval reference, preceded minutes earlier by reads of that vendor’s bank details and scheduled payments from the same key and IP.

**Not established by this evidence:** external attacker attribution; credential compromise; whether the IPs are vendor-controlled; whether changes were approved outside the recorded field; actual export contents or onward transfer; whether any payment used the changed bank details; financial loss; or a causal link between HelpDeskr overage and LedgerOne events.

**Recommended cross-checks for the team:** obtain integration permissions/owner and approved source-IP list; validate TallyBridge change tickets and vendor instructions; compare V-0412 payment runs and bank settlement records after 3 September; determine whether the two August export jobs were expected and where the downloaded files went; correlate E06 job IDs with HelpDeskr audit events; preserve full request/change records and relevant approvals. Confirm timezone treatment before merging timelines from other evidence.

## Evidence references

- **E01:** `Given/E01_ledgerone_api_access.csv` — 36,183 records, 3 June–31 August.
- **E06:** `Given/E06_billing_alert_and_invoice.pdf` — billing alert, internal forward, and invoice extract.
- **E18:** `Given/E18_ledgerone_api_access_1_to_7_sep.csv` — 2,891 records, 1–7 September.
- **E19:** `Given/E19_vendor_master_change_log.csv` — 367 vendor changes; API and human/import records.
