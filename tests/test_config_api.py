import os
import errno
import asyncio
import json
import pathlib
import shutil
import pytest
from fastapi.testclient import TestClient

# ── 在 import gateway 前 mock FastAPI 依赖 ─────────────────────────────
# 由于 conftest.py 还会被其他模块导入，此处跟 test_routing.py 保持一致
import sys
import types
from unittest.mock import MagicMock

# 仅在未导入时设置 mock，以避免干扰集成测试，但由于 TestClient 需要真实 app，
# 我们可以在这里直接导入 gateway 的 app 进行集成测试，
# 但为了防止某些模块抛错，我们可以直接安全地使用 TestClient(app)
from gateway import (
    app,
    _KW_FILE,
    _KW_MTIME_CACHE,
    _ASSET_MEMORY_CACHE,
    _read_asset_bytes,
    _agent_ledger_ready,
    _cache_fleet_ledger_data,
    _fleet_cache_is_usable,
    _fleet_has_node_issue,
    _fleet_has_stale_export_issue,
    _get_agent_ledger_data,
    _latest_cached_agent_ledger_data,
    _latest_complete_fleet_cache,
    _latest_fleet_cache,
)


@pytest.fixture
def backup_and_restore_keywords():
    """备份并在测试结束后恢复原来的 routing-keywords.json 文件。"""
    backup_path = _KW_FILE + ".bak_test"
    exists = os.path.exists(_KW_FILE)
    if exists:
        shutil.copy2(_KW_FILE, backup_path)

    yield

    # 恢复备份
    if exists:
        if os.path.exists(_KW_FILE):
            os.remove(_KW_FILE)
        shutil.move(backup_path, _KW_FILE)
    else:
        if os.path.exists(_KW_FILE):
            os.remove(_KW_FILE)

    # 清除 mtime 缓存，避免后续测试读到临时路由词表
    import gateway
    gateway._KW_MTIME_CACHE["_mtime"] = 0
    gateway._KW_MTIME_CACHE["data"] = None
    _KW_MTIME_CACHE["_mtime"] = 0
    _KW_MTIME_CACHE["data"] = None


def test_get_routing_config():
    """测试 GET /config 是否能正确返回路由配置数据。"""
    client = TestClient(app)
    response = client.get("/config")
    assert response.status_code == 200
    data = response.json()
    assert "routing" in data
    assert "local_hint" in data["routing"]
    assert "coding" in data["routing"]
    assert "reasoning" in data["routing"]
    assert "quality" in data["routing"]
    assert "providers" in data


def test_dashboard_static_assets_are_not_empty():
    client = TestClient(app)
    css = client.get("/dashboard.css")
    js = client.get("/dashboard.js")

    assert css.status_code == 200
    assert css.headers["content-type"].startswith("text/css")
    assert len(css.content) > 1000
    assert b":root" in css.content

    assert js.status_code == 200
    assert js.headers["content-type"].startswith("application/javascript")
    assert len(js.content) > 1000
    assert b"smart-agent-ledger-dashboard-settings" in js.content
    assert b"translations" in js.content


def test_demo_mode_returns_anonymized_sample_ledgers(monkeypatch):
    monkeypatch.setenv("SMART_AGENT_LEDGER_DEMO_MODE", "1")
    client = TestClient(app)

    agent = client.get("/agent-ledger?days=30&limit=10").json()
    fleet = client.get("/fleet-ledger?days=30&limit=10").json()
    subscriptions = client.get("/subscription-ledger").json()
    feishu = client.get("/feishu-reminder").json()
    combined = json.dumps([agent, fleet, subscriptions, feishu], ensure_ascii=False)

    assert agent["demo_mode"] is True
    assert fleet["demo_mode"] is True
    assert subscriptions["demo_mode"] is True
    assert feishu["demo_mode"] is True
    assert agent["totals"]["total_tokens"] > 0
    assert fleet["node_health"]["complete"] is True
    assert subscriptions["totals"]["plans"] >= 2
    assert "demo-founder-mac" in combined
    assert "/Users/" not in combined
    assert ("Library/" + "Mobile " + "Documents") not in combined
    assert "demo-laptop" not in combined.lower()
    assert "demo-main" not in combined.lower()


def test_readme_includes_open_source_demo_quickstart_without_private_paths():
    readme = pathlib.Path("README.md").read_text(encoding="utf-8")
    readme_zh = pathlib.Path("README.zh-CN.md").read_text(encoding="utf-8")

    assert "SMART_AGENT_LEDGER_DEMO_MODE=1" in readme
    assert "412%20passing" in readme
    assert "OPEN_SOURCE_READINESS.md" in readme
    assert pathlib.Path("OPEN_SOURCE_READINESS.md").is_file()
    assert "tests-371" not in readme
    private_cloud_path = "Mobile " + "Documents/" + "com~apple~" + "Cloud" + "Docs"
    assert private_cloud_path not in readme
    assert private_cloud_path not in readme_zh


