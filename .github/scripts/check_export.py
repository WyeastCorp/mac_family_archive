#!/usr/bin/env python3
"""CI guard for the mirror: footprint + export integrity. Stdlib only.

1. Third-party imports anywhere in tools/ wyeast/ must stay within the Mac's
   two-package footprint (pillow, pillow_heif); jsonschema is the one lazy,
   optional import and is deliberately not installed here.
2. Every file in .wyeast-export.json is compared with the hash the last export
   recorded. A mismatch is a local edit to a carried file. That used to fail
   the build, back when this repo was a mirror and every fix belonged upstream.
   Since 2026-10-14 work happens here (see CLAUDE.md), so a mismatch is the
   normal state of a carried file someone worked on. It is reported as a
   warning, not a failure: the list is still worth seeing, because it is
   exactly what Wyeast's export would refuse to overwrite (or, with --force,
   wipe), and what would have to be ported by hand to land the work upstream.
   Only the footprint check fails the build.
"""
import ast
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ALLOWED = {"PIL", "pillow_heif", "jsonschema"}
LOCAL = {"wyeast", "tools"}

bad = []
for py in sorted(p for d in ("tools", "wyeast") for p in (ROOT / d).rglob("*.py")):
    for node in ast.walk(ast.parse(py.read_text(encoding="utf-8"))):
        names = ([a.name for a in node.names] if isinstance(node, ast.Import)
                 else [node.module] if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module
                 else [])
        for n in names:
            top = n.split(".")[0]
            if top not in sys.stdlib_module_names and top not in LOCAL and top not in ALLOWED:
                # _local siblings imported as bare modules (tools/ is on sys.path)
                if (ROOT / "tools" / (top + ".py")).exists():
                    continue
                bad.append("%s imports third-party %r" % (py.relative_to(ROOT), top))

manifest = json.loads((ROOT / ".wyeast-export.json").read_text())
drift = []
for rel, want in sorted(manifest["files"].items()):
    f = ROOT / rel
    got = hashlib.sha256(f.read_bytes()).hexdigest() if f.is_file() else "MISSING"
    if got != want:
        drift.append((rel, "missing" if got == "MISSING" else "edited locally"))

# ::warning:: is a GitHub Actions annotation: it shows on the PR without
# failing the job. Outside Actions it is just a readable prefix.
for rel, how in drift:
    print("::warning file=%s::%s differs from Wyeast export %s (%s); an export would refuse "
          "to overwrite it, and --force would wipe it" % (rel, rel, manifest["source_commit"][:7], how))

if bad:
    print("\n".join(bad))
    sys.exit(1)
print("footprint OK; %d of %d carried files match export %s, %d changed here"
      % (len(manifest["files"]) - len(drift), len(manifest["files"]), manifest["source_commit"][:7], len(drift)))
