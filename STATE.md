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