def test_one_line_collector_bootstrap_is_documented_and_self_contained():
    readme = pathlib.Path("README.md").read_text(encoding="utf-8")
    readme_zh = pathlib.Path("README.zh-CN.md").read_text(encoding="utf-8")
    testing = pathlib.Path("TESTING.md").read_text(encoding="utf-8")
    bootstrap = pathlib.Path("deploy/bootstrap-collector-node.sh").read_text(encoding="utf-8")
    onboard = pathlib.Path("deploy/onboard-collector-node.sh").read_text(encoding="utf-8")
    install = pathlib.Path("deploy/install-agent-ledger-readonly-launchd.sh").read_text(encoding="utf-8")
    plist = pathlib.Path("deploy/com.smart-agent-ledger.agent-ledger.plist.example").read_text(encoding="utf-8")

    combined_docs = "\n".join([readme, readme_zh, testing])
    assert "bootstrap-collector-node.sh" in combined_docs
    assert "raw.githubusercontent.com/ChuluuMGL/Smart-Agent-Ledger/main/deploy/bootstrap-collector-node.sh" in combined_docs
    assert "--main http://<mac-mini-tailscale-ip>:8001" in combined_docs
    assert "https://github.com/ChuluuMGL/Smart-Agent-Ledger.git" in bootstrap
    assert "codeload.github.com/ChuluuMGL/Smart-Agent-Ledger" in bootstrap
    assert "deploy/onboard-collector-node.sh" in bootstrap
    assert "deploy/install-agent-ledger-readonly-launchd.sh" in onboard
    assert "/admin/nodes" in onboard
    assert "base_url_candidates" in onboard
    assert "agent_ledger_server:app" in install
    assert "com.smart-agent-ledger.agent-ledger" in plist
    assert "sudo" not in "\n".join([bootstrap, onboard, install])


def test_dashboard_allows_slow_fleet_cold_start():
    js = pathlib.Path("static/dashboard.js").read_text(encoding="utf-8")

    assert "fleet-ledger?days=" in js
    assert "state.settings.limit, 60000" in js


def test_dashboard_clears_previous_window_data_on_day_change():
    js = pathlib.Path("static/dashboard.js").read_text(encoding="utf-8")

    assert "function renderWindowLoadingState()" in js
    assert "function resetWindowDataForReload()" in js
    assert "state.lastFleet = null" in js
    assert "state.lastLedger = null" in js
    assert "renderWindowLoadingState();" in js
    assert "resetWindowDataForReload();" in js


def test_dashboard_kpis_are_fleet_first_not_local_fallback():
    js = pathlib.Path("static/dashboard.js").read_text(encoding="utf-8")

    assert "const fleetSnapshotReady = !!(fleet && fleet.totals);" in js
    assert "const totals = fleetSnapshotReady ?" in js
    assert "state.fleetLoadFailed" in js
    assert "未用本机账本替代" in js
    assert "label: t('fleet-health-token-total'" in js
    assert "const staleFleetNodeNames =" in js
    assert "kpi-fleet-stale-cache-detail" in js


def test_dashboard_surfaces_data_trust_contract():
    js = pathlib.Path("static/dashboard.js").read_text(encoding="utf-8")

    assert "dataTrustStatusLabel" in js
    assert "dataTrustOverview" in js
    assert "data.data_trust || {}" in js
    assert "data-trust-title" in js
    assert "data-trust-overview" in js


def test_dashboard_prefers_structured_node_next_action():
    js = pathlib.Path("static/dashboard.js").read_text(encoding="utf-8")

    assert "row.next_action || row.operator_hint" in js
    assert "row.health_reason" in js


def test_dashboard_default_navigation_is_core_only():
    html = pathlib.Path("static/dashboard.html").read_text(encoding="utf-8")
    js = pathlib.Path("static/dashboard.js").read_text(encoding="utf-8")
    nav = html.split('<nav class="nav" id="nav">', 1)[1].split("</nav>", 1)[0]

    for target in ["overview", "agents", "projects", "fleet", "settings"]:
        assert f'data-target="{target}"' in nav

    assert 'data-target="rankings"' not in nav
    assert 'data-target="trends"' not in nav
    assert 'data-target="subscriptions"' not in nav
    assert 'id="subscriptionAlerts"' in html
    assert '<section id="rankings">' not in html
    assert '<section id="trends">' not in html
    assert '<section id="subscriptions">' not in html
    assert 'id="subSummary"' in html
    assert 'id="planTable"' in html
    assert 'id="routing-advice"' in html
    assert "const corePages = new Set(['overview', 'agents', 'projects', 'fleet', 'settings']);" in js


