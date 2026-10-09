#!/usr/bin/env python3
"""CI guard for the mirror: footprint + export integrity. Stdlib only.

1. Third-party imports anywhere in tools/ wyeast/ must stay within the Mac's
   two-package footprint (pillow, pillow_heif); jsonschema is the one lazy,
   optional import and is deliberately not installed here.
2. Every file in .wyeast-export.json must still hash to what the last export
   recorded. A mismatch is a local edit to a carried file, which the next
   sync_from_wyeast.sh would silently revert - land it upstream instead.
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
for rel, want in sorted(manifest["files"].items()):
    f = ROOT / rel
    got = hashlib.sha256(f.read_bytes()).hexdigest() if f.is_file() else "MISSING"
    if got != want:
        bad.append("%s differs from the recorded export (%s)" % (rel, "missing" if got == "MISSING" else "edited locally"))

if bad:
    print("\n".join(bad))
    sys.exit(1)
print("footprint OK; %d carried files match export %s" % (len(manifest["files"]), manifest["source_commit"][:7]))
