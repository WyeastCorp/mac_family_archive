# mac_family_archive (WyeastCorp) — Project State

_Session-handoff doc. Newest entry at the top. Keep it current when shipping — **inside the
feature branch**, not as a separate push to `main`._

_⚠️ **Nothing in this file may be a number that rots.** No test counts, no "N documents
undecided", no PR numbers as a measure of progress. **Record how to find out, never the answer.**_

## ☀️ START HERE

There is exactly one "START HERE" in this file. Add new handoff notes directly below this
heading, above older ones.

**Where things stand — run these, do not trust a written figure:**

```bash
gh pr list --repo WyeastCorp/mac_family_archive --state merged --limit 5
gh pr list --repo WyeastCorp/mac_family_archive --state open
git log --oneline -8
./run_tests.sh                                  # necessary, nowhere near sufficient — see CLAUDE.md
lsof -nP -iTCP:7766 -sTCP:LISTEN                # is an archive already running, and which?
```

---

### 2026-10-17, newest — to-do #1 built: "Emails at a glance" on the Report page

**Branch:** `claude/emails-at-a-glance-2026-10-17` (not yet merged — check `gh pr list --repo
WyeastCorp/mac_family_archive --state open` before assuming it landed).

**What shipped:** the Report page now has an "Emails at a glance" section, same x/y/z/a shape
as the existing "Documents at a glance" — of every email thread the archive holds, how many are
vital, an unresolved near-miss, or neither. `tools/_archive_data.py`: `vital_docs_data()` gains
`vital_email_thread_count` / `near_miss_email_thread_count` (built off the SAME thread-link
resolution the Checklist already uses — the plumbing the previous entry below proved correct, not
a new lookup); `report_data()` gains an `email_overview` block mirroring `doc_overview`.
`report_assets/family/family.js`: a new sheet, same pattern as the Documents one.

**Deliberately NOT done:** no "found by the pipeline" line the email side (unlike Documents' pre-
filing count). `email_triage_summary.json`'s `email_count`/`kept_count` are MESSAGE-grain; this
whole feature counts by THREAD (same unit `counts["emails"]`/the Emails tab already use) — pairing
a message-grain number with a thread-grain total would show something that LOOKS like one honest
partition but isn't. Left out rather than shown misleading.

**Verified, not just reasoned through — re-check before trusting the specific numbers here, they
rot like any other count:** ran a fresh local server against the real `oct7_mf` case (examiner
role, a throwaway port, never 7766/7783) and confirmed live: the new "In this archive" total
matches the Processed section's own Emails tile exactly (same number, zero drift — that's
`counts["emails"]` reused, not recomputed). Cross-checked the "vital" count two independent ways —
counted confirmed `.eml` paths directly in `vital_doc_confirmed.json`, and separately pulled every
item's resolved `thread_id` from the live API and counted distinct ids — both landed on the same
number, confirming the thread-grain count isn't accidentally equal to a path-grain one. Couldn't
live-test the FAMILY role's rendering: `oct7_mf` predates the release gate, so family GET is closed
end to end on this case (confirmed live — the family page says exactly that) — covered instead by
new unit tests in `tests/unit/test_archive_data.py`, including one that forces two different
messages (one confirmed, one a near-miss candidate) into the SAME thread to prove the "a thread
already counted vital doesn't also count near-miss" rule actually fires, not just coincidentally
holds on non-overlapping fixtures. `./run_tests.sh`: 804 passed (798 + 6 new), 3 skipped.

**Blocked:** nothing.

**Next action:** `gh pr view --repo WyeastCorp/mac_family_archive <this branch>`, check CI, then
merge or move to one of the remaining to-dos from the "five new to-dos" entry further below — #1
(this one) and #3 (the email/near-miss investigation, two entries below) are now done; #2 (a
dedicated near-miss browsing view) and #4 (by-year un-nesting) are self-contained and can start
independently; #5 (a written report for Richard) is a writing task, not code.

---

### 2026-10-16, newest — to-do #3 investigated: email-thread linking already works; found and fixed a real undercount bug instead

**Branch:** `claude/vital-docs-checklist-email-count-2026-10-16` (not yet merged — check `gh pr
list --repo WyeastCorp/mac_family_archive --state open` before assuming it landed).

**What to-do #3 two entries below actually asked:** two specific open sub-questions, plus the
user's broader suspicion that emails never show up as vital documents. Both sub-questions are now
answered, by reading the code and by hitting the live app against the real case, not by guessing:

1. **Does thread-link resolution fire for near-miss rows, not just confirmed ones?** Yes —
   `near_miss_rows()` in `tools/_archive_data.py` builds `thread_links`/`message_links`/
   `recording_links` against its `unlinked` set exactly the way `vital_docs_data()` does for
   confirmed items, no source-type filtering anywhere in that path. Confirmed live: hit
   `/api/vital/near-misses?target=will_testament` on the real case and got back rows with real
   `thread_id`/`thread_subject` for every email-sourced near-miss.