def test_dashboard_keeps_subscription_alerts_as_overview_surface_only():
    html = pathlib.Path("static/dashboard.html").read_text(encoding="utf-8")
    js = pathlib.Path("static/dashboard.js").read_text(encoding="utf-8")

    assert '<div id="subscriptionAlerts" class="overview-alerts">' in html
    assert 'href="#settings"' in js
    assert 'href="#subscriptions"' not in js
    assert 'data-target="subscriptions"' not in html
    assert '<section id="subscriptions">' not in html
    assert "document.getElementById('subscriptionAlerts').innerHTML" in js


def test_dashboard_kpi_cards_have_fixed_number_alignment():
    css = pathlib.Path("static/dashboard.css").read_text(encoding="utf-8")
    js = pathlib.Path("static/dashboard.js").read_text(encoding="utf-8")

    assert 'class="kpi-head"' in js
    assert 'class="value-row"' in js
    assert ".kpi {" in css
    assert "grid-template-rows: 22px 46px minmax(34px, auto);" in css
    assert ".kpi .value-row" in css
    assert "font-variant-numeric: tabular-nums;" in css


def test_dashboard_uses_team_node_language_and_health_check():
    html = pathlib.Path("static/dashboard.html").read_text(encoding="utf-8")
    js = pathlib.Path("static/dashboard.js").read_text(encoding="utf-8")

    assert "团队节点" in html
    assert "'nav-fleet': '团队节点'" in js
    assert "'sec-fleet': '团队节点'" in js
    assert "'node-ops-title': '健康检查'" in js
    assert "'fleet-ops-title': '健康检查'" in js
    assert "'nav-fleet': 'Team Nodes'" in js
    old_label = "公司" + "节点"
    assert old_label not in html
    assert old_label not in js
    assert "Company Fleet Nodes" not in js


def test_dashboard_core_load_does_not_wait_for_optional_management_panels():
    js = pathlib.Path("static/dashboard.js").read_text(encoding="utf-8")

    assert "function loadOptionalPanels(loadId = state.activeLoadId)" in js
    assert "Promise.allSettled([loadFleet(loadId), loadSubscriptions(), loadFeishuReminder()])" not in js
    assert "const fleetResult = await Promise.allSettled([loadFleet(loadId)]);" in js
    assert "loadOptionalPanels(loadId);" in js


def test_dashboard_renders_kpis_as_soon_as_fleet_returns():
    js = pathlib.Path("static/dashboard.js").read_text(encoding="utf-8")
    load_fleet = js.split("async function loadFleet", 1)[1].split("function showLedgerLoading", 1)[0]

    assert "renderKpis(state.lastLedger || { window_days: state.settings.days, totals: {} });" in load_fleet
    assert "document.getElementById('loading').style.display = 'none';" in load_fleet


def test_dashboard_explains_stale_fleet_snapshot_refreshing():
    js = pathlib.Path("static/dashboard.js").read_text(encoding="utf-8")

    assert "kpi-fleet-refreshing-detail" in js
    assert "fleet && (fleet._stale || fleet._refreshing)" in js


def test_dashboard_explains_partial_fleet_cache_snapshot():
    js = pathlib.Path("static/dashboard.js").read_text(encoding="utf-8")

    assert "kpi-fleet-partial-cache-detail" in js
    assert "fleet && fleet._partial_cache" in js


def test_dashboard_surfaces_demo_mode_without_extra_page():
    html = pathlib.Path("static/dashboard.html").read_text(encoding="utf-8")
    js = pathlib.Path("static/dashboard.js").read_text(encoding="utf-8")
    css = pathlib.Path("static/dashboard.css").read_text(encoding="utf-8")

    assert 'id="demoBanner"' in html
    assert "function renderDemoModeBanner" in js
    assert "data && data.demo_mode" in js
    assert ".demo-banner" in css


def test_dashboard_core_refresh_skips_retired_ranking_and_trend_rendering():
    js = pathlib.Path("static/dashboard.js").read_text(encoding="utf-8")
    apply_ledger = js.split("function applyLedger", 1)[1].split("function connectSse", 1)[0]
    load_fleet = js.split("async function loadFleet", 1)[1].split("function showLedgerLoading", 1)[0]

    assert "renderRankings(" not in apply_ledger
    assert "renderTrendChart(" not in apply_ledger
    assert "renderRankings(" not in load_fleet
    assert "renderTrendChart(" not in load_fleet


