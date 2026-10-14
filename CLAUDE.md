# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
./setup.sh --dev                  # private .venv + pillow/pillow_heif + pytest
./run_tests.sh                    # whole suite (pytest under .venv)
./run_tests.sh tests/unit/test_rebase.py -q          # one file
./run_tests.sh tests/unit/test_rebase.py::test_name  # one test
./family_archive.sh CASE_ID --cases-root /path/to/cases   # serve, then open http://127.0.0.1:7766/
./sync_from_wyeast.sh /path/to/Wyeast                # DO NOT RUN without reading "The operating constraint" below
```

`$WYEAST_PYTHON` overrides the interpreter; `$WYEAST_CASES_ROOT` the cases root.
There is no linter or formatter configured — pytest is the only check.

Exit codes: `0` served · `1` bad args / missing case · `2` case not complete · `3` family view blocked.

**Read `STATE.md` first.** It is the session-handoff doc: what shipped, what is blocked and on
whom, known issues not yet filed, and the one command to start the next session with. Newest entry
at the top. Keep it current when shipping, inside the feature branch. Like this file, it is not part
of the export, so a sync leaves it alone.

## The operating constraint: this was a mirror; it is now the source

**As of 2026-10-14 all work happens directly in this repo, front end included.** The rest of this
section describes how the program files got here, and still matters for one reason: Wyeast's
`ops/export_family_archive.sh` (also run by `./sync_from_wyeast.sh`) would replace them. It refuses to overwrite a file edited here
unless given `--force`, and with `--force` it wipes that work. **Never run an export with
`--force`**, and warn the user before running one at all. Edit the files here; do not route
changes through Wyeast's `ops/family_archive_patches/` unless the user asks.

History:

Everything under `tools/`, `wyeast/`, `report_assets/`, `config/` and `tests/` is **copied from
WyeastCorp/Wyeast** — the complete import closure of `tools/family_archive.py`, derived by walking
the AST. Read `UPSTREAM.md` before editing any of it. Fixes to the archive itself belong upstream
and flow here via `sync_from_wyeast.sh`, which re-copies the closure and re-applies a short list of
local modifications. Local edits that aren't on that list get silently reverted on the next sync.
Mac-only features (the Documents folder-tree view and `--documents-only`) are on that list as
patches kept upstream in Wyeast's `ops/family_archive_patches/`. They were changed there until
2026-10-14; they are now changed here (see the top of this section).

The pipeline that *produces* a case (`wyeast/stages/`, orchestration, the stage registry) is **not
here**. A Mac only ever consumes a case that is already finished.

`config/pipeline_config.json` is byte-identical to Zone B's, which is why `paths.cases` still says
`/data/cases`. `family_archive.sh` always supplies `--cases-root` to compensate. Do not "fix" the
config.

`wyeast/core/` must stay **stdlib-pure** — those modules are imported by pipeline stages running
under six different venvs upstream, so a third-party import breaks them at case time.
`tests/unit/test_audience.py::test_audience_is_stdlib_pure` enforces this for `audience.py` with an
import whitelist; honor it for the other core modules too. When a core module needs behavior from
outside its whitelist, inject it (see `audience.install_index_loader`) rather than importing.

## Architecture

### One data layer, two front doors

`tools/_archive_data.py` holds **pure builders** — no argparse, no import side effects — that turn
the pipeline's `output/metadata/*.json` indexes into per-section data structures. Role-gating and
field selection live there so both front doors share them. `tools/family_archive.py` is the
stdlib-only HTTP server on 127.0.0.1 that serves those structures, renders media inline, and applies
verbs. (The other front door, `build_explorer.py`, is upstream-only and not in this closure.)

Verbs are plain functions over an `ArchiveCase`, so almost everything is testable without a socket.

### Absolute paths are the id space

The pipeline records **absolute workstation paths** in every index. Those strings are not just
locations — they are identity: `archive_map` is keyed by them, `document_classifications` names
them, `ocr_index` joins on them, and the UI round-trips them back as `?src=`.

`--cases-root` only decides where the case *folder* is (`CasePaths.from_case_id`). It does nothing
to the paths *inside* the indexes. Correcting those is `wyeast/core/rebase.py`'s job — read its
module docstring before touching anything path-related. Two rules it establishes:

- **In memory, every path is local.** That is what lets the existence checks, resolvers, OCR joins
  and search index work without each of them knowing the case moved.
- **On disk, the case's own files stay in recorded form** — decision sidecars and the audit log are
  converted back on write, so a later move rebases them instead of orphaning them.

Both readers of a case index (`_archive_data.load_json` and `wyeast/core/audience`) share one
registry in `rebase.py`. They **join on path** — a thread names the message files whose bodies
`email_index.json` carries — so wiring one and not the other empties the join with no error
anywhere. `install_rebaser` wires both together for that reason.

Case tree (`wyeast/core/paths.py`): `original_files/`, `extracted/`, `quarantine/`, `duplicates/`,
`logs_<case_id>/`, and `output/{archive,metadata,suspense,...}`. A *delivery* carries only
`output/` — so index paths under `extracted/` have nothing to rebase onto, and documents/audio are
matched to their delivered copies under `output/<kind>/<category>/` by filename.

### Two audiences, asymmetric failure

`wyeast/core/audience.py` is the one place that decides who may see an item; its header explains the
whole model and is worth reading in full. The core asymmetry: a forgotten check on the **examiner**
side fails closed (they miss evidence, a human notices); on the **family** side it fails open
(unscreened material reaches a grieving family). So the default audience is `family`, and no caller
ever types an index filename — the module owns every path so a reader physically cannot open the
wrong audience's file by habit.

Several indexes are **role-scoped on disk** (`email_threads_index_{family,examiner}.json`,
correspondent cards). Pick them through `audience.py` helpers, never by concatenating a name.

### The security surfaces

- `resolve_media_path` is the single gate for serving bytes. For the family role it is an
  **allow-list** of delivered/working roots (`family_media_roots`) plus a delivered-set check —
  deliberately an allow-list, because a deny-list silently leaks every tree nobody remembered to
  forbid. Note `_media` swallows its `VerbError` and retries through dup-member then quarantine
  resolvers, so **the error text reaching the browser is the last resolver's, not the real one**.
- **E5**: the family GET surface is default-closed. Only page shells, `/assets/*` and the status
  endpoint answer on an unreleased case; every body (`/media`, `/thumb`, all other `/api/*`) is
  gated. Allow-list the shell, gate everything else — never enumerate body routes.
- **E3**: family startup distinguishes absent (legacy_unsigned, start closed) from
  present-but-invalid (refuse). `wyeast/core/release.py` explains the fingerprint-vs-stamp split.
- Every GET and POST passes an Origin/Host check — the server binds loopback, but a hostile page can
  rebind its own hostname to 127.0.0.1 and read the whole estate.

### Never destroy; overlay instead

Verbs never edit a pipeline-authored index. Examiner decisions land in `family_decisions.json` as
**overlays** (`doc_placements`, `person_merges`, `face_assignments`, `junk_rescued`,
`scanned_released`, `vital_doc_dismissed`, …) applied at render time; `curation_layer.json` is a
similar additive sidecar for favorites/collections/notes. Banish moves bytes to
`output/family_banished/`, it does not unlink. Grep for "never-destroy" and "DECISIONS OVERLAY"
before adding a verb.

Every verb appends a line to `output/metadata/family_actions.ndjson` (History view, with Undo);
byte-level moves also go through the move ledger and chain of custody. POST verbs are serialized
under `CASE._lock`; the process holds a cross-process lock file for the decision sidecars.

### Loading and caching

`ArchiveCase.load()` rebuilds all index state and publishes it as a **single atomic reference swap**,
so a concurrent reader sees either the whole old generation or the whole new one — index attributes
come out of that dict via `__getattr__`. Derived work is memoized per generation with
`_state_cached`. The heavy indexes (`email_index.json`, per-conversation JSONs) are loaded lazily
behind their own locks, with a bounded LRU, because they run to hundreds of megabytes. The FTS5
index builds off-thread on first search and self-heals when its stored signature goes stale.

Large sections return a `{rows, total, offset, limit}` envelope so a capped view is never presented
as complete.

## Conventions worth matching

- **Fail closed on ambiguity.** A basename that collides across delivered items yields no link
  rather than a possibly-wrong one (`delivered_basename_index`, and the relocation map in
  `rebase.py`). Prefer an honest 404 to a plausible wrong answer.
- Comments here carry the *why*, often at length, including the bug that motivated the code. Match
  that density when touching security gates or path handling — a terse patch there reads as a
  regression to the next person.
- Tests build a real case tree on disk via `tests/unit/_case_fixture.py::make_case` (lifted from an
  upstream module outside this closure). Extend the fixture rather than mocking the filesystem.

## Known drift

`UPSTREAM.md` states that nothing in `wyeast/core/` is modified. That is **no longer true**:
`wyeast/core/rebase.py` was added and `wyeast/core/audience.py` gained an injectable index loader,
to make a delivered case servable off the workstation. Both belong upstream. Update `UPSTREAM.md`'s
local-modifications list, and check `sync_from_wyeast.sh` re-applies them, before the next sync —
otherwise a sync silently reverts the fix.

## macOS caveats that bite

APFS is case-insensitive by default and normalizes filenames to NFD, while the pipeline ran on
case-sensitive Linux storing NFC. Two delivered files differing only in case collide on copy; accented
filenames matched between a directory scan and an index JSON can mismatch. Apple's system `python3`
has historically shipped without SQLite FTS5 (breaks Search), and without `pillow_heif` iPhone
thumbnails fail **silently blank rather than erroring** — `setup.sh` checks both.

## Verify in a browser

A green `./run_tests.sh` says nothing about the family-facing UI. Navigation defects are
structurally invisible to pytest: every function returns what it promises, and the failure exists
only in the sequence of clicks. Drive the real app at `http://127.0.0.1:7766` after any change that
reaches `report_assets/family/`. **Clicking writes real decisions to the real case** (confirmations,
moves, banishes all persist and are audited in `output/metadata/family_actions.ndjson`), so a count
that moved is more often a click than a bug.

## What must never enter a commit

**Never post user data or PII. Warn the user if any personally identifying data will be
included in the repo.** Warn — do not quietly scrub and carry on. It is the user's data,
the user's repo and the user's call; the job is to make sure they are the one making it,
with the specific strings in front of them.

The case tree is not the risk. It lives outside the checkout (`~/WyeastCases`, or a mounted drive
image), `.gitignore` blocks `/cases/`, and nothing case-shaped is tracked — so "will my data be
committed?" has a reassuring answer, and it is the wrong question.

The leak path that actually bites is **quotation**: real names, phone numbers, email addresses
and document titles copied out of a live case into a code comment, a commit message, a PR body,
or a doc, to illustrate the bug being fixed. That material is not in `.gitignore`'s reach, and on
a public repo it is permanent — a later commit that deletes the line leaves it readable in history
forever. It has happened here before: `report_assets/family/family.js` once carried real contacts
of the deceased, with live mobile numbers, in an explanatory comment.

So, when writing a comment, a commit message, a PR body or a doc in this repo:

- **Never paste from the live case.** Use invented stand-ins — Alex Rendon, `+15035550178`,
  `a.rendon@example.com`. `555-01xx` numbers are reserved for fiction precisely for this.
- That covers **names, phone numbers, email addresses, street addresses, account numbers, and
  document titles** that identify a real person or a real instrument. "A divorce judgment filed
  under court_filing" is fine; the filename and the parties are not.
- A case id (`813_mf`, `oct7_mf`) is fine on its own — it names a case, not a person.
- **Check before pushing, not after.** `/ship` step 2 scans the outgoing range. If something turns
  up, rebuild the branch so the string never enters a commit — a scrub commit on top does not
  remove it from history.
