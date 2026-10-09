import contextlib
import importlib.util
import sys
from pathlib import Path

import pytest

# The repo root is the scripts directory: step scripts get it on sys.path[0]
# when run directly. Tests need the same so `wyeast` (incl. wyeast.embed and
# wyeast.core.io) imports identically to production.
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))



def pytest_configure(config):
    config.addinivalue_line(
        "markers", "real_openjev_lease: test exercises the real openjev_lease "
        "(it mocks the processes itself); skips the _no_real_openjev guard")


@pytest.fixture(autouse=True)
def _no_real_openjev(request, monkeypatch):
    """System One ships enabled for vital_doc_confirm and sensitive_scan, so a
    stage test on the real config would otherwise start the real openjev server
    (evicting Ollama from the GPU). Every test sees the lease fail as if openjev
    were not installed, which is the stage's loud fall-back-to-production path;
    tests of the engine itself replace `openjev_lease` with their own fake.

    This conftest is carried to the macOS port, whose closure does not include
    wyeast.core.openjev. monkeypatch.setattr on a dotted path imports the module,
    so the fixture is a no-op when the module is absent (nothing to guard)."""
    if request.node.get_closest_marker("real_openjev_lease"):
        return
    if importlib.util.find_spec("wyeast.core.openjev") is None:
        return

    @contextlib.contextmanager
    def _unavailable(*_a, **_kw):
        raise sys.modules["wyeast.core.openjev"].OpenjevError(
            "openjev disabled under tests (tests/conftest.py)")
        yield  # pragma: no cover

    monkeypatch.setattr("wyeast.core.openjev.openjev_lease", _unavailable)