def test_static_asset_read_uses_cache_after_icloud_deadlock(tmp_path, monkeypatch):
    import gateway

    asset = tmp_path / "dashboard.css"
    asset.write_bytes(b"body{color:white}")
    monkeypatch.setattr(gateway, "_ASSET_DISK_CACHE_DIR", tmp_path / "asset-cache")
    _ASSET_MEMORY_CACHE.clear()
    assert _read_asset_bytes(asset) == b"body{color:white}"
    asset.write_bytes(b"body{color:black}")

    original_read_bytes = pathlib.Path.read_bytes

    def flaky_read_bytes(self):
        if self == asset:
            raise OSError(errno.EDEADLK, "Resource deadlock avoided")
        return original_read_bytes(self)

    monkeypatch.setattr(pathlib.Path, "read_bytes", flaky_read_bytes)
    assert _read_asset_bytes(asset) == b"body{color:white}"


def test_fleet_node_issue_detection():
    assert _fleet_has_node_issue({"nodes": [{"status": "connected"}], "access_issues": []}) is False
    assert _fleet_has_node_issue({"nodes": [{"status": "disabled"}], "access_issues": []}) is False
    assert _fleet_has_node_issue({"nodes": [{"status": "unreachable"}], "access_issues": []}) is True
    assert _fleet_has_node_issue({"nodes": [{"status": "connected"}], "access_issues": [{"node": "n8n"}]}) is True
    assert _fleet_cache_is_usable({"nodes": [{"status": "connected"}], "access_issues": []}) is True
    assert _fleet_cache_is_usable({"nodes": [{"status": "missing_url"}], "access_issues": []}) is False
    assert _fleet_cache_is_usable({"nodes": [{"status": "connected"}], "_last_refresh_failed": True}) is False
    assert _agent_ledger_ready({"recent_sessions": [{"id": "s1"}]}) is True
    assert _agent_ledger_ready({"recent_sessions": [{"id": "s1"}], "_refreshing": True}) is False


def test_latest_complete_fleet_cache_matches_days_and_survives_memory_clear(tmp_path, monkeypatch):
    import gateway

    monkeypatch.setattr(gateway, "FLEET_DISK_CACHE_DIR", tmp_path / "fleet-cache")
    monkeypatch.setattr(gateway.time, "time", lambda: 1000)
    gateway.FLEET_CACHE.clear()
    good = {
        "window_days": 90,
        "nodes": [{"node": "mba", "status": "connected"}],
        "access_issues": [],
        "node_health": {"complete": True},
        "totals": {"total_tokens": 7000},
    }
    partial = {
        "window_days": 90,
        "nodes": [{"node": "n8n", "status": "unreachable"}],
        "access_issues": [{"node": "n8n", "issue": "ssh timeout"}],
        "totals": {"total_tokens": 3000},
    }
    try:
        _cache_fleet_ledger_data((90, 300), good)
        gateway.FLEET_CACHE[(90, 120)] = {"ts": 1000, "data": partial}

        fallback = _latest_complete_fleet_cache(days=90, now=1001)
        assert fallback["data"]["totals"]["total_tokens"] == 7000
        assert _latest_complete_fleet_cache(days=30, now=1001) is None

        gateway.FLEET_CACHE.clear()
        disk_fallback = _latest_complete_fleet_cache(days=90, now=1001)
        assert disk_fallback["data"]["totals"]["total_tokens"] == 7000
    finally:
        gateway.FLEET_CACHE.clear()


def test_fleet_ledger_returns_cached_snapshot_while_refreshing(tmp_path, monkeypatch):
    import gateway

    monkeypatch.setattr(gateway, "FLEET_DISK_CACHE_DIR", tmp_path / "fleet-cache")
    gateway.FLEET_CACHE.clear()
    monkeypatch.setattr(gateway.time, "time", lambda: 1000)
    cached_snapshot = {
        "generated_at": "2026-07-08T03:50:00+00:00",
        "window_days": 30,
        "nodes": [{"node": "demo-main", "status": "connected"}],
        "access_issues": [],
        "node_health": {"complete": False, "status": "partial"},
        "totals": {"total_tokens": 1000},
    }
    gateway.FLEET_CACHE[(30, 120)] = {"ts": 900, "data": cached_snapshot}

    async def fake_agent_ledger(days, limit):
        return {
            "window_days": days,
            "recent_sessions": [{"session_id": "local"}],
            "totals": {"total_tokens": 2000},
        }

    async def fake_build_fleet_ledger(**kwargs):
        return {
            "generated_at": "2026-07-08T04:00:00+00:00",
            "window_days": kwargs["days"],
            "nodes": [{"node": "demo-main", "status": "connected"}],
            "access_issues": [],
            "node_health": {"complete": True, "status": "complete"},
            "totals": {"total_tokens": 2000},
        }

    monkeypatch.setattr(gateway, "_get_agent_ledger_data", fake_agent_ledger)
    monkeypatch.setattr(gateway, "build_fleet_ledger", fake_build_fleet_ledger)

    try:
        data = asyncio.run(gateway.fleet_ledger(days=30, limit=120))
    finally:
        for task in gateway.FLEET_TASKS.values():
            task.cancel()
        gateway.FLEET_TASKS.clear()
        gateway.FLEET_CACHE.clear()

    assert data["totals"]["total_tokens"] == 1000
    assert data["_stale"] is True
    assert data["_refreshing"] is True
    assert data["_stale_cache_age_seconds"] == 100


