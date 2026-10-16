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

### 2026-10-15, latest — Report percentages; Gather-for-someone built end to end

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
