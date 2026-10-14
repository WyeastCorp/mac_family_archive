#!/usr/bin/env bash
# sync_from_wyeast.sh — re-copy the Family Archive import closure from a Wyeast
# checkout and re-apply this repo's local modifications.
#
#   ./sync_from_wyeast.sh /path/to/Wyeast [--force]
#
# Hands off to Wyeast's own ops/export_family_archive.sh, which owns the file
# list, the local modifications (including the Mac-only feature patches kept in
# Wyeast's ops/family_archive_patches/), the downstream-edit audit and the
# .wyeast-export.json provenance. This script used to copy a hand-kept file list
# and patch it itself; that list went stale, and it could not apply the feature
# patches, so a sync through it silently reverted them.
#
# Afterwards: review `git diff`, run ./run_tests.sh, commit.

set -euo pipefail
_HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="${1:-}"
if [[ -z "$SRC" || ! -x "$SRC/ops/export_family_archive.sh" ]]; then
  echo "usage: $0 /path/to/Wyeast [--force]   (a checkout with ops/export_family_archive.sh)" >&2
  exit 1
fi
shift
exec "$SRC/ops/export_family_archive.sh" "$_HERE" "$@"