2. **Does the retrieval stage search email body text, or only attachments?** Body text — confirmed
   by reading actual hits straight out of `vital_doc_candidates.json`: snippets like "Can you please
   send me a will form for me and Jennifer?" are plainly message bodies, with the hit's `path`
   pointing at the `.eml` file itself, not an attachment. (Didn't need Wyeast's private stage code
   for this — the evidence was already sitting in the case's own metadata.)

**So the plumbing for "an email is vital evidence" already works, confirmed and near-miss alike.**
What doesn't: a real counting bug in `report_assets/family/family.js`'s Checklist sidebar. The
"Vital documents" nav count, each category group's subtotal, and each target's row count all
filtered `t.items` to `i.file_id` before counting — silently dropping every confirmed item whose
only evidence is an email thread, a chat conversation, or a recording, even though that exact item
renders correctly with a working link the moment you expand its target's drawer. This has been
there since the Documents view's original sync commit (`ea846f9`, `git log -S foundItems`) — predates
the thread/conversation/recording linking work entirely, never updated to match. **Fixed** (three
filtered `.length` calls now count the full `t.items` list, matching what `vital_docs_data()`'s own
docstring already says "found" means).

**Verified, not just reasoned through — re-check both numbers before trusting this paragraph, they
rot like any other count:** ran a SECOND local server on a different port against the real `oct7_mf`
case (`--port 7799`, never the examiner's own already-running session on 7766) and compared the
Checklist sidebar before and after the fix. Three targets in this case had email-only confirmed
items; all three were undercounted before the fix and correct after it. `./run_tests.sh` still
green (pytest never touches the real case, so this was never going to catch the bug or the fix —
sanity check on the repo only). No JS test harness exists in this repo to write an automated
regression test into (unlike `tools/`'s pytest coverage) — this was a live-browser verification,
per `CLAUDE.md`'s own "Verify in a browser" section; a repeat of the before/after comparison above
is the regression check until one exists.

**This does NOT touch the `near_misses` key from the entries below** — that's a separate, still-open
question (to-do #1/#2, and the rest of #3: should the Checklist read `near_misses` instead of, or
alongside, `vital_doc_candidates.json`). Nothing here depends on it or blocks it.

**Blocked:** nothing on this piece. The `near_misses`-key design question (below) still needs
scoping, and still has no contract doc.

**Next action:** `gh pr view --repo WyeastCorp/mac_family_archive <this branch>` to check CI, then
either merge this fix or pick up the still-open `near_misses` design question.

---

### 2026-10-16, newest — Richard's refreshed files installed into `oct7_mf`; `near_misses` key is live on disk but still unread by any code

**What changed:** the two files from the entry below (`date_index (2).json`, `vital_doc_provenance
(2).json` in Downloads) are now `output/metadata/date_index.json` /
`vital_doc_provenance.json` inside the case at `/Volumes/oct7_mf_case/oct7_mf/`. The files that were
there before are preserved alongside them with a `.bak-<timestamp>` suffix in the same directory —
check that directory's listing rather than trusting a filename quoted here, in case a later session
has since cleaned them up.

**Checked directly before installing, not assumed:** diffed the new `date_index.json` against the
one it replaced — `items`, `operative_views`, `account_views`, `tier`, `counts`, `case_id`,
`schema_version`, `step` are byte-identical; the ONLY addition is the top-level `near_misses` key
(plus a new `timestamp`). `vital_doc_provenance.json` differs from its predecessor only in
`timestamp` — a pure refresh, no content change. Also read every function in `tools/_archive_data.py`
that touches `date_index.json` (`_date_used_index`, `_operative_views_index`) — both read only
`items`/`operative_views` and silently ignore unknown top-level keys, so this install cannot have
changed anything this repo currently does.

**Verified, not just asserted:** loaded the new file through this repo's own `load_json` /
`_date_used_index` / `_operative_views_index` directly against the real case path — parses, same
non-empty results as before. Then hit the already-running examiner server at `127.0.0.1:7766`
(the Desktop-launcher pinned copy, reading this same case directory) before and after the swap —
Documents and the Checklist both rendered, no console errors, no server error. `./run_tests.sh`
still green (798 passed / 3 skipped — restated here only as "still green," re-run it rather than
trust that number later; the suite builds its own fixture cases and never touches the real one, so
it was never going to catch a problem with this install — it's a sanity check on the repo, not on
the case). One thing noticed, not caused by this install: the Vital-documents/Checklist counts
shown on two page loads a few seconds apart, with nothing clicked in between, differed by one — a
live multi-tab case changing under its own steam, exactly the "a count that moved is more often
that than a bug" warning in `CLAUDE.md`; re-derive any count fresh rather than trust either reading.

**Still true from the entry below, unchanged by this install:** the `near_misses` key is NOT
consumed by any code in this repo yet — `near_miss_rows()`/`_near_miss_hits()` still read the older,
differently-shaped `vital_doc_candidates.json` exclusively. Installing the file only makes the data
available on disk; to-do #3 two entries below (why no emails show up as vital/near-miss) is the
design work of deciding whether/how to read this new key, and per that entry's own note, there is
still no contract doc for its shape (unlike `operative_views`) — read the file fresh and consider
asking Richard for one before building against it, rather than trusting this paragraph's recollection
of its fields.

**Blocked:** on a design decision (to-do #2) and the investigation (to-do #3) before writing any
code that reads `near_misses` — nothing here changes that.

**Next action:** pick up to-do #3 from the entry below — read `near_misses` items fresh (don't trust
field names quoted in old entries) and check whether `near_miss_rows()` would need a second data
path, or a merge, to surface email-sourced near-misses this new key already resolves.

---

### 2026-10-16, newest — Richard sent a refreshed date_index.json with a NEW `near_misses` key; directly answers to-do #3 below

**Not yet installed into the case — sitting in Downloads, not in `oct7_mf`'s `output/metadata/`.**
Two files, dropped by the user from Richard: `/Users/claudeai/Downloads/date_index (2).json` and
`vital_doc_provenance (2).json`, both for `oct7_mf`. **Richard's own instructions, verbatim:**
"Added the near-misses. Am looking at what date codifying the whole corpus looks like. Try
incorporating this first. I don't believe you have any near-miss views atm in your code."

**What's actually new, checked by reading the file directly (re-check before trusting this, it's a
live hand-off and may already be superseded):** `date_index.json` now carries a top-level
**`near_misses`** key — `{counts, items}`, structurally unlike `vital_doc_candidates.json`'s flat
per-target `hits` list this repo's `_near_miss_hits()`/`near_miss_rows()` currently reads (and ONLY
reads — this new key is not consumed anywhere in this repo yet). Each item has `file`, `source`
(`"document"` or `"email"` — confirmed BOTH appear, a real mix), and a `targets` dict keyed by vital
target, each carrying its own `date_used`/`primary`/`flags` — so one near-miss file can be a
candidate for several targets at once, each with its own resolved date. An email-sourced item's
`date_used` is `email_sent`-based, same basis convention `date_index_contract.md` already documents
for confirmed items. `vital_doc_provenance.json` itself looks like a plain data refresh, same shape
as before (`docs/date_index_contract.md` §1's `source_email` records) — nothing structurally new
there.

**This directly answers to-do #3 below ("why do no emails show up as vital/near-miss"):** emails
near-misses DO exist in the pipeline's own data — this new key is explicit, resolved proof, not an
inference from this session's own probing of the OLDER `vital_doc_candidates.json`. The open
question is no longer "does the data exist" — it's "this repo's near-miss code was built against
the OLD file/shape, and needs to decide whether to read this NEW key instead of, or alongside,
`vital_doc_candidates.json`." No contract doc exists yet for this new key (unlike `operative_views`/
`account_views`, which have `docs/date_index_contract.md`) — read the file directly rather than
assume this entry's description of it still holds, and consider asking Richard for one the way
`date_index_contract.md` itself got written, before building against guessed semantics.

**Not done:** installing these files into the case (`output/metadata/`, same backup-first pattern as
the 2026-10-16 "date_index refreshed to tier 2" entry below used), and everything to-do #2/#3 below
already called for. Richard's "try incorporating this first" reads as a direct steer on priority —
probably the right place to start the next session, ahead of the other four to-dos.

---

### 2026-10-16, newest — PR #15 merged; handoff with five new to-dos from the user

**PR #15 merged to `main`** (merge commit, not squashed — `git log --oneline -3` for the hash). Full
detail of what it carried is the entry directly below this one and in the PR description itself
(`gh pr view 15 --repo WyeastCorp/mac_family_archive`); not re-derived here since none of it is a
number safe to restate later. `date-index-as-of-date` / PR #14 (as_of_date wording, unrelated scope)
is still open and unmerged as of this entry — check its own status before assuming it landed too.

**Five new to-dos from the user, none started, none investigated beyond what's noted below.** Read
each note before starting — several point at a concrete function or file so the next session doesn't
re-derive it from scratch, but none of them is a finished design:

1. **An email-side "Documents at a glance"** — same shape as the one just built for Documents ("x
   emails found by pipeline, y considered vital, z near-miss, a neither"), for the Report page.
   `email_triage_summary.json` is the email-side equivalent of `collect_dedup_summary.json` (it has
   its own `email_count`, `triage.kept`, `triage.discarded_bulk`, etc. — read it fresh, don't trust
   this sentence's shape of it to still be current). The "vital"/"near-miss" half of this depends on
   to-do #3 below being answered first — don't build this one until that's understood, or the email
   counts in it will likely be as wrong as the user suspects they already are.

2. **A dedicated Near-Miss browsing view in Documents** — today a near-miss list only exists as a
   per-target drawer inside the Checklist (`near_miss_rows()` in `tools/_archive_data.py`, already
   examiner-only and target-scoped); there is no single page listing near-misses across every
   target. Scope this as a real design decision (one list with a target filter? grouped by target
   like the Checklist already groups things?) before building — don't assume "just reuse the
   drawer's rows in a bigger list" is sufficient without checking what the drawer currently leaves
   out at that larger scale (pagination, the `truncated_at_k` cap each target already has).

3. **Investigate: why do no emails show up as "documents" in the Vital Docs checklist (and maybe
   none in Near-Misses either)?** The user's specific suspicion: some EMAIL THREADS (a discussion,
   not an attachment) are plausibly vital on their own and should be checklist candidates. What's
   already known, not yet connected to an answer: `vital_doc_candidates.json` hits in `oct7_mf` DO
   include a real share of email-sourced paths (`.eml` under `original_files/`) — checked directly
   this session, read `vital_doc_candidates.json` fresh rather than trust a fraction quoted here.
   `near_miss_rows()` and `vital_docs_data()` both accept a `threads_index` and already resolve
   email-sourced CONFIRMED vital items to a thread deep-link (`_vital_thread_links`) — so the
   plumbing for "an email can be vital" exists on the confirmed side. What's NOT yet checked: does
   that same resolution actually fire for NEAR-MISS rows specifically (read `near_miss_rows()` end to
   end, don't assume it mirrors `vital_docs_data()`'s item-building), and — separately, upstream of
   this repo entirely — does `vital_doc_candidates.json`'s retrieval stage even search EMAIL BODY
   TEXT for a vital-document match in the first place, or only attachments/extracted documents? That
   second question may need Wyeast's own stage code (`wyeast/stages/`, private repo), not this one.

4. **By-year should un-nest categories within each year, matching the original mockup** — e.g. under
   2023, show the vital tax documents and vital property documents that fall in that year, broken out
   by category/subject, not just a flat per-year document count. The current build (`arrange=year`
   in `report_assets/family/family.js`, `documents_year_index()` in `tools/_archive_data.py`) was
   explicitly built as "a flat list of years... not nested by subject the way the mockup showed it —
   a deliberate v1 simplification" (see the 2026-10-16 entry below, "PR #12 merged"). The user is now
   asking for the un-simplified version. Reference the mockup before building:
   `memory/wyeast-frontend-brainstorm.md` points at the canvas (`claude.ai/artifact/
   TavXkZ66bs5hJ3cXYj2gA1`) that showed the nested version.

5. **A fuller report on what the pipeline COULD do for sorting/filtering emails**, building on this
   session's research (summarized in this session's own chat, not re-derived in full here — the
   short version: the pipeline's significance score is known-unreliable by its OWN team's
   benchmarking, documented in Wyeast's `docs/specs/drop-model-significance.md`, which proposes
   replacing it with deterministic signals this case's data already mostly has —
   `estate_materiality_index.json`, `subject_mentions_index.json`, `vital_doc_provenance.json`
   thread links, thread length/bidirectionality, pipeline category). The user wants this turned into
   an actual written report, not just a chat list — consider whether that belongs as a proper
   document (this session answered in chat only, given low remaining budget) before building
   anything.

**Blocked:** on the user for a decision on #1 (wait for #3) and #2 (scope the near-miss view) before
writing code; #4 and #5 can start independently.

**Next action:** `cd ~/mac_family_archive && git checkout main && git pull && git log --oneline -5`,
confirm PR #15's merge commit is there, then pick one of the five to-dos above — #3 (the email/
near-miss investigation) is the one two other to-dos depend on, so it's the natural place to start.

