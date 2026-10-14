# Upstream provenance

Everything under `tools/`, `wyeast/`, `report_assets/`, `config/` and `tests/` in
this repo is copied from **WyeastCorp/Wyeast**, not written here.

| | |
|---|---|
| Source repo | https://github.com/WyeastCorp/Wyeast |
| Source commit | `a290b7ee58e796dfb0a8e07d39032bfb224730c0` (`a290b7e`) |
| Spec | [`docs/specs/family-archive-macos-standalone.md`](https://github.com/WyeastCorp/Wyeast/blob/main/docs/specs/family-archive-macos-standalone.md) |
| Phase | Phase 0 — de-risk (terminal launch, no `.app`, no signing) |

## What was copied

The **complete import closure** of `tools/family_archive.py`, derived by walking
the AST of every module reachable from it (including imports made lazily inside
functions), not by hand:

```
tools/family_archive.py      the server
tools/_archive_data.py       view/data builders
tools/build_fts.py           SQLite FTS5 index (imported at module load)
tools/export_delivery.py     Export verb (lazy import)
tools/gen_email_threads.py   threaded conversation view (lazy import)

wyeast/core/{audience,config,custody,delivery,errors,filetypes,
             io,media,moves,paths,release,safe_names}.py
```

Plus `report_assets/` (CSS/JS/fonts/Leaflet served at `/assets/*`) and the two
config files the closure reads through `wyeast.core.config.config_dir()`.

The spec listed 9 `wyeast.core` modules; the AST walk found **12** — it also
pulls `errors`, `safe_names` (via `delivery`/`paths`) and `filetypes` (via
`media`) — plus `tools/gen_email_threads.py`, which the spec's list omitted.
Everything the walk found is here.

## What was deliberately left behind

- `requirements/venv-phase1.txt` — the ~15 GB torch/CUDA/scikit-learn stack.
  Nothing in the closure imports any of it, and several of those wheels have no
  macOS build at all. See `requirements.txt` for the real footprint.
- `jsonschema` — reachable, but only through `wyeast.core.io`'s *lazy, optional*
  validation path. No call site in this closure passes a schema. Its absence
  is a documented no-op, and the test suite passes without it.
- `wyeast/stages/`, `orchestration/`, `ops/`, the registry — the pipeline that
  *produces* a case. A Mac only ever consumes a finished one.

## Local modifications to copied files

Re-applied by every sync (Wyeast's `ops/export_family_archive.sh`; the roster is
`LOCAL_MODS` in Wyeast's `ops/family_archive_closure.py`):

1. `tools/family_archive.py`, `tools/export_delivery.py` — shebang changed from
   `#!/opt/estate-pipeline/envs/venv-phase1/bin/python3` to
   `#!/usr/bin/env python3`. (Both are run via `python3 -m`, so this is
   cosmetic, but a Zone-B-literal path in a Mac repo is a trap.)
2. `tests/unit/_case_fixture.py` — upstream loads its `make_case` fixture out of
   `tests/unit/test_build_explorer.py` by path. That module tests
   `tools/build_explorer.py`, which is outside the closure, so `make_case` is
   lifted verbatim into this file.
3. `tests/unit/test_family_archive.py`, `tests/unit/test_rebase.py` — the
   `make_case` loader block imports it from `_case_fixture` instead.
4. `tests/unit/test_safe_names.py` — dropped `test_safe_album_dirname_delegates`,
   which asserts delegation from `wyeast.stages.llm_synthesis` (not carried).
5. `tests/unit/test_config.py` — not carried; it imports
   `wyeast.core.registry`, the pipeline stage table.
6. **Mac-only features**, applied as patches kept upstream in Wyeast's
   `ops/family_archive_patches/`. Wyeast's own copy does not have them.
   - `documents-view.patch` — the Documents page as a folder tree (vital kinds,
     categories, collections) with List/Detail views, drag-to-file, an undo
     banner and document fields in the viewer; and the `--documents-only`
     server mode (Documents alone, no section rail). Touches
     `tools/family_archive.py`, `tools/_archive_data.py`,
     `report_assets/family/family.{js,css}` and `tests/unit/test_family_archive.py`.

   To change a Mac-only feature, change its patch in Wyeast (the runbook, §9d,
   says how) and re-sync. An edit made here instead is flagged by CI's
   export-integrity guard and refused by the next sync.

Nothing in `wyeast/core/` is modified. It is byte-identical to upstream,
including the now-dead `DEFAULT_SCRIPTS_DIR = Path("/opt/estate-pipeline/app")`
constant — left alone precisely so the files stay diffable.

`config/pipeline_config.json` is also byte-identical to Zone B's. The closure
reads only `paths`, `transcribe.deliver` and `sensitive_scan.sensitivity_filters`
out of it; the rest (LLM prompts, GPU model paths, stage tuning) is inert here
and kept only so re-syncing is a straight copy. Note `paths.cases` still points
at Zone B's `/data/cases`, which is why `family_archive.sh` always supplies
`--cases-root`.

## Re-syncing

`./sync_from_wyeast.sh /path/to/Wyeast` runs Wyeast's
`ops/export_family_archive.sh` against this checkout: it re-copies the closure,
re-applies modifications 1–6 above and records `.wyeast-export.json`. Run
`./run_tests.sh` afterwards.
