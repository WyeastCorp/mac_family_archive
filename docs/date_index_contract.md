# date_index.json: a synopsis for the mac_family_archive front end

Source: Wyeast `origin/main` @ 71e3b11 (`wyeast/stages/date_index.py`, `_dateextract.py`,
`wyeast/schemas/date_index.schema.json`, spec `docs/specs/date-index-stage.md`). Every example
below is real output from those functions, run on synthetic text (Jane Doe, accounts `4321`,
`7788`). Paths are shortened to `…/documents/`. In a real file, `file` is the absolute path
used by every other index in the case.

## What the stage does

`date_index` runs right after `vital_doc_confirm`. It is deterministic: no LLM and no GPU, and a
whole case takes a few seconds. It dates every **confirmed vital document** and nothing else.
Media, mail and messages belong to tier 3, which is not built. It writes two files to
`output/metadata/`:

- `date_index.json`: the subject of this note.
- `vital_doc_provenance.json`: the email(s) that carried each attached vital document. The
  Mac fork already reads it, and each record now also carries the same `date_used`.

The design rules show up directly in the data:

1. **A blank date beats a wrong one.** The filesystem mtime is never used. PDF metadata, print
   dates and dates a document only *refers to* are kept as candidates but can never be the date.
   Ambiguous `01/02/2020` stays unresolved unless the case sets `date_order`.
2. **No date is invented.** Precision can be `day`, `month` or `year`, so values look like
   `2019-03-14`, `2014-01` or `2014`.
3. **"Latest" is a lead, not a verdict.** The ranked lists are labelled *"latest by date, not
   governing"*. The pipeline never says a document is superseded; that decision belongs to the
   attorney.

## Top-level shape

```jsonc
{
  "schema_version": 1, "case_id": "...", "step": "date_index", "timestamp": "...",
  "tier": 2,                     // 1 when date_index.statement_accounts is off
  "counts": { ... },             // documents, with_primary, with_date_used, form_like,
                                 // date_used_from_form, date_used_from_email,
                                 // statement_accounts, statements_ungrouped, ...
  "items": [ ... ],              // one per confirmed vital document
  "operative_views": [ ... ],    // tier 1: wills / POA / trusts / beneficiary forms, ranked
  "account_views": [ ... ]       // tier 2: statements grouped by account, ranked
}
```

## 1. `items[]`: one record per document. **The front end needs `date_used`.**

`date_used` is the single date to show. Its `basis` says what kind of date it is, and the UI
**must** word each basis differently:

| `basis` | Meaning | Suggested wording | Confidence |
|---|---|---|---|
| `execution_date` | signed/executed date in the text | "Signed 14 Mar 2019" | high (medium if several differ) |
| `period_end` | statement period end | "Period ending 31 Dec 2023" | high; medium from a 2-digit-year range |
| `as_of_date` | statement with no period, only "as of" | "As of 30 Sep 2024" | medium |
| `form_date` | month/year printed on an **unfilled form** | "Form dated Jan 2014 (unsigned form)" | low |
| `email_sent_no_later_than` | earliest email that carried it | "Existed by 5 May 2020 (emailed)" | low |
| `date_used: null` | nothing usable | "Date unknown". Show `primary_reason` to the examiner |

`primary_reason` values: `execution_date`, `period_end`, `as_of_date`, `no_execution_date_found`,
`ambiguous_day_month`, `unusable_date_only`, `form_like_date`, `no_text`.
`flags` values seen: `form_like`, `multiple_execution_dates`, `no_text`, `source_email_unresolved`,
plus per-email rejection reasons.

Example: an undated POA that arrived as an attachment in two emails. The bound comes from the
earlier one:

```json
{
  "file": "…/documents/poa_scan.pdf",
  "target": "power_of_attorney",
  "primary": null,
  "primary_reason": "no_execution_date_found",
  "source_email": { "status": "resolved", "sightings": 2 },
  "earliest_transmitted": "2020-05-05",
  "date_used": { "value": "2020-05-05", "precision": "day",
                 "basis": "email_sent_no_later_than", "confidence": "low" },
  "candidates": [
    { "value": "2020-05-05", "precision": "day", "role": "transmitted",
      "raw": "Tue, 05 May 2020 10:00:00 -0700", "span": null, "confidence": "low",
      "source": "email_date", "evidence": { "container": "extracted/mail/inbox.mbox", "message_index": 3 } }
    /* …1 more transmitted candidate (2021-07-12)… */
  ],
  "form_like": false, "form_date": null, "flags": [], "text_hash": "de900f64010dee5a"
}
```