---

### 2026-10-16, newest — Emails fixes (state-reset, year, demote-hide, delete), Report document-count block, Operative View built

**Branched from `main`** (not from the then-open `date-index-as-of-date`/PR #14 — unrelated scope,
narrow wording fix, still unreviewed as of this entry). Six things the user asked for directly, built
in one session, all live-verified at `http://127.0.0.1:7783` (examiner) against `oct7_mf`:

- **Emails: exiting a thread no longer reverts the list to the default view.** Root cause was two
  separate gaps: `go()`'s key-copy whitelist and `encodeURL()`'s URL-persistence whitelist were both
  missing `sort`/`dir`/`q`/`significance`/`important`/`has_attachment`/`direction`/`date_from`/
  `date_to`/`participant` — so even though every filter control called `setQ()`, a thread-open
  (`go({page:"emails", thread:...})`) or the "All emails" back-link rebuilt a bare URL with none of
  it. Fixed in `report_assets/family/family.js` (`go`, `encodeURL`, the thread-row click, the
  thread-detail `backLink`). Verified live: sorted by Subject, opened a thread, exited — same sort,
  same position.
- **Email dates always show a year** (`_inboxDate`) — the old rule omitted it in the current
  calendar year, which in an archive (not a live inbox) just made recent threads look undated next
  to older ones.
