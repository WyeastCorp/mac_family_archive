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
