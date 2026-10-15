"""公共 fixture — 将项目根目录加入 sys.path，便于 import 各模块。"""
import sys
import pathlib

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


import importlib

import pytest

# Starlette's TestClient reports the client as "testclient" and sends
# Host: testserver. Production code only trusts real loopback IPs/hosts, so
# the suite registers these placeholder names as local. Tests that exercise the
# remote-client path reset _EXTRA_LOCAL_NAMES to an empty set explicitly.
_TESTCLIENT_LOCAL_NAMES = frozenset({"testclient", "testserver"})


@pytest.fixture(autouse=True)
def _testclient_counts_as_loopback(monkeypatch):
    for name in ("gateway", "agent_ledger_server"):
        module = sys.modules.get(name)
        if module is None:
            try:
                module = importlib.import_module(name)
            except Exception:  # fastapi missing etc. — pure-logic tests still run
                continue
        if hasattr(module, "_EXTRA_LOCAL_NAMES"):
            monkeypatch.setattr(module, "_EXTRA_LOCAL_NAMES", _TESTCLIENT_LOCAL_NAMES)
    yield