Example: an unfilled will form ("I, ______, residing at ______ … Signed this ____ day of
January, 2014"). The month is **not** treated as an execution date:

```json
{ "primary": null, "primary_reason": "form_like_date", "form_like": true, "flags": ["form_like"],
  "form_date": { "value": "2014-01", "precision": "month" },
  "date_used": { "value": "2014-01", "precision": "month", "basis": "form_date", "confidence": "low" } }
```

`candidates[]` is evidence for an examiner "why this date" drawer, not for the main display.
Each candidate has a `role`: `execution`, `period_start`, `period_end`, `as_of`, `reference`,
`mentioned`, `print`, `metadata` (PDF Info) or `transmitted` (email). It also carries `raw` (the
exact text), `span` (character offsets into the OCR text, or `null`), plus `ambiguous` and
`readings` for dates that read two ways. Range candidates add `"range": true` and possibly
`"two_digit_year": true`:

```json
{ "value": "2023-11-30", "precision": "day", "role": "period_end", "raw": "11/1/23 to 11/30/23",
  "span": [61, 80], "confidence": "medium", "range": true, "two_digit_year": true }
```

Statements also get `accounts`: a list of the last four digits of each *labelled* account
number, for example `["4321"]`.

## 2. `operative_views[]`: wills, POAs, trusts, beneficiary forms (tier 1)

There is one view per type that has at least one document. Every instrument of that type is
listed:

```json
{
  "target": "will_testament",
  "label": "latest by date, not governing",
  "latest_by_date": "…/documents/codicil_2021.txt",
  "order_uncertain": false,
  "instruments": [
    { "file": "…/documents/codicil_2021.txt", "primary_date": "2021-06-02", "precision": "day",
      "confidence": "high", "primary_reason": "execution_date", "flags": [], "form_like": false,
      "earliest_transmitted": null,
      "date_used": { "value": "2021-06-02", "precision": "day", "basis": "execution_date", "confidence": "high" },
      "refers_to": ["2019-03-14"], "copies": [] },
    { "file": "…/documents/will_2019.txt", "primary_date": "2019-03-14", "...": "...",
      "refers_to": [], "copies": [] },
    { "file": "…/documents/will_blank_form.txt", "primary_date": null,
      "primary_reason": "no_execution_date_found", "flags": ["form_like"], "form_like": true,
      "date_used": null, "refers_to": [], "copies": [] }
  ]
}
```

How to render it:

- **Show `label` verbatim** as the heading. Never write "current", "operative" or "superseded".
- `latest_by_date` is the file of the first instrument with a `primary_date`. Highlight it as a
  *lead*. A `form_date` or email bound **never** makes a document the lead.
- Order is already final: dated instruments come first, latest first. Undated ones follow,
  ordered by email sighting, then by path. Don't re-sort.
- If `order_uncertain` is true, the top two can't be told apart at their precision (for
  example both are just `2014`, or `2014` vs `2014-08`). Show a "same period — order unclear"
  note beside the lead.
- `refers_to` holds dates the document mentions as another instrument, such as a codicil naming
  its will. Show "refers to an instrument dated 14 Mar 2019". It is **not** a link, because
  instruments are not matched to each other.
- `copies` lists other files with identical text that were collapsed onto this one. Show a
  "2 copies" chip. The instrument's email bound is the earliest across all copies.
- The fields are those of an `items[]` record, plus `primary_date`, `refers_to` and `copies`.
  `date_used` is the same object. Join back to `items[]` by `file` for candidates.

## 3. `account_views[]`: statements by account (tier 2, new 16 Oct)

There is one view per account (last four digits), ordered by those digits. A **last view with
`"account": null`** holds statements that can't be grouped:

```json
[
  { "target": "financial_statement", "account": "4321",
    "label": "latest statement by period end, per account",
    "latest_by_date": "…/documents/bank_dec23.txt", "order_uncertain": false,
    "instruments": [
      { "file": "…/documents/bank_dec23.txt", "primary_date": "2023-12-31", "confidence": "high",
        "primary_reason": "period_end", "accounts": ["4321"], "...": "..." },
      { "file": "…/documents/bank_nov23.txt", "primary_date": "2023-11-30", "confidence": "medium",
        "primary_reason": "period_end", "accounts": ["4321"], "...": "..." } ] },
  { "account": "7788", "latest_by_date": "…/documents/brokerage_asof.txt",
    "instruments": [ { "primary_date": "2024-09-30", "primary_reason": "as_of_date",
                       "confidence": "medium", "accounts": ["7788"], "...": "..." } ] },
  { "account": null, "latest_by_date": null, "order_uncertain": false,
    "instruments": [ { "file": "…/documents/consolidated.txt", "primary_date": "2024-06-30",
                       "accounts": ["1111", "2222"], "account_reason": "multiple_accounts", "...": "..." } ] }
]
```

How to render it:

- Title each account "Account ending 4321". Keep the full `label` as the subtitle.
- The ungrouped view (`account: null`) has **no lead on purpose**. Title it something like
  "Statements not grouped by account". Show `account_reason` per row: `no_account` means no
  labelled number was found; `multiple_accounts` means a consolidated statement.
- No institution is extracted. Two banks' accounts that end in the same four digits will share
  one group. Label groups by the four digits only, never by a guessed bank name.

## Front-end checklist

- **Precision-aware formatting**: `2014` → "2014", `2014-01` → "Jan 2014", `2014-01-05` →
  "5 Jan 2014". Do not pad the day or month.
- **Show basis and confidence**: low confidence (form or email) must look visibly weaker than a
  signed date.
- **Missing views are normal.** A case with no wills has no `will_testament` view, and
  `account_views` is `[]` at tier 1. An older file has no `account_views` key at all (oct7_mf's
  current one is like this), so read it with `.get(..., [])`.
- **Role**: today the fork serves `date_used` and provenance only to the examiner role
  (`_archive_data._date_used_index`, `role == "examiner"`). The views contain file paths and
  account last-fours, so decide explicitly whether the family role sees them. Defaulting them to
  examiner-only matches the current posture.
- **Contract**: `date_index.json` is a cross-repo contract (`schema_version` 1). Tier 3 will
  add records and fields, so ignore unknown keys rather than fail on them.