def test_fleet_ledger_cold_build_returns_without_local_ready_leak(tmp_path, monkeypatch):
    import gateway

    monkeypatch.setattr(gateway, "FLEET_DISK_CACHE_DIR", tmp_path / "fleet-cache")
    gateway.FLEET_CACHE.clear()

    async def fake_build_response(days, limit):
        return {
            "generated_at": "2026-07-08T04:00:00+00:00",
            "window_days": days,
            "nodes": [{"node": "demo-main", "status": "connected"}],
            "access_issues": [],
            "node_health": {"complete": True, "status": "complete"},
            "totals": {"total_tokens": 3000},
        }

    monkeypatch.setattr(gateway, "_build_fleet_ledger_response", fake_build_response)

    try:
        data = asyncio.run(gateway.fleet_ledger(days=30, limit=120))
    finally:
        for task in gateway.FLEET_TASKS.values():
            task.cancel()
        gateway.FLEET_TASKS.clear()
        gateway.FLEET_CACHE.clear()

    assert data["totals"]["total_tokens"] == 3000


def test_fleet_ledger_cold_build_timeout_returns_refreshing_snapshot(tmp_path, monkeypatch):
    import gateway

    monkeypatch.setattr(gateway, "FLEET_DISK_CACHE_DIR", tmp_path / "fleet-cache")
    monkeypatch.setattr(gateway, "FLEET_FIRST_RESPONSE_TIMEOUT_SECONDS", 0.1)
    gateway.FLEET_CACHE.clear()
    gateway.FLEET_TASKS.clear()

    async def slow_build_response(days, limit):
        await asyncio.sleep(60)
        return {
            "generated_at": "2026-07-08T04:00:00+00:00",
            "window_days": days,
            "nodes": [{"node": "demo-main", "status": "connected"}],
            "access_issues": [],
            "node_health": {"complete": True, "status": "complete"},
            "data_trust": {"scope": "fleet", "status": "complete", "score": 100},
            "totals": {"total_tokens": 3000},
        }

    monkeypatch.setattr(gateway, "_build_fleet_ledger_response", slow_build_response)

    async def exercise():
        try:
            data = await gateway.fleet_ledger(days=30, limit=120)
            await asyncio.sleep(0)
            return data, set(gateway.FLEET_TASKS.keys())
        finally:
            for task in gateway.FLEET_TASKS.values():
                task.cancel()
            gateway.FLEET_TASKS.clear()
            gateway.FLEET_CACHE.clear()

    data, task_keys = asyncio.run(exercise())

    assert data["_refreshing"] is True
    assert data["data_trust"]["status"] == "refreshing"
    assert (30, 120) in task_keys


def test_fleet_refreshing_placeholder_nodes_have_next_action(tmp_path, monkeypatch):
    import gateway

    nodes_path = tmp_path / "company-agent-nodes.json"
    nodes_path.write_text(
        json.dumps({"nodes": [{"name": "demo-laptop"}, {"name": "disabled-demo", "enabled": False}]}),
        encoding="utf-8",
    )
    monkeypatch.setattr(gateway, "_COMPANY_NODES_PATH", nodes_path)

    data = gateway._empty_fleet_ledger(days=30, limit=120)

    assert data["nodes"][0]["health_status"] == "info"
    assert data["nodes"][0]["health_reason"] == "background_refreshing"
    assert "后台刷新" in data["nodes"][0]["next_action"]
    assert len(data["nodes"]) == 1


def test_fleet_cached_snapshot_normalizes_node_next_action(tmp_path, monkeypatch):
    import gateway

    monkeypatch.setattr(gateway, "FLEET_DISK_CACHE_DIR", tmp_path / "fleet-cache")
    gateway.FLEET_CACHE.clear()
    gateway.FLEET_TASKS.clear()
    gateway.FLEET_CACHE[(30, 120)] = {
        "ts": gateway.time.time(),
        "data": {
            "generated_at": "2026-07-09T04:00:00+00:00",
            "window_days": 30,
            "totals": {"total_tokens": 1000},
            "nodes": [
                {
                    "node": "demo-laptop",
                    "status": "unreachable",
                    "source_type": "smart_gateway",
                    "data_quality": "unavailable",
                    "current_data_included": False,
                    "attempted_urls": ["http://100.64.0.9:8002/agent-ledger?days=30&limit=120"],
                    "issue": "旧缓存提示：请确认两台机器在同一 Wi-Fi。",
                    "next_action": "旧缓存提示：请确认两台机器在同一 Wi-Fi。",
                }
            ],
            "access_issues": [{"node": "demo-laptop", "issue": "timeout"}],
            "node_health": {"status": "partial", "complete": False},
            "data_trust": {"scope": "fleet", "status": "partial", "score": 30},
        },
    }

    try:
        data = asyncio.run(gateway.fleet_ledger(days=30, limit=120))
    finally:
        gateway.FLEET_CACHE.clear()
        gateway.FLEET_TASKS.clear()

    action = data["nodes"][0]["next_action"]
    assert "Tailscale 在线" in action
    assert "同一 Wi-Fi" not in action


