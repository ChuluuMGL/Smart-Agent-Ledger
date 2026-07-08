from fastapi.testclient import TestClient
import pytest
import time


@pytest.fixture(autouse=True)
def clear_readonly_ledger_cache(tmp_path, monkeypatch):
    import agent_ledger_server

    monkeypatch.setattr(agent_ledger_server, "READONLY_LEDGER_DISK_CACHE_DIR", tmp_path / "readonly-cache")
    for task in agent_ledger_server.READONLY_LEDGER_TASKS.values():
        task.cancel()
    agent_ledger_server.READONLY_LEDGER_TASKS.clear()
    agent_ledger_server.READONLY_LEDGER_CACHE.clear()
    yield
    for task in agent_ledger_server.READONLY_LEDGER_TASKS.values():
        task.cancel()
    agent_ledger_server.READONLY_LEDGER_TASKS.clear()
    agent_ledger_server.READONLY_LEDGER_CACHE.clear()


def test_readonly_agent_ledger_server_health():
    import agent_ledger_server

    client = TestClient(agent_ledger_server.app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "agent-ledger-readonly"


def test_readonly_agent_ledger_server_bounds_query_params(monkeypatch):
    import agent_ledger_server

    calls = []

    def fake_build_agent_ledger(days, limit):
        calls.append({"days": days, "limit": limit})
        return {
            "generated_at": "2026-06-16T00:00:00+00:00",
            "totals": {"sessions": 0, "total_tokens": 0},
            "recent_sessions": [],
        }

    monkeypatch.setattr(agent_ledger_server, "build_agent_ledger", fake_build_agent_ledger)
    client = TestClient(agent_ledger_server.app)

    response = client.get("/agent-ledger?days=99999&limit=99999")

    assert response.status_code == 200
    assert calls == [{"days": 3660, "limit": 2000}]
    assert response.json()["totals"]["total_tokens"] == 0


def test_readonly_agent_ledger_server_returns_cached_snapshot_on_slow_refresh(tmp_path, monkeypatch):
    import agent_ledger_server

    agent_ledger_server.READONLY_LEDGER_CACHE.clear()
    agent_ledger_server.READONLY_LEDGER_TASKS.clear()
    monkeypatch.setattr(agent_ledger_server, "READONLY_LEDGER_DISK_CACHE_DIR", tmp_path)
    monkeypatch.setattr(agent_ledger_server, "READONLY_LEDGER_CACHE_TTL_SECONDS", 0)
    monkeypatch.setattr(agent_ledger_server, "READONLY_LEDGER_FIRST_RESPONSE_TIMEOUT_SECONDS", 0.01)

    def fast_build_agent_ledger(days, limit):
        return {
            "generated_at": "2026-06-16T00:00:00+00:00",
            "window_days": days,
            "totals": {"sessions": 1, "total_tokens": 1000},
            "recent_sessions": [{"session_id": "cached", "total_tokens": 1000}],
        }

    monkeypatch.setattr(agent_ledger_server, "build_agent_ledger", fast_build_agent_ledger)
    with TestClient(agent_ledger_server.app) as client:
        first = client.get("/agent-ledger?days=30&limit=120")
        assert first.status_code == 200
        assert first.json()["totals"]["total_tokens"] == 1000

        def slow_build_agent_ledger(days, limit):
            time.sleep(0.2)
            return {
                "generated_at": "2026-06-16T00:01:00+00:00",
                "window_days": days,
                "totals": {"sessions": 1, "total_tokens": 2000},
                "recent_sessions": [{"session_id": "fresh", "total_tokens": 2000}],
            }

        monkeypatch.setattr(agent_ledger_server, "build_agent_ledger", slow_build_agent_ledger)
        second = client.get("/agent-ledger?days=30&limit=120")

    body = second.json()
    assert second.status_code == 200
    assert body["totals"]["total_tokens"] == 1000
    assert body["_ledger_cache_fallback"] is True
    assert body["_refreshing"] is True
    assert body["_stale"] is True
    assert body["_cache_age_seconds"] >= 0