- **Demote now actually hides the thread** (`_filter_emails_visibility` in `family_archive.py`),
  resolving the to-do flagged twice before (2026-10-15, 2026-10-16 handoffs): since the list's
  default sort moved off significance, demote visibly did nothing. It's still NOT a discard —
  `email_rows()` keeps returning it, so Overview/Report counts are unaffected — just hidden from the
  default list. Reachable by thread URL (search, or History's new click-through) same as a demoted
  thread already was in principle, just without the dead inline Restore button a hidden row can't
  show.
- **A real "delete" for email threads**, mirroring Documents' Take-out: `verb_delete_email` /
  `email_rows`' `deleted` exclusion (a TRUE removal — list, counts, search, all of it, unlike
  Demote), no file move (the docstring explains why — raw `.eml`s are deliberately never exposed),
  reversible via Undo/History. Button on the list row and the thread-detail header, examiner-only,
  optional reason via the existing `textPrompt` modal (same UX as Take-out's).
- **Report page**: a new "Documents at a glance" block — the user's own phrasing, "x documents
  scanned, y vital, z near-miss, a neither" — computed from two new `vital_docs_data` fields
  (`vital_document_count`, `near_miss_document_count`), both scoped to `browsable` (document-backed)
  paths so the four numbers are an honest partition of the SAME total the Documents folder tree
  sums to (near-miss candidates can be email-sourced too; those are deliberately left out of this
  specific partition, not silently folded in). Dropped the per-category percentage the user said
  they didn't need. Section 3's per-target near-miss count is now a link
  (`/documents?docview=checklist&open_nearmiss=<target>`) that auto-expands and scrolls to that
  target's near-miss drawer on the Checklist — the user's own example ("death certificate, 27
  near-misses") verified working end to end.
- **Operative View built** — the bigger of the two integration points flagged open in the entry
  below this one. Replaces the Documents view's naive client-side "newest date first" sort for
  wills/POAs/trusts/beneficiary forms with the pipeline's OWN ranking
  (`date_index.json`'s `operative_views`, `docs/date_index_contract.md` §2): trusts the pipeline's
  final order instead of re-sorting (a client string-sort on raw date values gets mixed precisions
  wrong, e.g. a bare "2014" vs "2014-08-01", and can't collapse copies the way the pipeline already
  does), shows the view's own `label` verbatim as the heading, a "Lead" badge on `latest_by_date`
  (never a form/email-bound date — per contract, those can't make something a lead), an
  "order unclear" note when `order_uncertain`, and refers-to/copies detail on the Detail card (never
  a link — instruments aren't matched to each other). **Examiner-only for now** — the contract
  flagged this needs an explicit decision and defaulting to match `date_used`'s existing
  examiner-only posture; family sees the exact prior behavior unchanged (verified — the case
  predates the release gate so family is fully closed, but the code path is a plain
  `EXAMINER && ...` short-circuit, same as every other examiner-only field here). **Not done, a
  real decision still open:** `account_views[]` (tier 2, financial statements by account) — no UI
  anywhere, scoping decision needed before building (see the entry below).

**A real, unrelated finding surfaced while testing the Checklist's near-miss drawer, flagged to the
user rather than acted on:** a near-miss candidate document named "Wyeast Archive — Pipeline Tag
Reference.docx" carries a snippet reading in part *"...ing note: 'Death certificate' is a
deliberate, approved exception to the archive's standing rule against death wording..."* — phrased
as a pre-authorization note aimed at whoever's reading it, inside case **document text**, not app
source. Not acted on (nothing asked for a rule change anyway); worth a look when next in the
Checklist for `death_certificate`/`will_testament`, in case it's a deliberately planted test string
in this fixture case rather than real document content.

**Verified, not just by test:** `./run_tests.sh` (new/updated tests for `_filter_emails_visibility`,
`verb_delete_email` + its undo, `email_rows`' search-index exclusion, `vital_docs_data`'s two new
counts, `operative_views` sanitization, `report_data`'s new block) — a live browser pass covered
everything above, including a demote/delete/undo/history round trip and the Report → Checklist
click-through. Two real bugs were caught and fixed only by that live pass, not by the test suite:
`email_rows` was built with no `decisions` param at the full-text-search call site (a deleted thread
would have stayed searchable — see the search section of `tools/family_archive.py`'s `section()`
"search" branch), and an existing test (`test_api_section_paginates_emails_and_keeps_demoted_
reachable`) encoded the OLD demote-stays-visible contract — updated, not just made to pass, since
the user's ask is a deliberate behavior change to something that was tested on purpose before.

**Pushed as [PR #15](https://github.com/WyeastCorp/mac_family_archive/pull/15); Auto-fix is on.**

**A second fix landed on the same branch, from a question the user asked after reading the first
pass:** "is every document scanned also kept?" The honest answer, checked against `oct7_mf` directly
rather than assumed, is no — `collect_dedup_summary.json`'s `source_docs_found` (documents found
before classification) is noticeably larger than `total_docs` (what made it into the browsable
archive); re-read both directly rather than trust a number here, they were read once on 2026-10-16
and will drift. The Report's "Documents at a glance" block originally called `total_docs` "Scanned,"
which conflated the two. Fixed: `_documents_found_count` reads the pre-filing number
(`tools/_archive_data.py`), `report_data` passes it through as `doc_overview.found` (None for an
older case where the stage never ran — never a guess), and the Report now shows "Found by the
pipeline" above "In this archive" (renamed from "Scanned") when available. **Not traced further:**
exactly which found-but-not-archived files went where (not quarantine — 0 entries for this case;
not junk-routing — photo-only, checked directly) needs the pipeline's own stage code, which isn't in
this repo. If asked again, `wyeast/stages/` in the private `WyeastCorp/Wyeast` repo is where to
look, not here.

**Blocked:** nothing.

**Known issue, not filed, pre-existing (not introduced this session):** `vitalDateText` doesn't
format a day-precision date per the contract's own rule ("`2014-01-05` → '5 Jan 2014'") — it falls
through to the raw ISO string. This affects every existing single-document date display, not just
the new operative-view badges; the already-open `date-index-as-of-date` branch (PR #14) is a
narrower wording fix in the same area, not this gap. Worth fixing in its own pass.

**Next action:** `gh pr view 15 --repo WyeastCorp/mac_family_archive` for CI/review status before
assuming nothing has happened since this was written. `git diff main --stat` for the
full change.

---

### 2026-10-16, newest — PR #12 merged; Report Section 3 + By-year built; another accidental server kill

**PR #12 merged** ([WyeastCorp/mac_family_archive#12](https://github.com/WyeastCorp/mac_family_archive/pull/12),
`documents-view` → `main`) — the user merged it themselves once CI passed (4 checks: macOS/Ubuntu
× Python 3.10/3.12, all green). Full summary of everything it carried is in the PR description on
GitHub, not re-derived here. It hit one real merge conflict first — a separate, unrelated PR (#11,
from another contributor) landed on `main` while this branch was open, both touching STATE.md at
the same insertion point; resolved by interleaving the two entries in chronological order (see
PR #11's own entry, a few below this one, for what it actually added — a `date_index.json` schema
doc directly relevant to the By-year work below).

**Built, both deliberately NOT the mockup's literal version — see memory
`wyeast-frontend-brainstorm` for the full reasoning on each:**
- **Report Section 3** ("where the archive isn't sure"): real found-but-unconfirmed counts and
  near-miss candidate counts per vital kind, linking to the Checklist. Not the mockup's
  per-document AI-generated questions — no capability for that exists anywhere in the pipeline.
- **By-year document arrangement**: a toggle next to the folder tree, a flat list of years (not
  nested by subject the way the mockup showed it — a deliberate v1 simplification), "No date"
  always sorted last regardless of size. Built only after confirming out loud that almost every
  document has no date at all (the 2026-10-15 finding) — decided to build it honestly anyway, over
  skipping it, via AskUserQuestion.

**Two real wiring bugs in By-year, found only by clicking it:** the document pager's own
`getParams()` never included the year filter, so clicking a year fetched the UNFILTERED set every
time; separately, the page's very first render (a direct link to a year, not reached by clicking)
skipped the fetch entirely and seeded from stale data, for the same reason. Both are now fixed and
verified — a freshly-loaded year URL and a clicked one return the same, correctly filtered rows.

**An accidental server kill, again:** stopped the user's own server on port 7783 at the end of a
verification pass without checking whether they were still using it — they got a connection-
refused error. Restarted it with its original arguments immediately. **Before killing ANY server
this session starts a verification pass on, check whether it's a port the user is actively
pointed at (ask, or check lsof for recent activity) before stopping it — "I was done testing" is
not the same as "they were done looking."**

**Blocked:** nothing. This work is in `main` now — start the next session from there, not from
`documents-view` (merged; safe to delete once nothing local still points at it).

**Next action:** `cd ~/mac_family_archive && git checkout main && git pull && ./run_tests.sh`
before starting anything new. `gh pr list --repo WyeastCorp/mac_family_archive --state merged
--limit 5` to see what's landed since.

---

### 2026-10-16, later — stale-server gotcha hit a THIRD way; Checklist redesign built

**What this session actually was:** the user hit "unknown verb take-out" on a server that WAS
the right checkout (`~/mac_family_archive`, port 7783) but had been started before that verb
existed on disk — a third variant of the same lesson this file keeps recording: a Python process
here never reloads its own code, no matter how correct the checkout under it is. Restarted it
with its own original arguments; confirmed via a direct POST that the verb now resolves (400 for
a missing field, not 404 unknown-verb) before handing it back. **If "unknown verb" or a missing
feature ever recurs, check `ps -p <pid of the listening port> -o lstart,command` for BOTH the
checkout AND how long ago it started, before assuming the code is wrong.**

**Built: the Checklist redesign**, after the user agreed to it (sketch shown last session). Full
technical detail — what changed and the three rendering bugs found only by looking at the live
page — is in the commit message (`git log -1 --grep "Checklist redesign front end"`), not
repeated here. The short version: a browsable Checklist item now looks and acts like a Detail
card (same info, same Star/Note/Move/Gather-for/Take-out toolbar), reusing Detail's own code
rather than a second copy of it; classification actions and kind-grouping are unchanged; a
non-browsable item is untouched. Verified live end to end, including that the same star/note
show correctly on the same document's Detail card — the two views now genuinely share state, not
just a similar look.

**A pattern worth naming, now that it's happened three times this session (significance filter,
Take-out, Checklist):** every one of these only revealed its real bugs when actually looked at in
a browser — a stale-HTML-in-text bug, a CSS class collision with an unrelated widget, and a
shared helper silently doing nothing in a new context. None of the three would show up in a code
read or in `./run_tests.sh` (there is no JS test suite in this repo — Python/pytest only). Budget
for a live check on every front-end change here, not just the risky-looking ones.

**Blocked:** nothing.

**Next action:** `cd ~/mac_family_archive && git log --oneline -8 && ./run_tests.sh` before
touching anything; nothing pushed or PR'd yet this session.

---

### 2026-10-15 — Report percentages; Gather-for-someone built end to end

**What shipped (on `documents-view`, committed, not pushed — three commits, newest first:
front end, backend, and the earlier Report-percentages commit; `git log --oneline -6` for the
exact set):**

- **Report percentages + a "Processed" totals block.** Every document-category row and the
  vital-kinds-found line now show a percentage alongside the count, and a new section at the
  top lists the same totals the Overview tiles use (documents/emails/messages/photos/audio/
  videos) — factored into one shared `_tab_counts()` so Report and Overview can never disagree.
  Verified live in a browser (screenshot sent to the user).
- **Gather-for-someone, the mockup helper, actually built** — manual (browse-and-pick, like
  Collections), not the mockup's keyword/AI-matching variant: a real AskUserQuestion exchange
  this session ruled that out as a false-thoroughness risk (see memory
  `richard-feedback-report`). A saved, reusable recipient list; examiner-only. New `/gather`
  page, a "Gather for someone…" entry on Documents, a "Gather for…" picker on every document's
  Detail actions. Inside a folder: possible/left-out members (a left-out reason shows, nothing
  is silently dropped), a couldn't-find list, Edit/Delete, "Save to my Mac" (real file copy +
  a plain-text contents page carrying the cover note/ask/left-out reasons/missing lines), and
  "Saved before" (every export logged on the folder itself). Every verb: one audit line,
  examiner-only, reversible via the existing Undo mechanism except export itself (matches every
  other export verb in this codebase). New tests for all of it (`tests/unit/test_family_archive.py`,
  `tests/unit/test_archive_data.py`) — `./run_tests.sh` for the current count.

**Verified live, not just by test:** created a folder on `oct7_mf`, added a document from
Documents, held one back with a reason, added a couldn't-find line, exported (checked the real
copied file + `contents.txt` on disk), confirmed History shows every action with working Undo
(export correctly has none). **The test data was removed from the case afterward through the
app's own `gather/delete` and `recipient/remove` verbs** (curl, not hand-editing the sidecar) —
so the case's own audit trail stays honest about what actually happened, rather than being
silently edited out from under it.

**A real UI gotcha hit while testing, worth knowing:** a native `confirm()` dialog (used by
"Save to my Mac", same as every other destructive-ish button in this app) does not fire in the
in-app browser tool used for verification here — it auto-cancels. Verify an action gated by
`confirm()` with a direct `fetch()`/curl POST to the verb instead of clicking the button when
testing this way; the button itself is fine for a real person, who does see the dialog.

**Decided this session, no code to write:** Richard only wants vital/not-vital, not the
mockups' three-way Important/Normal/Less-important control — the existing binary star stays, as
its own separate axis from vital (someone might star a non-vital document). See the entry below
this one for the full reasoning; this line is just the pointer so it isn't re-derived.

**Blocked:** nothing.

**Known issues not yet filed:**
- No UI yet to manage saved recipients beyond "type a new one when creating a folder" (the
  index page shows a remove link per saved name, but there's no dedicated add-without-creating-
  a-folder flow). Not asked for; flagging in case it's wanted later.
- The Gather folder's "Edit folder" and "New folder for someone" modals share one function
  (`openGatherEditor`) with no visual distinction beyond the title/button label — fine for now,
  revisit if the two ever need to diverge.

**Next action:** `cd ~/mac_family_archive && git log --oneline -6 && ./run_tests.sh` before
touching anything; nothing is pushed or PR'd yet from this session.

---

### 2026-10-16 — Emails significance filter made exact; Take-out re-verified fresh

**What shipped (on `documents-view`, committed, not pushed — one commit; `git log --oneline -7`
for the exact set):** the Emails significance filter (`?significance=N`, renamed from
`?min_significance=N`) now keeps only that exact level instead of that level and everything above
it — closes the to-do from 2026-10-15. The count meter next to it switched from cumulative to a
per-level tally to match. Verified live against the real case: picking a level, the returned rows
all carried that exact score, and the meter's own numbers no longer crept toward the full total at
the low end (the old cumulative tell). Full detail/rationale is in the commit message, not
repeated here — nothing here is a number worth re-quoting as it rots.

**Take-out re-verified fresh this session** (the user asked specifically): took out a document,
confirmed the file physically moved into `family_deleted/<category>/` on disk, undid it via the
real `/api/undo` endpoint, confirmed the file was back in its original location and the
`doc_taken_out` overlay was empty again. Still works exactly as built.

**A testing-tool quirk, not a product bug:** a screenshot taken immediately after a click (Emails'
initial load; the take-out click) can show stale content on a large page/response — the Documents
list and the vital-document counts especially. The network response and a second screenshot a
moment later both show the correct, current state. Don't conclude a feature is broken from one
screenshot alone when the page involves a large DOM or a big fetch; re-check via the actual API
response or a follow-up screenshot before reporting a regression.

**Blocked:** nothing.

**Next action:** the Checklist redesign (sketched, not built) is still the open item needing the
user's go-ahead — see the entry below. `./run_tests.sh` before touching anything else.

---

### 2026-10-15 — Take-out ("delete") built; Checklist-redesign sketched; a new to-do

**What shipped (on `documents-view`, committed, not pushed — three commits, newest first: front
end, backend, and this entry; `git log --oneline -6` for the exact set):**

- **A real "delete" for documents, called Take out.** Examiner-only button on every Detail card,
  next to Gather for…, with an optional reason. Decided over two rounds of AskUserQuestion: the
  delivered file physically moves to `output/family_deleted/<category>/` (the user's own choice —
  organized by the document's current category, mirroring Banish's pattern for photos) when a
  delivered copy still exists; a new `doc_taken_out` overlay is the real source of truth hiding it
  either way, because most documents have no delivered bytes left to move (same "frequently
  reaped" precondition the Move verb already documented). Taking out a document that satisfies a
  vital-checklist kind also drops that kind back to not-found (the user's choice over leaving the
  two independent). Fully reversible via the existing Undo/History mechanism — no new "Taken out"
  browsing page was built, matching Banish's own precedent (it doesn't have one either). Verified
  live: took out a document, confirmed the real file move on disk, confirmed Undo moved it back.
- **Why Banish itself couldn't be reused:** confirmed by reading it — `_banish_one` hard-requires
  the canonical path to live under `output/archive/`, which is photo/video-only; no document ever
  resolves there. This is a new, parallel mechanism, not a generalization of Banish.

**Sketched, not built: a richer Checklist row.** The user asked how Checklist and Detail view
differ (goal-first/thin-actions vs. document-first/full-toolbar — see the mockup comparison shown
inline this session) and whether Checklist should look more like Detail. Recommendation given:
pull Detail's per-document info (summary/date/kind) and action bar (Star/Note/Move/Gather) into
Checklist's item rows, keeping the grouping-by-kind and classification actions (Confirm/Dismiss/
Reassign) as they are, rather than rebuilding Checklist as Detail cards outright. Not started —
needs the user's go-ahead first.

**New to-do, not started — Emails' significance filter should be exclusive, not cumulative.**
Today picking a level in the Emails significance dropdown (`?min_significance=N`) shows that level
AND EVERY LEVEL ABOVE IT ("N and up") — deliberate, and covered by its own test
(`test_significance_threshold_counts_matches_each_filter_option`). The user wants picking one
level to show ONLY that level (e.g. "Everyday" hides "Personal"/"Emotionally resonant"/"Major life
events" instead of including them). This is a real behavior CHANGE to a tested, deliberate
default, not a bug — before building it, decide whether "and up" should still exist as an option
(a second control?) or whether exclusive fully replaces it, and whether the "N and up" count meter
(`sigmeter`) stays cumulative or also switches to per-bucket. Not investigated further this round.

**A recurring gotcha, worth repeating because it bit again this session:** the user looked for the
Report page's new percentages and didn't see them — port 7766 was still the pinned
`~/wyeast_documents_only` Desktop-launcher copy from before this session even started, which
(a) has none of today's code and (b) runs `--documents-only`, which hides Report entirely. Gave
the user `./family_archive.sh oct7_mf --cases-root /Volumes/oct7_mf_case --port 7767` (no
`--documents-only`) as the fix. If this keeps recurring, the real fix is probably syncing or
re-pinning `~/wyeast_documents_only` itself — ask the user before touching that checkout, it's
intentionally separate.

**Blocked:** nothing on Take-out. The Checklist redesign and the Emails-filter change both need
the user's decision/go-ahead before building.

**Next action:** `cd ~/mac_family_archive && git log --oneline -6 && ./run_tests.sh` before
touching anything; nothing pushed or PR'd yet.

---

### 2026-10-15, later yet — demo-vs-built gap check, by reading code (not trusting the brainstorm memory)

**Why this entry exists:** the user asked for a side-by-side of what the 2026-10-09–14 mockup
canvas (`claude.ai/artifact/TavXkZ66bs5hJ3cXYj2gA1`, both its "TODAY" and "WISHLIST" boards) shows
versus what's actually in this repo today. The front-end brainstorm memory already claimed an
answer to this; it was checked against the real code rather than trusted, and one of its claims
turned out to be wrong (see below) — that memory file has been corrected.

**Built and matching a mockup:** top nav (Documents/Emails/**Messages**/Report), List/Detail
toggle, vital-doc classification confirm ("Yes, that's right" / "Different kind…"), per-document
notes, Move to…/Add to collection…, Report Sections 1–2, and — corrected from this memory's prior
claim — **drag-and-drop between folders IS built** (`docDragStart`/`docDropTarget` in
`report_assets/family/family.js`, examiner-role-gated same as the rest of curation).

**Built but NOT matching any mockup (a local decision, not from the demo):** the "Include emails"
checkbox on Documents, the significance-threshold filter + count meter and Received/Sent tabs on
Emails, the "Flag important" toggle. None of this was wrong to build — the Emails section itself
postdates every mockup (both boards call it "later"/absent) — just worth knowing these aren't
demo-derived if someone goes looking for them on the canvas.

**Confirmed still not built, by reading the code (not by trusting the old note):**
- Report Section 3 ("where the archive isn't sure") — correctly deferred; needs AI question-
  generation the real pipeline doesn't have.
- By-year document arrangement (mockup has a By subject/By year toggle; only "by subject" exists
  here).
- A per-document Vital on/off switch on ordinary documents (don't confuse with the checklist's
  near-miss "Mark as vital"/"Not a vital document" bulk action, which is a different, narrower
  thing scoped to checklist candidates only — that one IS built).
- The "Gather for someone…" helper and its "Handed over" bundle tracking — absent entirely.
- The mockup's ruled/numbered-sheet document-row style — only typography/color were applied.

**A real naming/behavior drift, flagged for a decision:** both mockups ("TODAY" and "WISHLIST"
alike) replaced the star with one three-way **Important / Normal / Less important** control
(decided 2026-10-11) — the real build never made that change and still has a binary ☆ star
(`favorite_curation`) plus a separate significance score driving a different filter. **Resolved
2026-10-15: the user decided to keep the real build's model, not the mockups'.** Richard only
cares about vital/not-vital; a star is its own, separate thing — a PR might star a non-vital
document for sentimental reasons, independent of vital status. No code change — current behavior
already matches. The mockups' single control is superseded, not a gap to close.

Still open, not decided this round: the final 2026-10-14 tab decision said "Texts"; the shipped
code says "Messages". Intentional rename or drift — ask before treating either as correct.

**Blocked:** on the user, for the Messages/Texts naming question only.

**Next action:** none required for the star/vital point (closed). If Messages/Texts should be
reconciled, that's a naming decision, not a bug fix — ask before picking a direction.

---

### 2026-10-15, even later — why ordinary documents carry no date: confirmed upstream, not a bug here

**What this means for the product:** a recipe, a piece of creative writing, an ordinary letter —
anything that isn't a will, trust, tax return, deed, POA, or similar — will never show a date in
this archive, no matter what we build here. The pipeline simply never looked for one. This isn't
new information changing; it's the 2026-10-13 brainstorm note's claim, re-checked from scratch
against this session's live case data (not trusted as written) and found to still hold, with the
scope now pinned down exactly.

**The mechanism:** the pipeline runs a dedicated date-extraction stage (`date_index.json`), but
only for documents it already recognizes as one of ~13 "vital" kinds — will, trust, tax return,
financial statement, power of attorney, deed, and a few others — because the dates there answer a
real legal question (which copy of the will governs). In this case that stage touched 199
documents. The other ~36,800 — every recipe, every ordinary letter, every piece of correspondence
that isn't flagged vital — have no date anywhere in their pipeline record: not in
`case_summary.json`'s `document_classifications`, not in `date_index.json`, nowhere. Confirmed by
reading both files directly for this case, not by trusting a prior note. The front end's "—" is
accurate: `family.js`'s `docDateOf()` only reads a document's `vital[].date_used`, which simply
doesn't exist for a non-vital document.

**The one thing that looked fixable here, and why it isn't (safely):** some ordinary documents
arrived as email attachments — their filename carries a `msgNNNNN_` prefix, and the carrying email
does have a real date. But that number isn't an index we can resolve from this repo (the stage
that assigns it isn't in this closure, and some of the numbers exceed the email list's own
length), and matching by attachment filename instead is unsafe: tested against this case's own
`email_index.json`, a single attachment filename came back shared by three separate emails with
three different dates — not a one-off, real collisions happen. Guessing one would be exactly the
kind of "plausible wrong answer" this codebase already refuses to give elsewhere (see
`delivered_basename_index`'s fail-closed design, which this would have to duplicate correctly to
be safe — showing a date only when exactly one email matches, never a guess among several).

**Not done, needs a decision, not a detour into pipeline work:** this is an upstream pipeline
limitation, not a bug in this repo's consume/export layer — there's no local fix that doesn't
either (a) ask the pipeline to extract dates for far more document kinds than it does today (real
scope increase, not something to build from this side), or (b) add a new, narrower feature here —
show a date only for the email-attachment documents where the email match is unambiguous, labeled
as "received" rather than implied to be the document's own date, since it would otherwise look as
authoritative as a will's execution date. (b) is a real option but is new work and a product
decision (is an approximate "received" date worth showing, and how is it visually distinguished
from a real document date), not something to build without that decision first.

**Blocked:** on the user — whether to leave this as a known, accurate "—", or build (b) above.

**Next action:** none until the user decides; nothing further to investigate here without new
upstream pipeline work.

---

### 2026-10-15, later still — List/Detail highlight fixed; a gotcha about port 7766

**What shipped:** the List/Detail toggle buttons on the Documents page now show which one is
active, live, with no reload needed. Root cause (found last session, fixed this one): the
buttons' "active" attribute was only set once when they were first built; clicking just redrew
the content below them. Fix is in `report_assets/family/family.js`, in the segment-button code
right after the vital-docs checklist branch (search for `segButtons`) — the click handler now
updates both buttons' state, not just the layout variable. Verified by hand in a browser: clicked
each button both directions, confirmed the highlight moves immediately and matches the rendered
view (table rows for List, cards for Detail).

**A gotcha worth knowing before trusting anything on port 7766:** whatever is already listening
there (`lsof -nP -iTCP:7766 -sTCP:LISTEN`) may not be running this checkout's code at all. The
Desktop launcher (`~/Desktop/oct7 Documents.command`, described at the top of this project's
global instructions) starts a *pinned copy* of the archive in `~/wyeast_documents_only` — a
separate checkout, not this repo. Edits here do not reach it, and it will not show your changes
no matter how many times you restart it — because you're not restarting it, someone else's copy
is already running. If a fix doesn't show up in the browser after confirming the test server has
the new code (`fetch` the asset and grep it, as done this session), check which checkout the
listening process actually launched from (`ps -p <pid> -o command` on the pid `lsof` names) before
assuming the bug is still there. To test safely without disturbing that pinned instance, run this
repo's own server on a different port: `./family_archive.sh oct7_mf --cases-root
/Volumes/oct7_mf_case --documents-only --port <other>`.

**Blocked:** nothing.

**Next action:** the undated-ordinary-documents question below is still open and untouched this
round — pick that up next.

---

### 2026-10-15, end of session — handoff: dates on ordinary documents, a List/Detail bug, demo work to reference

**Where this session's work landed:** three commits on `documents-view`, nothing pushed, no PR
yet. `git log --oneline -5` from this branch for the exact set — the two entries directly below
this one describe each in plain language (top nav/Report/navy look + the Emails rebuild, then the
checklist-jump fix).

**New to-do, not started: why do ordinary (non-vital) documents carry no dates?**
Raised by the user this session, using the "recipe" folder as the concrete example — nothing in it
shows a date. Per the 2026-10-13 front-end brainstorm note (`memory/wyeast-frontend-brainstorm.md`),
as of that check against upstream main, only vital documents, photos, emails and texts carry dates
from the pipeline; ordinary documents get none, and categories fold unknowns into "miscellaneous."
That note is now two days old and was **never re-verified against current main** — treat it as a
lead, not an answer. Next session: re-check from scratch (`grep -rn "date_index" wyeast/ tools/` is
a reasonable start), and find out whether this is a gap in the upstream pipeline or something
fixable in this repo's own export/consume layer before proposing a fix.

**New to-do, not started: the List/Detail toggle buttons don't show which one is active.**
Root cause already found (not fixed): `report_assets/family/family.js`, the `.seg` buttons built
around `[["list","List"],["detail","Detail"]].forEach(...)` (search for that literal) set each
button's `aria-pressed` — which drives the dark-blue "active" styling — only once, when the
buttons are first built. Clicking either button updates the `layout` variable and calls
`drawBody()` to redraw the content, but never rebuilds the `seg` control itself, so the attribute
never updates again. Detail view itself works correctly; only the button's own highlight is stuck
on List. Fix: update both buttons' `aria-pressed` (or rebuild `seg`) inside the `onclick` handler.

**Demo/brainstorm work to refer to before touching the front end, not yet (all) applied:**
- `memory/wyeast-frontend-brainstorm.md` — the full decision history behind the current
  Documents/Emails/Messages/Report top nav, the Report page's three-section design, and the
  "law office navy" look.
- The mockup canvas itself: `claude.ai/artifact/TavXkZ66bs5hJ3cXYj2gA1` — read it with the
  Artifact tool, list its files, and read `project/Navy.dc.html` / `project/Documents.dc.html`
  directly for the actual CSS/markup — the memory note is a summary, not a substitute.
- **Specifically not yet built, so nobody re-derives it from scratch:** the mockup's "ruled
  numbered sheet" document-row treatment (a pink margin line + numbered rows, legal-pad style) —
  only the typography/color/top-bar pieces of the look were applied, not this. And the Report
  page's Section 3 ("where the archive isn't sure") — needs a real question-generation feature
  that doesn't exist anywhere in the pipeline; the mockup used invented example documents for it,
  so don't build it from vibes if asked for "the rest of the Report."

**Blocked:** nothing.

**Next action:** `cd ~/mac_family_archive && git log --oneline -5 && ./run_tests.sh` before
touching anything.

---

### 2026-10-15, later — Top nav, inbox redesign, Report page, "law office navy" look

**What shipped (on branch `documents-view`, not yet committed — see Next action)**
- Left sidebar replaced with a top nav bar, scoped to **Documents · Emails · Messages · Report**
  — matching the 2026-10-09/14 front-end brainstorm's decided design exactly (see
  `memory/wyeast-frontend-brainstorm.md` and the mockup canvas it links,
  `claude.ai/artifact/TavXkZ66bs5hJ3cXYj2gA1`). Every other existing page (Photos, People,
  Collections, Review queue, ...) is still fully functional at its own URL — only the *nav*
  changed, nothing was removed.
- Emails list rebuilt as a compact single-line inbox (from / subject / date), matching a
  typical mail client. Dropped the old significance-banded grouping and "Most significant"
  sort — decided unreliable for now (see below) — replaced with clickable From/Subject/Date
  column headers (`?sort=&dir=`, toggles like Mail.app/Outlook).
- **Received / Sent tabs**: a thread shows under Received if any message came from someone
  else, Sent if any came from the owner — both, for a real back-and-forth (Gmail's model).
  Needs `owner_addresses` set via the page's own settings form; the tabs don't render until
  it is (no silent wrong split).
- **Significance threshold filter + count meter**: decided to keep using the pipeline's score
  for *filtering* (a "this level and up" dropdown) even though it's been pulled from
  sort/grouping as unverified — these are independent decisions, not a contradiction. A bar
  per level shows the count each option would yield, given whatever else is filtered.
- **Report page** (top-nav tab), Sections 1-2 only: "what's here" (folder counts + vital
  documents found) and "what wasn't found" (the vital-doc checklist's misses, grouped the
  same way the Documents tree already groups them). Section 3 ("where the archive isn't
  sure") is NOT built — it needs an AI-question-generation feature that doesn't exist in the
  real pipeline; the mockup that proposed it used invented example documents. Don't build it
  from vibes if asked for "the rest of the Report" — it needs a real design decision first.
- **"Law office navy" look** applied app-wide: Source Serif 4 (headings) + Source Sans 3
  (body), vendored locally (see `report_assets/fonts/source-serif-4/`,
  `source-sans-3/` — same no-CDN pattern as the existing Fraunces/Inter/IBM Plex Mono, air-
  gapped-safe), navy `#1f3a5f` as the one accent, double-ruled top bar. The "ruled numbered
  sheet" document-row treatment from the mockup (pink margin line + numbered rows, legal-pad
  style) was **not** applied — only the typography/color/top-bar pieces. Still the SAME
  `data-theme="heirloom"` key every page uses; only the palette under that key changed
  (atlas/gallery themes untouched, still unused by any page).

**A real bug caught and fixed during this session, worth knowing about:** the Python backend
(`tools/family_archive.py`, `tools/_archive_data.py`) only loads once when the preview server
starts — editing those files does NOT hot-reload into a running process, unlike the JS/CSS,
which ARE re-read from disk on every request. Twice this session a backend change looked like
it "did nothing" in the browser until the server was restarted. **If a backend change doesn't
seem to take effect, restart the preview server before assuming it's a bug.**

**Blocked:** nothing.

**Known issues not yet filed**
- Demote (examiner's "remove from top of the sort") still writes `email_demoted` and the
  Restore button still works, but since no remaining Emails sort is significance-based, it no
  longer visibly moves anything. Not fixed — flagged to the user, no decision made yet on
  whether to remove the button or leave it as a quiet audit action.
- To-do raised by the user, not yet investigated: **why do ordinary (non-vital) documents —
  e.g. the "recipe" folder — carry no dates at all?** As of the 2026-10-13 brainstorm's check
  against upstream main, only vital documents, photos, emails and texts get dates from the
  pipeline; this wasn't re-verified against current main. To check freshly: look at what
  `wyeast/core/` or the pipeline's date_index actually covers today, not what this note says.
- The Report page's folder-count links (`/documents?cat=X`) assume the raw category key
  reads fine through `pretty()` for display; not checked against every category name that
  exists across real cases, only `oct7_mf`'s.

**Next action:** `cd ~/mac_family_archive && git diff --stat` to see the full change, then
decide whether to commit — nothing from this round is committed yet.

---

### 2026-10-15 — Emails get their own view; Documents can include them by topic

**What shipped (on branch `documents-view`, not yet committed — see Next action)**
- Documents view: an "Include emails" checkbox folds email-sourced categories into the
  topic tree (counts) and, inside one open folder, lists the matching threads in their own
  "From the emails" section below the regular file table. Off by default; nothing changes
  for anyone who doesn't touch the checkbox. `tools/_archive_data.py`:
  `email_category_counts`/`merge_email_category_counts`/`email_rows_for_category`.
- Emails view: a "Flag important" toggle, visible and usable by **both** family and
  examiner (every other curation action — star, note, collection — is still examiner-only;
  this is the first exception, on purpose — see `verb_important_email`'s docstring for why).
  Plus a "Has attachment" filter (an attachment that actually resolved to something the
  pipeline delivered, not just a raw .eml attachment) and a "Sender (A–Z)" sort, which needs
  a new small settings form ("Whose email is this?") because nothing in the pipeline's
  existing data says which address is the account owner's own — see the next item.
- New case-level setting, `owner_addresses` (`family_decisions.json`), settable by either
  role via the Emails page form. Without it, sender-sort is a no-op (every row's
  `correspondent` is `None` — never a guess).

**A real, pre-existing behavior this surfaced (not a new bug, not yet acted on)**
Both new family-writable actions (important-flag, owner-addresses) write to
`family_decisions.json` / `curation_layer.json`. Those two files are explicitly part of the
release fingerprint (`wyeast/core/release.py` — "serve-gating metadata"), so **any** write to
them — by either role — makes the next `release_status()` check see "changed since release"
and pause family delivery until an examiner re-signs. This already applied to every
examiner-only curation verb (star a photo after signing → same pause); flagging-by-family
just gives a second way to trigger a pre-existing mechanism, not a new one. It doesn't affect
today's actual usage — the desktop launcher (`oct7 Documents.command`) runs `--role examiner`
with no `--role family` flag, and examiner is never subject to this gate (confirmed: the
`do_GET` check is `if CASE.role == "family"`, and examiner sees an informational banner, not
a block). Decided (2026-10-15): ship as built; revisit the fingerprint's scope only once an
actual `--role family` session is in real use for real family members — there's no file or
flag that records that, so the way to find out is to ask.

**Verified in a browser** (a throwaway signed case, not `oct7_mf` — see
`tests/unit/_case_fixture.py::make_case` for the pattern): Documents "Include emails" folder
counts and the "From the emails" row list, both filters, the sort, the settings form, and
the important toggle in both the list and thread-detail view, under both roles.

**Blocked:** nothing.

**Known issues not yet filed**
- No per-person attribution on the important flag — only "family" or "examiner" is recorded
  (decided: acceptable, see conversation; `curation_layer.json`'s `important` entries carry
  `actor_role`, not a name).
- The Documents-view email merge only applies to plain category browsing — the vital-doc
  checklist and curation collections are untouched (those already have their own, separate
  email linking via `_vital_thread_links`).

**Next action:** `cd ~/mac_family_archive && git diff --stat` to see the full change (six
files, all in `tools/`, `report_assets/family/`, and `tests/`), then decide whether to commit
and open a PR — nothing has been committed yet.

---

### 2026-10-16 — date_index.json contract written down for the front end

**What changed**
- `docs/date_index_contract.md` describes what Wyeast's `date_index` stage writes, with synthetic
  examples: `items[].date_used` and its `basis` values, the ranked `operative_views` (wills, POAs,
  trusts, beneficiary forms) and the new tier 2 `account_views` (statements grouped by account).
  Only `date_used` is displayed here today, and only to the examiner. The two views have no UI yet.

**To refresh a case's dates** (the pipeline is not here): re-run `date_index` in Wyeast and copy
`output/metadata/date_index.json` and `vital_doc_provenance.json` into the case. Whether a case
has tier 2 data: `python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('tier'))" <case>/output/metadata/date_index.json`

**Blocked:** nothing.

**Next action:** decide whether the family role sees the ranked views before building them.

---

### 2026-10-14 — CI no longer fails on edits to carried files

**What changed**
- `.github/scripts/check_export.py` used to fail the build whenever a carried file differed
  from the hash recorded in `.wyeast-export.json`. Now that work happens here, that is the normal
  state, so drift is reported as `::warning::` annotations on the PR instead. The footprint check
  (no third-party import beyond pillow/pillow_heif) still fails the build.

**Nothing here flows back to Wyeast.** Export is one-way (Wyeast → here). There is no tool that
carries edits made here upstream; landing them in Wyeast means porting by hand against the
commit in `.wyeast-export.json` (`source_commit`). The drift warnings are that porting list. To
see it locally: `python3 .github/scripts/check_export.py`

**Blocked:** nothing.

**Next action:** as below — `git fetch origin && git status` before starting anything.

---

### 2026-10-14 — this repo became the home

**What changed**
- Work now happens off `WyeastCorp/mac_family_archive` only. The marklandf-lab fork
  (`marklandf-lab/marklands_family_archive`) and the experimental `markland_oct_front_end`
  are retired. Nothing was deleted; both remain readable on GitHub.
- `/ship` now runs the PII scan before committing (step 2), and `CLAUDE.md` carries the
  "never commit PII" and "verify in a browser" rules the fork had.

**All work happens directly in this repo, front end included.** Program files here (`tools/`,
`wyeast/`, `report_assets/`, `config/`, `tests/`) were exported from the private
`WyeastCorp/Wyeast` repo until now. Wyeast's export script refuses to overwrite files edited
here, and `--force` would wipe them — **never run it with `--force`**, and warn before running
an export at all. To see which files an export would touch:
`gh api repos/WyeastCorp/Wyeast/contents/ops/family_archive_closure.py --jq .content | base64 -d`

**The fork's UI work is not here.** Breadcrumbs, the Reports section, Document Photos, the
Correspondents list, the email cuts and more were built on the fork between 26 Aug and 3 Sep 2026
and never reached WyeastCorp. To see the list:
`git log --no-merges --oneline origin/main..marklandf/main` (a local checkout needs a
`marklandf` remote for the fork). The fork's own `STATE.md` and `BACKEND.md` (the list of
problems only the pipeline can fix) are there too. Port a piece only when asked — the
Documents view here overlaps several of them.

**Blocked:** nothing.

**Known issues not yet filed**
- Case `oct7_mf` has only `doc_classifications_partial.json` in `output/metadata/`, no complete
  classification file. Whether its document sort is unfinished has not been checked. To look:
  `ls <cases-root>/oct7_mf/output/metadata/ | grep -i classif`
- There is no `/walk` skill in this repo (the fork had one, written for the fork's UI). Browser
  checks are by hand until one is written for this UI.

**Next action:** `cd ~/mac_family_archive && git fetch origin && git status` — confirm the
checkout tracks `WyeastCorp/mac_family_archive` before starting anything.