def test_fleet_ledger_prefetches_sibling_windows_after_cold_build(tmp_path, monkeypatch):
    import gateway

    monkeypatch.setattr(gateway, "FLEET_DISK_CACHE_DIR", tmp_path / "fleet-cache")
    monkeypatch.setattr(gateway, "FLEET_PREFETCH_WINDOWS", (7, 30, 90), raising=False)
    gateway.FLEET_CACHE.clear()
    gateway.FLEET_TASKS.clear()

    async def fake_build_response(days, limit):
        return {
            "generated_at": "2026-07-08T04:00:00+00:00",
            "window_days": days,
            "nodes": [{"node": "demo-main", "status": "connected"}],
            "access_issues": [],
            "node_health": {"complete": True, "status": "complete"},
            "totals": {"total_tokens": days},
        }

    async def fake_refresh(cache_key, days, limit):
        try:
            if days == 30:
                data = await fake_build_response(days, limit)
                gateway._cache_fleet_ledger_data(cache_key, data)
                return data
            await asyncio.sleep(60)
        finally:
            if days == 30:
                gateway.FLEET_TASKS.pop(cache_key, None)

    monkeypatch.setattr(gateway, "_build_fleet_ledger_response", fake_build_response)
    monkeypatch.setattr(gateway, "_refresh_fleet_cache", fake_refresh)

    async def exercise():
        try:
            data = await gateway.fleet_ledger(days=30, limit=120)
            await asyncio.sleep(0)
            return data, set(gateway.FLEET_TASKS.keys())
        finally:
            for task in gateway.FLEET_TASKS.values():
                task.cancel()
            gateway.FLEET_TASKS.clear()
            gateway.FLEET_CACHE.clear()

    data, task_keys = asyncio.run(exercise())

    assert data["totals"]["total_tokens"] == 30
    assert (7, 120) in task_keys
    assert (90, 120) in task_keys
    assert (30, 120) not in task_keys


def test_fleet_ledger_reuses_fresh_partial_snapshot_without_refetch(tmp_path, monkeypatch):
    import gateway

    monkeypatch.setattr(gateway, "FLEET_DISK_CACHE_DIR", tmp_path / "fleet-cache")
    monkeypatch.setattr(gateway.time, "time", lambda: 1000)
    gateway.FLEET_CACHE.clear()
    gateway.FLEET_TASKS.clear()
    calls = 0

    async def fake_build_response(days, limit):
        nonlocal calls
        calls += 1
        return {
            "generated_at": "2026-07-08T04:00:00+00:00",
            "window_days": days,
            "nodes": [
                {"node": "demo-main", "status": "connected"},
                {"node": "demo-laptop", "status": "unreachable"},
            ],
            "access_issues": [{"node": "demo-laptop", "issue": "timeout"}],
            "node_health": {"complete": False, "status": "partial"},
            "totals": {"total_tokens": 700},
        }

    monkeypatch.setattr(gateway, "_build_fleet_ledger_response", fake_build_response)

    async def exercise():
        try:
            first = await gateway.fleet_ledger(days=7, limit=120)
            second = await gateway.fleet_ledger(days=7, limit=120)
            return first, second
        finally:
            for task in gateway.FLEET_TASKS.values():
                task.cancel()
            gateway.FLEET_TASKS.clear()
            gateway.FLEET_CACHE.clear()

    first, second = asyncio.run(exercise())

    assert calls == 1
    assert first["node_health"]["status"] == "partial"
    assert second["node_health"]["status"] == "partial"
    assert second["_partial_cache"] is True
    assert second["_cache_age_seconds"] == 0


def test_displayable_partial_fleet_cache_persists_to_disk(tmp_path, monkeypatch):
    import gateway

    monkeypatch.setattr(gateway, "FLEET_DISK_CACHE_DIR", tmp_path / "fleet-cache")
    monkeypatch.setattr(gateway.time, "time", lambda: 1000)
    gateway.FLEET_CACHE.clear()
    partial = {
        "generated_at": "2026-07-08T04:00:00+00:00",
        "window_days": 30,
        "nodes": [
            {"node": "demo-main", "status": "connected"},
            {"node": "demo-laptop", "status": "unreachable"},
        ],
        "access_issues": [{"node": "demo-laptop", "issue": "timeout"}],
        "node_health": {"complete": False, "status": "partial"},
        "data_trust": {"scope": "fleet", "status": "partial", "score": 70},
        "totals": {"total_tokens": 700},
    }

    try:
        _cache_fleet_ledger_data((30, 120), partial)
        assert (tmp_path / "fleet-cache" / "fleet-ledger-30d.json").is_file()

        gateway.FLEET_CACHE.clear()
        fallback = _latest_fleet_cache(days=30, limit=120, now=1001)
    finally:
        gateway.FLEET_CACHE.clear()

    assert fallback["data"]["totals"]["total_tokens"] == 700
    assert fallback["data"]["data_trust"]["status"] == "partial"


def test_fleet_ledger_returns_stale_partial_snapshot_after_ttl(tmp_path, monkeypatch):
    import gateway

    monkeypatch.setattr(gateway, "FLEET_DISK_CACHE_DIR", tmp_path / "fleet-cache")
    monkeypatch.setattr(gateway.time, "time", lambda: 1000)
    gateway.FLEET_CACHE.clear()
    gateway.FLEET_TASKS.clear()
    gateway.FLEET_CACHE[(30, 120)] = {
        "ts": 900,
        "data": {
            "generated_at": "2026-07-08T04:00:00+00:00",
            "window_days": 30,
            "nodes": [
                {"node": "demo-main", "status": "connected"},
                {"node": "demo-laptop", "status": "unreachable"},
            ],
            "access_issues": [{"node": "demo-laptop", "issue": "timeout"}],
            "node_health": {"complete": False, "status": "partial"},
            "data_trust": {"scope": "fleet", "status": "partial", "score": 70},
            "totals": {"total_tokens": 700},
        },
    }

    async def fail_build_response(days, limit):
        raise AssertionError("expired displayable partial cache should be returned before synchronous rebuild")

    async def slow_refresh(cache_key, days, limit):
        await asyncio.sleep(60)

    monkeypatch.setattr(gateway, "_build_fleet_ledger_response", fail_build_response)
    monkeypatch.setattr(gateway, "_refresh_fleet_cache", slow_refresh)

    async def exercise():
        try:
            data = await gateway.fleet_ledger(days=30, limit=120)
            await asyncio.sleep(0)
            return data, set(gateway.FLEET_TASKS.keys())
        finally:
            for task in gateway.FLEET_TASKS.values():
                task.cancel()
            gateway.FLEET_TASKS.clear()
            gateway.FLEET_CACHE.clear()

    data, task_keys = asyncio.run(exercise())

    assert data["totals"]["total_tokens"] == 700
    assert data["_stale"] is True
    assert data["_refreshing"] is True
    assert (30, 120) in task_keys


def test_partial_cold_build_prefetches_sibling_windows(tmp_path, monkeypatch):
    import gateway

    monkeypatch.setattr(gateway, "FLEET_DISK_CACHE_DIR", tmp_path / "fleet-cache")
    monkeypatch.setattr(gateway, "FLEET_PREFETCH_WINDOWS", (7, 30, 90), raising=False)
    gateway.FLEET_CACHE.clear()
    gateway.FLEET_TASKS.clear()

    async def fake_build_response(days, limit):
        return {
            "generated_at": "2026-07-08T04:00:00+00:00",
            "window_days": days,
            "nodes": [
                {"node": "demo-main", "status": "connected"},
                {"node": "demo-laptop", "status": "unreachable"},
            ],
            "access_issues": [{"node": "demo-laptop", "issue": "timeout"}],
            "node_health": {"complete": False, "status": "partial"},
            "data_trust": {"scope": "fleet", "status": "partial", "score": 70},
            "totals": {"total_tokens": days},
        }

    async def fake_refresh(cache_key, days, limit):
        try:
            if days == 30:
                data = await fake_build_response(days, limit)
                gateway._cache_fleet_ledger_data(cache_key, data)
                return data
            await asyncio.sleep(60)
        finally:
            if days == 30:
                gateway.FLEET_TASKS.pop(cache_key, None)

    monkeypatch.setattr(gateway, "_build_fleet_ledger_response", fake_build_response)
    monkeypatch.setattr(gateway, "_refresh_fleet_cache", fake_refresh)

    async def exercise():
        try:
            data = await gateway.fleet_ledger(days=30, limit=120)
            await asyncio.sleep(0)
            return data, set(gateway.FLEET_TASKS.keys())
        finally:
            for task in gateway.FLEET_TASKS.values():
                task.cancel()
            gateway.FLEET_TASKS.clear()
            gateway.FLEET_CACHE.clear()

    data, task_keys = asyncio.run(exercise())

    assert data["totals"]["total_tokens"] == 30
    assert (7, 120) in task_keys
    assert (90, 120) in task_keys
    assert (30, 120) not in task_keys


def test_stale_export_issue_is_not_treated_as_usable_fleet_cache():
    data = {
        "nodes": [{"node": "demo-laptop", "status": "connected", "export_stale": True}],
        "access_issues": [{"node": "demo-laptop", "issue": "ledger export is stale: generated_at=2026-06-17"}],
    }

    assert _fleet_has_node_issue(data) is True
    assert _fleet_has_stale_export_issue(data) is True
    assert _fleet_cache_is_usable(data) is False


def test_agent_ledger_fallback_cache_matches_days(monkeypatch):
    import gateway

    monkeypatch.setattr(gateway.time, "time", lambda: 1000)
    gateway.LEDGER_CACHE.clear()
    try:
        gateway.LEDGER_CACHE[(7, 200)] = {
            "ts": 999,
            "data": {"window_days": 7, "totals": {"total_tokens": 700}, "recent_sessions": [{"id": "7d"}]},
        }
        gateway.LEDGER_CACHE[(90, 120)] = {
            "ts": 990,
            "data": {"window_days": 90, "totals": {"total_tokens": 9000}, "recent_sessions": [{"id": "90d"}]},
        }

        assert _latest_cached_agent_ledger_data(days=90)["totals"]["total_tokens"] == 9000
        assert _latest_cached_agent_ledger_data(days=30) is None
    finally:
        gateway.LEDGER_CACHE.clear()


def test_agent_ledger_timeout_uses_same_day_cached_snapshot(monkeypatch):
    import gateway

    monkeypatch.setattr(gateway.time, "time", lambda: 1000)
    monkeypatch.setattr(gateway, "LEDGER_FIRST_RESPONSE_TIMEOUT_SECONDS", 0)
    gateway.LEDGER_CACHE.clear()
    gateway.LEDGER_TASKS.clear()

    gateway.LEDGER_CACHE[(90, 1000)] = {
        "ts": 999,
        "data": {
            "window_days": 90,
            "totals": {"sessions": 3, "total_tokens": 9000},
            "recent_sessions": [{"id": "cached"}],
        },
    }

    def fake_build_agent_ledger(days, limit):
        return {
            "window_days": days,
            "totals": {"sessions": 1, "total_tokens": 1},
            "recent_sessions": [{"id": "fresh"}],
        }

    monkeypatch.setattr(gateway, "build_agent_ledger", fake_build_agent_ledger)

    try:
        data = asyncio.run(_get_agent_ledger_data(days=90, limit=120))

        assert data["totals"]["total_tokens"] == 9000
        assert data["recent_sessions"] == [{"id": "cached"}]
        assert data["_refreshing"] is True
        assert data["_stale"] is True
        assert data["_cache_age_seconds"] == 1
    finally:
        gateway.LEDGER_CACHE.clear()
        gateway.LEDGER_TASKS.clear()


def test_post_routing_config_success(backup_and_restore_keywords):
    """测试成功更新配置并验证热加载。"""
    client = TestClient(app)

    new_config = {
        "local_hint": ["test-local-key"],
        "coding": ["test-coding-key"],
        "reasoning": ["test-reason-key"],
        "quality": ["test-quality-key"]
    }

    # 提交配置
    response = client.post("/config/routing", json=new_config)
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

    # 校验磁盘写入
    with open(_KW_FILE, "r", encoding="utf-8") as f:
        saved = json.load(f)
    assert saved == new_config

    # 校验 GET 接口是否获取到最新热加载配置
    resp_get = client.get("/config")
    assert resp_get.status_code == 200
    get_data = resp_get.json()
    assert get_data["routing"]["local_hint"] == ["test-local-key"]
    assert get_data["routing"]["coding"] == ["test-coding-key"]


def test_post_routing_config_missing_field(backup_and_restore_keywords):
    """测试缺少字段时的错误验证。"""
    client = TestClient(app)

    incomplete_config = {
        "local_hint": ["test-local-key"],
        "coding": ["test-coding-key"]
        # 缺少 reasoning, quality
    }

    response = client.post("/config/routing", json=incomplete_config)
    assert response.status_code == 400
    assert "缺少必要的路由字段" in response.json()["detail"]


def test_post_routing_config_invalid_type(backup_and_restore_keywords):
    """测试字段类型不合法时的错误验证。"""
    client = TestClient(app)

    invalid_config = {
        "local_hint": "not-a-list",  # 不合法
        "coding": ["test-coding-key"],
        "reasoning": ["test-reason-key"],
        "quality": ["test-quality-key"]
    }

    response = client.post("/config/routing", json=invalid_config)
    assert response.status_code == 422
    assert "list" in response.json()["detail"][0]["msg"]
