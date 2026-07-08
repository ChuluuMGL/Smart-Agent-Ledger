"""测试 fleet_ledger.py 的配置加载、URL 构建、排行聚合。"""
import asyncio
import datetime as dt
import json
import pathlib
import httpx
import pytest

from fleet_ledger import (
    _activity_rank,
    _activity_timeline,
    _load_config,
    _local_records_from_ledger,
    _n8n_records_from_sections,
    _n8n_timeline_records_from_sections,
    _node_url,
    _parse_sectioned_tsv,
    _rank,
    _token_quality,
    _tokens_are_known,
    build_fleet_ledger,
    register_node,
    remove_node,
)


class TestLoadConfig:
    def test_missing_file_returns_default(self, tmp_path, monkeypatch):
        """配置文件不存在时返回默认结构。"""
        import fleet_ledger
        monkeypatch.setattr(fleet_ledger, "CONFIG_PATH", tmp_path / "nonexistent.json")
        config = _load_config()
        assert config["schema_version"] == 1
        assert config["nodes"] == []
        assert config["authorized_networks"] == []

    def test_valid_config(self, tmp_path, monkeypatch):
        """正确读取配置文件。"""
        import fleet_ledger
        config_path = tmp_path / "nodes.json"
        config_path.write_text(json.dumps({
            "schema_version": 1,
            "nodes": [{"name": "dev1", "base_url": "http://10.0.0.1:8001"}],
            "authorized_networks": ["10.0.0.0/24"],
        }))
        monkeypatch.setattr(fleet_ledger, "CONFIG_PATH", config_path)
        config = _load_config()
        assert len(config["nodes"]) == 1
        assert config["nodes"][0]["name"] == "dev1"
        assert "10.0.0.0/24" in config["authorized_networks"]

    def test_invalid_json_returns_error(self, tmp_path, monkeypatch):
        """无效 JSON 返回含 load_error 的默认结构。"""
        import fleet_ledger
        config_path = tmp_path / "bad.json"
        config_path.write_text("not json at all")
        monkeypatch.setattr(fleet_ledger, "CONFIG_PATH", config_path)
        config = _load_config()
        assert "load_error" in config
        assert config["nodes"] == []

    def test_non_dict_root_returns_error(self, tmp_path, monkeypatch):
        """根元素非 dict 返回错误。"""
        import fleet_ledger
        config_path = tmp_path / "arr.json"
        config_path.write_text("[1, 2, 3]")
        monkeypatch.setattr(fleet_ledger, "CONFIG_PATH", config_path)
        config = _load_config()
        assert "load_error" in config

    def test_missing_fields_get_defaults(self, tmp_path, monkeypatch):
        """缺少 nodes/authorized_networks 字段时自动补 []。"""
        import fleet_ledger
        config_path = tmp_path / "partial.json"
        config_path.write_text(json.dumps({"schema_version": 2}))
        monkeypatch.setattr(fleet_ledger, "CONFIG_PATH", config_path)
        config = _load_config()
        assert config["nodes"] == []
        assert config["authorized_networks"] == []


class TestNodeUrl:
    def test_ledger_url_takes_priority(self):
        node = {"ledger_url": "http://host:8001/custom-ledger", "base_url": "http://host:8001"}
        assert _node_url(node, 30, 100) == "http://host:8001/custom-ledger"

    def test_base_url_with_params(self):
        node = {"base_url": "http://10.0.0.1:8001/"}
        url = _node_url(node, 7, 50)
        assert url == "http://10.0.0.1:8001/agent-ledger?days=7&limit=50"

    def test_no_urls_returns_none(self):
        assert _node_url({}, 30, 100) is None

    def test_n8n_ssh_node_has_no_http_url(self):
        node = {"type": "n8n_ssh", "host": "example.com"}
        assert _node_url(node, 30, 100) is None

    def test_local_agent_node_has_no_http_url(self):
        node = {"type": "local_agent_ledger", "base_url": "http://127.0.0.1:8001"}
        assert _node_url(node, 30, 100) is None


class TestTokensAreKnown:
    def test_known_token_sessions(self):
        assert _tokens_are_known({"known_token_sessions": 5}) is True

    def test_zero_known_token_sessions_with_tokens(self):
        assert _tokens_are_known({"total_tokens": 1000, "token_status": "ok"}) is True

    def test_not_available_status(self):
        assert _tokens_are_known({"total_tokens": 0, "token_status": "not_available"}) is False

    def test_zero_tokens(self):
        assert _tokens_are_known({"total_tokens": 0}) is False

    def test_pending_schema_mapping_is_not_known(self):
        assert _tokens_are_known({"total_tokens": 100, "token_status": "pending_schema_mapping"}) is False

    def test_estimated_tokens_are_available_but_marked_estimated(self):
        row = {"total_tokens": 100, "token_status": "estimated_from_turn_count"}
        assert _tokens_are_known(row) is True
        assert _token_quality(row) == "estimated"


class TestRank:
    def test_ranks_by_tokens(self):
        rows = [
            {"agent": "claude", "total_tokens": 1000, "token_status": "ok"},
            {"agent": "codex", "total_tokens": 5000, "token_status": "ok"},
        ]
        result = _rank(rows, ["agent"])
        assert len(result) == 2
        assert result[0]["agent"] == "codex"  # highest tokens first

    def test_skips_unknown_tokens(self):
        rows = [
            {"agent": "claude", "total_tokens": 1000, "token_status": "ok"},
            {"agent": "cursor", "total_tokens": 0, "token_status": "not_available"},
        ]
        result = _rank(rows, ["agent"])
        assert len(result) == 1
        assert result[0]["agent"] == "claude"

    def test_merges_same_key(self):
        rows = [
            {"agent": "claude", "total_tokens": 1000, "token_status": "ok", "sessions": 2},
            {"agent": "claude", "total_tokens": 2000, "token_status": "ok", "sessions": 3},
        ]
        result = _rank(rows, ["agent"])
        assert len(result) == 1
        assert result[0]["total_tokens"] == 3000
        assert result[0]["sessions"] == 5

    def test_empty_input(self):
        assert _rank([], ["agent"]) == []

    def test_respects_limit(self):
        rows = [{"agent": f"a{i}", "total_tokens": i * 100, "token_status": "ok"} for i in range(50)]
        result = _rank(rows, ["agent"], limit=5)
        assert len(result) == 5


class TestActivityRank:
    def test_activity_rank_uses_sessions_without_tokens(self):
        rows = [
            {"agent": "n8n", "project": "daily-news", "sessions": 10, "token_status": "not_available"},
            {"agent": "n8n", "project": "draft-gen", "sessions": 3, "token_status": "not_available"},
            {"agent": "codex", "project": "gateway", "sessions": 4, "total_tokens": 1000, "token_status": "ok"},
        ]
        result = _activity_rank(rows, ["agent"])
        assert result[0]["agent"] == "n8n"
        assert result[0]["sessions"] == 13
        assert result[1]["agent"] == "codex"

    def test_activity_rank_tracks_n8n_non_success(self):
        rows = [
            {"project": "flow", "sessions": 5, "n8n_success": 4, "n8n_non_success": 1, "latest_at": "2026-06-13 01:00:00"},
            {"project": "flow", "sessions": 2, "n8n_success": 2, "n8n_non_success": 0, "latest_at": "2026-06-13 02:00:00"},
        ]
        result = _activity_rank(rows, ["project"])
        assert result[0]["sessions"] == 7
        assert result[0]["n8n_success"] == 6
        assert result[0]["n8n_non_success"] == 1
        assert result[0]["latest_at"] == "2026-06-13 02:00:00"


class TestActivityTimeline:
    def test_activity_timeline_keeps_activity_only_agents(self):
        rows = [
            {"agent": "n8n", "date": "2026-06-12", "sessions": 10, "token_status": "not_available", "node": "aliyun"},
            {"agent": "n8n", "date": "2026-06-12", "sessions": 3, "token_status": "not_available", "node": "aliyun"},
            {"agent": "Codex", "started_at": "2026-06-12T10:00:00+08:00", "sessions": 1, "total_tokens": 1000, "token_status": "ok", "node": "mba"},
        ]
        result = _activity_timeline(rows)
        n8n = next(row for row in result if row["agent"] == "n8n")
        codex = next(row for row in result if row["agent"] == "Codex")
        assert n8n["activity"] == 13
        assert n8n["total_tokens"] == 0
        assert codex["activity"] == 1
        assert codex["total_tokens"] == 1000


class TestN8nParsing:
    def test_parse_sectioned_tsv(self):
        payload = """__SUMMARY__
workflows	active_workflows	executions
85	13	10208
__WORKFLOWS__
workflow_id	workflow	executions	success	non_success	avg_duration_seconds	first_at	latest_at
abc	Mengniu	10	10	0	1.25	2026-06-13 01:00:00	2026-06-13 02:00:00
"""
        sections = _parse_sectioned_tsv(payload)
        assert sections["summary"][0]["workflows"] == "85"
        assert sections["workflows"][0]["workflow"] == "Mengniu"

    def test_n8n_records_are_activity_only(self):
        sections = {
            "summary": [
                {
                    "workflows": "85",
                    "active_workflows": "13",
                    "executions": "10208",
                    "success": "10197",
                    "non_success": "11",
                    "latest_at": "2026-06-13 02:44:42.022",
                }
            ],
            "workflows": [
                {
                    "workflow_id": "abc",
                    "workflow": "Mengniu",
                    "executions": "1645",
                    "success": "1645",
                    "non_success": "0",
                    "avg_duration_seconds": "2.5",
                    "first_at": "2026-06-13 01:00:00",
                    "latest_at": "2026-06-13 02:44:42.022",
                }
            ],
            "daily": [
                {
                    "date": "2026-06-13",
                    "workflow_id": "abc",
                    "workflow": "Mengniu",
                    "executions": "12",
                    "success": "11",
                    "non_success": "1",
                    "latest_at": "2026-06-13 02:44:42.022",
                }
            ],
        }
        records, summary = _n8n_records_from_sections(sections)
        timeline = _n8n_timeline_records_from_sections(sections)
        assert summary["executions"] == 10208
        assert records[0]["agent"] == "n8n"
        assert records[0]["project"] == "Mengniu"
        assert records[0]["sessions"] == 1645
        assert records[0]["token_status"] == "not_available"
        assert records[0]["total_tokens"] == 0
        assert _rank(records, ["agent"]) == []
        assert timeline[0]["agent"] == "n8n"
        assert timeline[0]["activity_count"] == 12
        assert timeline[0]["date"] == "2026-06-13"


class TestLocalAgentLedgerParsing:
    def test_local_records_from_ledger(self):
        ledger = {
            "totals": {
                "sessions": 2,
                "agents": 1,
                "projects": 1,
                "known_token_sessions": 2,
                "total_tokens": 3000,
                "known_cost_usd": 0.12,
            },
            "recent_sessions": [
                {"agent": "Codex", "project": "Smart Agent Ledger", "total_tokens": 1000},
                {"agent": "Codex", "project": "Smart Agent Ledger", "total_tokens": 2000},
            ],
        }
        records, summary = _local_records_from_ledger(ledger)
        assert len(records) == 2
        assert summary["sessions"] == 2
        assert summary["total_tokens"] == 3000
        assert _rank(records, ["agent"])[0]["agent"] == "Codex"

    def test_local_records_from_ledger_dedupes_export_snapshots(self):
        ledger = {
            "totals": {"sessions": 2, "agents": 1, "projects": 1, "total_tokens": 350, "known_token_sessions": 2},
            "recent_sessions": [
                {
                    "agent": "Codex",
                    "session_id": "s1",
                    "project": "Smart Agent Ledger",
                    "total_tokens": 100,
                    "raw_total_tokens": 100,
                    "token_status": "codex_token_count_event_window_full",
                    "estimated_cost_usd": 1.0,
                    "ended_at": "2026-06-10T00:00:00+00:00",
                },
                {
                    "agent": "Codex",
                    "session_id": "s1",
                    "project": "Smart Agent Ledger",
                    "total_tokens": 250,
                    "raw_total_tokens": 250,
                    "token_status": "codex_token_count_event_window_full",
                    "estimated_cost_usd": 2.5,
                    "ended_at": "2026-06-11T00:00:00+00:00",
                },
            ],
        }

        records, summary = _local_records_from_ledger(ledger)

        assert len(records) == 1
        assert records[0]["total_tokens"] == 250
        assert summary["sessions"] == 1
        assert summary["total_tokens"] == 250
        assert summary["known_cost_usd"] == pytest.approx(2.5)
        assert summary["dedupe_adjusted"] is True
        assert summary["raw_total_tokens"] == 350

    def test_local_records_from_ledger_filters_requested_window(self):
        now_epoch = dt.datetime(2026, 6, 24, tzinfo=dt.timezone.utc).timestamp()
        ledger = {
            "totals": {"sessions": 2, "agents": 1, "projects": 1, "total_tokens": 3000, "known_token_sessions": 2},
            "recent_sessions": [
                {
                    "agent": "Codex",
                    "project": "Smart Agent Ledger",
                    "total_tokens": 1000,
                    "token_status": "ok",
                    "ended_at": "2026-06-23T00:00:00+00:00",
                },
                {
                    "agent": "Codex",
                    "project": "Smart Agent Ledger",
                    "total_tokens": 2000,
                    "token_status": "ok",
                    "ended_at": "2026-05-01T00:00:00+00:00",
                },
            ],
        }

        records, summary = _local_records_from_ledger(ledger, days=30, now_epoch=now_epoch)

        assert len(records) == 1
        assert summary["sessions"] == 1
        assert summary["total_tokens"] == 1000
        assert summary["raw_total_tokens"] == 3000


def test_build_fleet_ledger_keeps_node_agent_model_dimensions(tmp_path, monkeypatch):
    import fleet_ledger
    config_path = tmp_path / "nodes.json"
    config_path.write_text(json.dumps({
        "schema_version": 1,
        "nodes": [{"name": "mba", "type": "local_agent_ledger", "enabled": True}],
    }))
    monkeypatch.setattr(fleet_ledger, "CONFIG_PATH", config_path)
    monkeypatch.setattr(
        fleet_ledger,
        "_build_local_agent_records",
        lambda days, limit: (
            [
                {
                    "agent": "Codex",
                    "project": "Smart Agent Ledger",
                    "model": "deepseek-chat",
                    "provider": "DeepSeek",
                    "total_tokens": 1000,
                    "known_token_sessions": 1,
                    "token_status": "ok",
                }
            ],
            {"sessions": 1, "agents": 1, "projects": 1, "total_tokens": 1000},
        ),
    )
    data = asyncio.run(build_fleet_ledger())
    assert data["agent_token_rank"][0]["agent"] == "Codex"
    assert data["project_token_rank"][0]["project"] == "Smart Agent Ledger"
    assert data["model_token_rank"][0]["model"] == "deepseek-chat"
    assert data["node_token_rank"][0]["node"] == "mba"
    assert data["node_activity_rank"][0]["node"] == "mba"
    assert data["node_agent_token_rank"][0]["node"] == "mba"
    assert all(row["agent"] != "DeepSeek" for row in data["agent_token_rank"])


def test_build_fleet_ledger_reuses_local_agent_cache(tmp_path, monkeypatch):
    import fleet_ledger
    config_path = tmp_path / "nodes.json"
    config_path.write_text(json.dumps({
        "schema_version": 1,
        "nodes": [{"name": "mba", "type": "local_agent_ledger", "enabled": True}],
    }))
    monkeypatch.setattr(fleet_ledger, "CONFIG_PATH", config_path)
    monkeypatch.setattr(
        fleet_ledger,
        "_build_local_agent_records",
        lambda days, limit: (_ for _ in ()).throw(AssertionError("cache should be reused")),
    )
    cached_ledger = {
        "_cache_age_seconds": 7,
        "totals": {"sessions": 1, "agents": 1, "projects": 1, "total_tokens": 1000, "known_token_sessions": 1},
        "recent_sessions": [
            {
                "agent": "Codex",
                "project": "Smart Agent Ledger",
                "model": "gpt-5",
                "total_tokens": 1000,
                "known_token_sessions": 1,
                "token_status": "ok",
            }
        ],
    }

    data = asyncio.run(build_fleet_ledger(local_agent_ledger=cached_ledger))

    assert data["nodes"][0]["node"] == "mba"
    assert data["nodes"][0]["status"] == "connected"
    assert data["nodes"][0]["cache_age_seconds"] == 7
    assert data["agent_token_rank"][0]["agent"] == "Codex"
    assert data["node_health"]["complete"] is True
    assert data["node_health"]["status"] == "complete"
    assert data["totals"]["data_complete"] is True


def test_build_fleet_ledger_uses_node_summary_for_totals(tmp_path, monkeypatch):
    import fleet_ledger
    config_path = tmp_path / "nodes.json"
    config_path.write_text(json.dumps({
        "schema_version": 1,
        "nodes": [{"name": "mba", "type": "local_agent_ledger", "enabled": True}],
    }))
    monkeypatch.setattr(fleet_ledger, "CONFIG_PATH", config_path)
    monkeypatch.setattr(
        fleet_ledger,
        "_build_local_agent_records",
        lambda days, limit: (_ for _ in ()).throw(AssertionError("cache should be reused")),
    )
    cached_ledger = {
        "totals": {
            "sessions": 3,
            "agents": 1,
            "projects": 1,
            "total_tokens": 5000,
            "known_token_sessions": 3,
            "known_cost_usd": 0.5,
            "known_cost_sessions": 2,
        },
        "recent_sessions": [
            {
                "agent": "Codex",
                "project": "Smart Agent Ledger",
                "model": "gpt-5",
                "total_tokens": 1000,
                "known_token_sessions": 1,
                "known_cost_usd": 0.1,
                "token_status": "ok",
            }
        ],
    }

    data = asyncio.run(build_fleet_ledger(local_agent_ledger=cached_ledger))

    assert data["totals"]["total_tokens"] == 5000
    assert data["totals"]["records"] == 3
    assert data["totals"]["known_token_records"] == 3
    assert data["totals"]["known_cost_usd"] == pytest.approx(0.5)
    assert data["totals"]["known_cost_sessions"] == 2
    assert data["totals"]["token_total_source"] == "node_summary"
    assert data["totals"]["summary_token_nodes"] == 1
    assert data["totals"]["summary_record_nodes"] == 1
    assert data["totals"]["row_sample_records"] == 1
    assert data["totals"]["row_sample_total_tokens"] == 1000
    assert data["nodes"][0]["records"] == 3
    assert data["nodes"][0]["sample_records"] == 1


def test_build_fleet_ledger_reports_data_quality_by_node(tmp_path, monkeypatch):
    import fleet_ledger
    config_path = tmp_path / "nodes.json"
    config_path.write_text(json.dumps({
        "schema_version": 1,
        "nodes": [
            {"name": "mba", "type": "local_agent_ledger", "enabled": True},
            {"name": "n8n", "type": "n8n_ssh", "host": "10.0.0.2", "ssh_key_path": "/tmp/key", "enabled": True},
            {"name": "demo-laptop", "type": "agent_ledger_file", "enabled": False},
        ],
    }))
    monkeypatch.setattr(fleet_ledger, "CONFIG_PATH", config_path)
    monkeypatch.setattr(
        fleet_ledger,
        "_build_local_agent_records",
        lambda days, limit: (_ for _ in ()).throw(AssertionError("cache should be reused")),
    )

    async def fake_fetch_n8n_node(node, days, limit, timeout_seconds):
        return (
            "n8n",
            "connected",
            [
                {
                    "agent": "n8n",
                    "project": "flow",
                    "source_type": "n8n_ssh",
                    "sessions": 5,
                    "total_tokens": 0,
                    "token_status": "not_available",
                }
            ],
            None,
            {
                "source_type": "n8n_ssh",
                "summary": {"executions": 5, "workflows": 2, "active_workflows": 1},
            },
        )

    monkeypatch.setattr(fleet_ledger, "_fetch_n8n_ssh_node", fake_fetch_n8n_node)
    cached_ledger = {
        "totals": {"sessions": 1, "agents": 1, "projects": 1, "total_tokens": 1000, "known_token_sessions": 1},
        "recent_sessions": [
            {
                "agent": "Codex",
                "project": "Smart Agent Ledger",
                "model": "gpt-5",
                "total_tokens": 1000,
                "known_token_sessions": 1,
                "token_status": "ok",
            }
        ],
    }

    data = asyncio.run(build_fleet_ledger(local_agent_ledger=cached_ledger))

    nodes = {row["node"]: row for row in data["nodes"]}
    assert nodes["mba"]["data_quality"] == "real"
    assert nodes["mba"]["token_included"] is True
    assert nodes["n8n"]["data_quality"] == "activity_only"
    assert nodes["n8n"]["token_included"] is False
    assert nodes["demo-laptop"]["data_quality"] == "unavailable"
    assert nodes["demo-laptop"]["token_included"] is False
    assert data["totals"]["real_token_nodes"] == 1
    assert data["totals"]["activity_only_nodes"] == 1
    assert data["totals"]["unavailable_nodes"] == 1


def test_build_fleet_ledger_reports_real_estimated_and_activity_breakdown(tmp_path, monkeypatch):
    import fleet_ledger
    config_path = tmp_path / "nodes.json"
    config_path.write_text(json.dumps({
        "schema_version": 1,
        "nodes": [
            {"name": "mba", "type": "local_agent_ledger", "enabled": True},
            {"name": "n8n", "type": "n8n_ssh", "host": "10.0.0.2", "ssh_key_path": "/tmp/key", "enabled": True},
        ],
    }))
    monkeypatch.setattr(fleet_ledger, "CONFIG_PATH", config_path)
    monkeypatch.setattr(
        fleet_ledger,
        "_build_local_agent_records",
        lambda days, limit: (_ for _ in ()).throw(AssertionError("cache should be reused")),
    )

    async def fake_fetch_n8n_node(node, days, limit, timeout_seconds):
        return (
            "n8n",
            "connected",
            [
                {
                    "agent": "n8n",
                    "project": "flow",
                    "source_type": "n8n_ssh",
                    "sessions": 7,
                    "total_tokens": 0,
                    "token_status": "not_available",
                }
            ],
            None,
            {
                "source_type": "n8n_ssh",
                "summary": {"executions": 7, "workflows": 2, "active_workflows": 1},
            },
        )

    monkeypatch.setattr(fleet_ledger, "_fetch_n8n_ssh_node", fake_fetch_n8n_node)
    cached_ledger = {
        "totals": {
            "sessions": 3,
            "agents": 2,
            "projects": 1,
            "total_tokens": 1400,
            "known_token_sessions": 2,
            "token_breakdown": {
                "real_token_records": 1,
                "real_total_tokens": 1000,
                "estimated_token_records": 1,
                "estimated_total_tokens": 400,
                "unavailable_token_records": 1,
                "included_token_records": 2,
                "included_total_tokens": 1400,
            },
        },
        "recent_sessions": [
            {
                "agent": "Codex",
                "project": "Smart Agent Ledger",
                "model": "gpt-5",
                "total_tokens": 1000,
                "known_token_sessions": 1,
                "token_status": "ok",
            },
            {
                "agent": "Trae",
                "project": "Smart Agent Ledger",
                "model": "unknown",
                "total_tokens": 400,
                "token_status": "estimated_from_turn_count",
            },
            {
                "agent": "Cursor",
                "project": "Smart Agent Ledger",
                "model": "unknown",
                "total_tokens": 0,
                "token_status": "pending_schema_mapping",
            },
        ],
    }

    data = asyncio.run(build_fleet_ledger(local_agent_ledger=cached_ledger))

    nodes = {row["node"]: row for row in data["nodes"]}
    assert nodes["mba"]["data_quality"] == "real"
    assert nodes["mba"]["real_token_total"] == 1000
    assert nodes["mba"]["estimated_token_total"] == 400
    assert nodes["n8n"]["data_quality"] == "activity_only"
    assert data["totals"]["total_tokens"] == 1400
    assert data["totals"]["real_total_tokens"] == 1000
    assert data["totals"]["estimated_total_tokens"] == 400
    assert data["totals"]["unavailable_token_records"] == 2
    assert data["totals"]["real_token_nodes"] == 1
    assert data["totals"]["activity_only_nodes"] == 1
    assert data["totals"]["estimated_token_nodes"] == 0


def test_build_fleet_ledger_adds_node_dashboard_metrics(tmp_path, monkeypatch):
    import fleet_ledger
    missing_export_path = tmp_path / "missing-agent-ledger.json"
    config_path = tmp_path / "nodes.json"
    config_path.write_text(json.dumps({
        "schema_version": 1,
        "nodes": [
            {"name": "mba", "type": "local_agent_ledger", "enabled": True},
            {"name": "n8n", "type": "n8n_ssh", "host": "10.0.0.2", "ssh_key_path": "/tmp/key", "enabled": True},
            {
                "name": "demo-laptop",
                "type": "agent_ledger_file",
                "ledger_path": str(missing_export_path),
                "enabled": True,
            },
        ],
    }))
    monkeypatch.setattr(fleet_ledger, "CONFIG_PATH", config_path)
    monkeypatch.setattr(
        fleet_ledger,
        "_build_local_agent_records",
        lambda days, limit: (_ for _ in ()).throw(AssertionError("cache should be reused")),
    )

    async def fake_fetch_n8n_node(node, days, limit, timeout_seconds):
        return (
            "n8n",
            "connected",
            [
                {
                    "agent": "n8n",
                    "project": "flow",
                    "source_type": "n8n_ssh",
                    "sessions": 5,
                    "activity_count": 5,
                    "latest_at": "2026-06-16T12:05:00+00:00",
                    "total_tokens": 0,
                    "token_status": "not_available",
                }
            ],
            None,
            {
                "source_type": "n8n_ssh",
                "summary": {
                    "executions": 5,
                    "workflows": 2,
                    "active_workflows": 1,
                    "latest_at": "2026-06-16T12:05:00+00:00",
                },
            },
        )

    monkeypatch.setattr(fleet_ledger, "_fetch_n8n_ssh_node", fake_fetch_n8n_node)
    cached_ledger = {
        "totals": {
            "sessions": 1,
            "agents": 1,
            "projects": 1,
            "total_tokens": 1000,
            "known_token_sessions": 1,
            "known_cost_usd": 2.5,
            "known_cost_sessions": 1,
        },
        "recent_sessions": [
            {
                "agent": "Codex",
                "project": "Smart Agent Ledger",
                "model": "gpt-5",
                "started_at": "2026-06-16T12:00:00+00:00",
                "ended_at": "2026-06-16T12:01:00+00:00",
                "total_tokens": 1000,
                "known_token_sessions": 1,
                "known_cost_usd": 2.5,
                "token_status": "ok",
            }
        ],
    }

    data = asyncio.run(build_fleet_ledger(local_agent_ledger=cached_ledger))

    nodes = {row["node"]: row for row in data["nodes"]}
    assert nodes["mba"]["token_total"] == 1000
    assert nodes["mba"]["known_token_records"] == 1
    assert nodes["mba"]["known_cost_usd"] == 2.5
    assert nodes["mba"]["activity_count"] == 1
    assert nodes["mba"]["latest_at"] == "2026-06-16T12:01:00+00:00"
    assert nodes["n8n"]["token_total"] == 0
    assert nodes["n8n"]["activity_count"] == 5
    assert nodes["n8n"]["latest_at"] == "2026-06-16T12:05:00+00:00"
    assert nodes["demo-laptop"]["issue"]
    assert nodes["demo-laptop"]["activity_count"] == 0
    assert nodes["demo-laptop"]["token_total"] == 0


def test_build_fleet_ledger_respects_usage_event_source_node(tmp_path, monkeypatch):
    import fleet_ledger
    config_path = tmp_path / "nodes.json"
    config_path.write_text(json.dumps({
        "schema_version": 1,
        "nodes": [{"name": "collector-laptop", "type": "local_agent_ledger", "enabled": True}],
    }))
    monkeypatch.setattr(fleet_ledger, "CONFIG_PATH", config_path)
    monkeypatch.setattr(
        fleet_ledger,
        "_build_local_agent_records",
        lambda days, limit: (_ for _ in ()).throw(AssertionError("cache should be reused")),
    )
    cached_ledger = {
        "totals": {"sessions": 1, "agents": 1, "projects": 1, "total_tokens": 1234, "known_token_sessions": 1},
        "recent_sessions": [
            {
                "agent": "n8n",
                "source_node": "automation-n8n",
                "project": "Mengniu",
                "model": "deepseek-chat",
                "total_tokens": 1234,
                "known_token_sessions": 1,
                "token_status": "n8n_reported",
            }
        ],
    }

    data = asyncio.run(build_fleet_ledger(local_agent_ledger=cached_ledger))

    assert data["agent_token_rank"][0]["agent"] == "n8n"
    assert data["node_token_rank"][0]["node"] == "automation-n8n"
    assert data["node_activity_rank"][0]["node"] == "automation-n8n"


def test_build_fleet_ledger_reads_agent_ledger_file_node(tmp_path, monkeypatch):
    import fleet_ledger
    export_path = tmp_path / "demo-main-agent-ledger.json"
    export_path.write_text(json.dumps({
        "generated_at": "2026-06-13T12:00:00+08:00",
        "totals": {"sessions": 2, "total_tokens": 3000},
        "recent_sessions": [
            {
                "agent": "Codex",
                "project": "Smart Agent Ledger",
                "model": "gpt-5",
                "total_tokens": 3000,
                "known_token_sessions": 1,
                "token_status": "ok",
            }
        ],
    }), encoding="utf-8")
    config_path = tmp_path / "nodes.json"
    config_path.write_text(json.dumps({
        "schema_version": 1,
        "nodes": [
            {
                "name": "company-main",
                "type": "agent_ledger_file",
                "ledger_path": str(export_path),
                "max_export_age_seconds": 10_000_000,
                "enabled": True,
            }
        ],
    }), encoding="utf-8")
    monkeypatch.setattr(fleet_ledger, "CONFIG_PATH", config_path)

    data = asyncio.run(build_fleet_ledger())

    assert data["nodes"][0]["node"] == "company-main"
    assert data["nodes"][0]["status"] == "connected"
    assert data["nodes"][0]["source_type"] == "agent_ledger_file"
    assert data["agent_token_rank"][0]["agent"] == "Codex"
    assert data["node_token_rank"][0]["node"] == "company-main"
    assert data["node_activity_rank"][0]["node"] == "company-main"


def test_agent_ledger_file_node_filters_to_requested_window(tmp_path, monkeypatch):
    import fleet_ledger

    monkeypatch.setattr(
        fleet_ledger,
        "_now",
        lambda: dt.datetime(2026, 6, 24, tzinfo=dt.timezone.utc),
    )
    export_path = tmp_path / "demo-laptop-agent-ledger.json"
    export_path.write_text(json.dumps({
        "generated_at": "2026-06-24T00:00:00+00:00",
        "window_days": 90,
        "totals": {"sessions": 2, "agents": 1, "projects": 1, "known_token_sessions": 2, "total_tokens": 3000},
        "recent_sessions": [
            {
                "session_id": "recent",
                "agent": "Codex",
                "project": "Smart Agent Ledger",
                "model": "gpt-5",
                "total_tokens": 1000,
                "known_token_sessions": 1,
                "token_status": "ok",
                "ended_at": "2026-06-23T00:00:00+00:00",
            },
            {
                "session_id": "old",
                "agent": "Codex",
                "project": "Smart Agent Ledger",
                "model": "gpt-5",
                "total_tokens": 2000,
                "known_token_sessions": 1,
                "token_status": "ok",
                "ended_at": "2026-05-01T00:00:00+00:00",
            },
        ],
    }), encoding="utf-8")
    config_path = tmp_path / "nodes.json"
    config_path.write_text(json.dumps({
        "schema_version": 1,
        "nodes": [
            {
                "name": "collector-laptop",
                "type": "agent_ledger_file",
                "ledger_path": str(export_path),
                "enabled": True,
            }
        ],
    }), encoding="utf-8")
    monkeypatch.setattr(fleet_ledger, "CONFIG_PATH", config_path)

    data = asyncio.run(build_fleet_ledger(days=30))

    assert data["totals"]["total_tokens"] == 1000
    assert data["totals"]["records"] == 1
    assert data["nodes"][0]["summary"]["raw_total_tokens"] == 3000


def test_agent_ledger_file_node_marks_stale_export_as_issue(tmp_path, monkeypatch):
    import fleet_ledger

    monkeypatch.setattr(
        fleet_ledger,
        "_now",
        lambda: dt.datetime(2026, 6, 24, tzinfo=dt.timezone.utc),
    )
    export_path = tmp_path / "demo-laptop-agent-ledger.json"
    export_path.write_text(json.dumps({
        "generated_at": "2026-06-17T00:00:00+00:00",
        "totals": {"sessions": 1, "agents": 1, "projects": 1, "known_token_sessions": 1, "total_tokens": 3000},
        "recent_sessions": [
            {
                "session_id": "s1",
                "agent": "Codex",
                "project": "Smart Agent Ledger",
                "model": "gpt-5",
                "total_tokens": 3000,
                "known_token_sessions": 1,
                "token_status": "ok",
                "ended_at": "2026-06-17T00:00:00+00:00",
            }
        ],
    }), encoding="utf-8")
    config_path = tmp_path / "nodes.json"
    config_path.write_text(json.dumps({
        "schema_version": 1,
        "nodes": [
            {
                "name": "collector-laptop",
                "type": "agent_ledger_file",
                "ledger_path": str(export_path),
                "max_export_age_seconds": 60,
                "enabled": True,
            }
        ],
    }), encoding="utf-8")
    monkeypatch.setattr(fleet_ledger, "CONFIG_PATH", config_path)

    data = asyncio.run(build_fleet_ledger(days=30))

    assert data["totals"]["data_complete"] is False
    assert data["totals"]["total_tokens"] == 0
    assert data["totals"]["known_token_records"] == 0
    assert data["totals"]["excluded_stale_nodes"] == 1
    assert data["totals"]["excluded_stale_total_tokens"] == 3000
    assert data["totals"]["excluded_stale_token_records"] == 1
    assert data["totals"]["current_data_nodes"] == 0
    assert data["totals"]["stale_nodes"] == 1
    assert data["node_health"]["current_data_node_count"] == 0
    assert data["node_health"]["stale_node_count"] == 1
    assert data["node_health"]["stale_nodes"] == ["collector-laptop"]
    assert data["node_health"]["excluded_nodes"] == ["collector-laptop"]
    assert data["nodes"][0]["export_stale"] is True
    assert "只读账本服务" in data["nodes"][0]["operator_hint"]
    assert data["nodes"][0]["data_quality"] == "stale"
    assert data["nodes"][0]["current_data_included"] is False
    assert data["nodes"][0]["token_total"] == 3000
    assert data["node_token_rank"] == []
    assert data["access_issues"][0]["node"] == "collector-laptop"
    assert "ledger export is stale" in data["access_issues"][0]["issue"]


def test_build_fleet_ledger_keeps_stale_file_out_of_current_totals(tmp_path, monkeypatch):
    import fleet_ledger

    monkeypatch.setattr(
        fleet_ledger,
        "_now",
        lambda: dt.datetime(2026, 6, 24, tzinfo=dt.timezone.utc),
    )
    export_path = tmp_path / "demo-laptop-agent-ledger.json"
    export_path.write_text(json.dumps({
        "generated_at": "2026-06-17T00:00:00+00:00",
        "totals": {"sessions": 1, "agents": 1, "projects": 1, "known_token_sessions": 1, "total_tokens": 3000},
        "recent_sessions": [
            {
                "session_id": "s1",
                "agent": "Codex",
                "project": "collector laptop Project",
                "model": "gpt-5",
                "total_tokens": 3000,
                "known_token_sessions": 1,
                "token_status": "ok",
                "ended_at": "2026-06-17T00:00:00+00:00",
            }
        ],
    }), encoding="utf-8")
    config_path = tmp_path / "nodes.json"
    config_path.write_text(json.dumps({
        "schema_version": 1,
        "nodes": [
            {"name": "demo-main", "type": "local_agent_ledger", "enabled": True},
            {
                "name": "demo-laptop",
                "type": "agent_ledger_file",
                "ledger_path": str(export_path),
                "max_export_age_seconds": 60,
                "enabled": True,
            },
        ],
    }), encoding="utf-8")
    monkeypatch.setattr(fleet_ledger, "CONFIG_PATH", config_path)
    monkeypatch.setattr(
        fleet_ledger,
        "_build_local_agent_records",
        lambda days, limit: (_ for _ in ()).throw(AssertionError("cache should be reused")),
    )
    cached_ledger = {
        "totals": {"sessions": 1, "agents": 1, "projects": 1, "total_tokens": 1000, "known_token_sessions": 1},
        "recent_sessions": [
            {
                "agent": "Codex",
                "project": "main collector Project",
                "model": "gpt-5",
                "total_tokens": 1000,
                "known_token_sessions": 1,
                "token_status": "ok",
            }
        ],
    }

    data = asyncio.run(build_fleet_ledger(days=30, local_agent_ledger=cached_ledger))

    assert data["totals"]["total_tokens"] == 1000
    assert data["totals"]["excluded_stale_total_tokens"] == 3000
    assert data["totals"]["current_data_nodes"] == 1
    assert data["totals"]["stale_nodes"] == 1
    assert data["node_health"]["current_data_node_count"] == 1
    assert data["node_health"]["stale_node_count"] == 1
    assert data["node_health"]["stale_nodes"] == ["demo-laptop"]
    assert [row["node"] for row in data["node_token_rank"]] == ["demo-main"]


def test_agent_ledger_file_node_uses_last_good_cache_when_file_unavailable(tmp_path, monkeypatch):
    import fleet_ledger

    monkeypatch.setattr(fleet_ledger, "AGENT_LEDGER_FILE_CACHE_DIR", tmp_path / "file-cache")
    export_path = tmp_path / "demo-laptop-agent-ledger.json"
    export_path.write_text(json.dumps({
        "generated_at": "2026-06-16T03:37:00+00:00",
        "totals": {"sessions": 1, "agents": 1, "projects": 1, "known_token_sessions": 1, "total_tokens": 3000},
        "recent_sessions": [
            {
                "session_id": "s1",
                "agent": "Codex",
                "project": "Smart Agent Ledger",
                "model": "gpt-5",
                "total_tokens": 3000,
                "known_token_sessions": 1,
                "token_status": "ok",
            }
        ],
    }), encoding="utf-8")
    config_path = tmp_path / "nodes.json"
    config_path.write_text(json.dumps({
        "schema_version": 1,
        "nodes": [
            {
                "name": "collector-laptop",
                "type": "agent_ledger_file",
                "ledger_path": str(export_path),
                "max_export_age_seconds": 10_000_000,
                "enabled": True,
            }
        ],
    }), encoding="utf-8")
    monkeypatch.setattr(fleet_ledger, "CONFIG_PATH", config_path)

    first = asyncio.run(build_fleet_ledger())
    export_path.unlink()
    second = asyncio.run(build_fleet_ledger())

    assert first["totals"]["data_complete"] is True
    assert second["totals"]["data_complete"] is False
    assert second["totals"]["connected_nodes"] == 1
    assert second["totals"]["node_issue_count"] == 1
    assert second["totals"]["stale_nodes"] == 1
    assert second["totals"]["total_tokens"] == 3000
    assert second["access_issues"] == []
    assert second["node_health"]["status"] == "partial"
    assert second["node_health"]["complete"] is False
    assert second["node_health"]["stale_nodes"] == ["collector-laptop"]
    assert second["nodes"][0]["status"] == "connected"
    assert second["nodes"][0]["ledger_cache_status"] == "stale"
    assert second["nodes"][0]["stale_ledger_cache"] is True


def test_fetch_remote_gateway_node_uses_ledger_summary_totals(tmp_path, monkeypatch):
    import fleet_ledger
    monkeypatch.setattr(fleet_ledger, "AGENT_LEDGER_FILE_CACHE_DIR", tmp_path)

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "totals": {
                    "sessions": 25,
                    "agents": 2,
                    "projects": 3,
                    "known_token_sessions": 20,
                    "total_tokens": 9999,
                    "known_cost_usd": 12.5,
                    "known_cost_sessions": 20,
                },
                "recent_sessions": [
                    {
                        "session_id": "sample",
                        "agent": "Codex",
                        "project": "Smart Agent Ledger",
                        "total_tokens": 111,
                        "known_token_sessions": 1,
                        "token_status": "ok",
                    }
                ],
    }

    class FakeClient:
        async def get(self, url, timeout=None):
            assert url == "http://demo-laptop.local:8001/agent-ledger?days=90&limit=1"
            assert timeout == fleet_ledger.AGENT_LEDGER_HTTP_TIMEOUT_MAX_SECONDS
            return FakeResponse()

    result = asyncio.run(fleet_ledger._fetch_node(
        FakeClient(),
        {"name": "demo-laptop-http", "base_url": "http://demo-laptop.local:8001", "timeout_seconds": 60},
        days=90,
        limit=1,
        timeout_seconds=4,
    ))

    name, status, records, issue, meta = result
    assert name == "demo-laptop-http"
    assert status == "connected"
    assert issue is None
    assert len(records) == 1
    assert meta["source_type"] == "smart_gateway"
    assert meta["summary"]["total_tokens"] == 9999
    assert meta["summary"]["known_token_sessions"] == 20
    assert meta["summary"]["known_cost_usd"] == 12.5


def test_fetch_remote_gateway_node_tries_base_url_candidates(tmp_path, monkeypatch):
    import fleet_ledger
    monkeypatch.setattr(fleet_ledger, "AGENT_LEDGER_FILE_CACHE_DIR", tmp_path)

    class FakeResponse:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    class FakeClient:
        def __init__(self):
            self.urls = []

        async def get(self, url, timeout=None):
            self.urls.append(url)
            if url.startswith("http://old-ip.local:8002"):
                raise httpx.ConnectError("connection refused")
            return FakeResponse({
                "totals": {"sessions": 2, "known_token_sessions": 1, "total_tokens": 2222},
                "recent_sessions": [
                    {"agent": "Codex", "project": "Gateway", "total_tokens": 2222, "token_status": "ok"},
                ],
            })

    client = FakeClient()
    result = asyncio.run(fleet_ledger._fetch_node(
        client,
        {
            "name": "demo-laptop",
            "base_url": "http://old-ip.local:8002",
            "base_url_candidates": ["http://192.0.2.63:8002"],
            "timeout_seconds": 60,
        },
        days=90,
        limit=120,
        timeout_seconds=4,
    ))

    name, status, records, issue, meta = result

    assert name == "demo-laptop"
    assert status == "connected"
    assert issue is None
    assert len(records) == 1
    assert client.urls == [
        "http://old-ip.local:8002/agent-ledger?days=90&limit=120",
        "http://192.0.2.63:8002/agent-ledger?days=90&limit=120",
    ]
    assert meta["resolved_url"] == "http://192.0.2.63:8002/agent-ledger?days=90&limit=120"
    assert meta["attempted_urls"] == client.urls


def test_fetch_remote_gateway_node_reports_actionable_http_issue(tmp_path, monkeypatch):
    import fleet_ledger
    monkeypatch.setattr(fleet_ledger, "AGENT_LEDGER_FILE_CACHE_DIR", tmp_path)

    class FakeClient:
        async def get(self, url, timeout=None):
            raise httpx.ConnectError("connection refused")

    result = asyncio.run(fleet_ledger._fetch_node(
        FakeClient(),
        {
            "name": "demo-laptop",
            "base_url": "http://192.0.2.63:8002",
            "base_url_candidates": ["http://demo-laptop.local:8002"],
            "timeout_seconds": 60,
        },
        days=90,
        limit=120,
        timeout_seconds=4,
    ))

    name, status, records, issue, meta = result

    assert name == "demo-laptop"
    assert status == "unreachable"
    assert records == []
    assert "collector laptop" in issue
    assert "同一 Wi-Fi" in issue
    assert "8002" in issue
    assert meta["attempted_urls"] == [
        "http://192.0.2.63:8002/agent-ledger?days=90&limit=120",
        "http://demo-laptop.local:8002/agent-ledger?days=90&limit=120",
    ]
    assert meta["operator_hint"]


def test_fetch_remote_gateway_node_uses_stale_http_cache_after_outage(tmp_path, monkeypatch):
    import fleet_ledger

    monkeypatch.setattr(fleet_ledger, "AGENT_LEDGER_FILE_CACHE_DIR", tmp_path)
    monkeypatch.setattr(fleet_ledger, "AGENT_LEDGER_HTTP_CACHE_FRESH_SECONDS", 0)

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "totals": {"sessions": 2, "known_token_sessions": 1, "total_tokens": 2222},
                "recent_sessions": [
                    {"agent": "Codex", "project": "Gateway", "total_tokens": 2222, "token_status": "ok"},
                ],
            }

    class HealthyClient:
        async def get(self, url, timeout=None):
            return FakeResponse()

    class OfflineClient:
        def __init__(self):
            self.timeouts = []

        async def get(self, url, timeout=None):
            self.timeouts.append(timeout)
            raise httpx.ConnectError("connection refused")

    node = {"name": "demo-laptop", "base_url": "http://192.0.2.63:8002", "timeout_seconds": 60}

    first = asyncio.run(fleet_ledger._fetch_node(HealthyClient(), node, days=90, limit=120, timeout_seconds=4))
    offline_client = OfflineClient()
    second = asyncio.run(fleet_ledger._fetch_node(offline_client, node, days=90, limit=120, timeout_seconds=4))

    assert first[1] == "connected"
    name, status, records, issue, meta = second
    assert name == "demo-laptop"
    assert status == "connected"
    assert issue is None
    assert records[0]["total_tokens"] == 2222
    assert meta["summary"]["total_tokens"] == 2222
    assert meta["stale_ledger_cache"] is True
    assert meta["ledger_cache_status"] == "stale_http"
    assert "connection refused" in meta["ledger_cache_issue"]
    assert offline_client.timeouts == [fleet_ledger.AGENT_LEDGER_HTTP_STALE_REFRESH_TIMEOUT_SECONDS]


def test_fetch_remote_gateway_node_marks_readonly_cache_fallback_stale(tmp_path, monkeypatch):
    import fleet_ledger

    monkeypatch.setattr(fleet_ledger, "AGENT_LEDGER_FILE_CACHE_DIR", tmp_path)

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "window_days": 30,
                "_stale": True,
                "_refreshing": True,
                "_ledger_cache_fallback": True,
                "_ledger_cache_status": "stale_readonly",
                "_cache_age_seconds": 321,
                "totals": {"sessions": 1, "known_token_sessions": 1, "total_tokens": 2222},
                "recent_sessions": [
                    {"agent": "Codex", "project": "Gateway", "total_tokens": 2222, "token_status": "ok"},
                ],
            }

    class FakeClient:
        async def get(self, url, timeout=None):
            return FakeResponse()

    name, status, records, issue, meta = asyncio.run(fleet_ledger._fetch_node(
        FakeClient(),
        {"name": "demo-laptop", "base_url": "http://100.64.0.9:8002"},
        days=30,
        limit=120,
        timeout_seconds=4,
    ))

    assert name == "demo-laptop"
    assert status == "connected"
    assert issue is None
    assert records[0]["total_tokens"] == 2222
    assert meta["stale_ledger_cache"] is True
    assert meta["ledger_cache_status"] == "stale_readonly"
    assert meta["ledger_cache_age_seconds"] == 321


def test_fetch_remote_gateway_node_uses_fresh_http_cache_without_network(tmp_path, monkeypatch):
    import fleet_ledger

    monkeypatch.setattr(fleet_ledger, "AGENT_LEDGER_FILE_CACHE_DIR", tmp_path)
    monkeypatch.setattr(fleet_ledger, "AGENT_LEDGER_HTTP_CACHE_FRESH_SECONDS", 300)

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "totals": {"sessions": 2, "known_token_sessions": 1, "total_tokens": 2222},
                "recent_sessions": [
                    {"agent": "Codex", "project": "Gateway", "total_tokens": 2222, "token_status": "ok"},
                ],
            }

    class HealthyClient:
        async def get(self, url, timeout=None):
            return FakeResponse()

    class CountingClient:
        def __init__(self):
            self.calls = 0

        async def get(self, url, timeout=None):
            self.calls += 1
            raise AssertionError("fresh cache should avoid remote fetch")

    node = {"name": "demo-laptop", "base_url": "http://192.0.2.63:8002", "timeout_seconds": 60}

    first = asyncio.run(fleet_ledger._fetch_node(HealthyClient(), node, days=90, limit=120, timeout_seconds=4))
    client = CountingClient()
    second = asyncio.run(fleet_ledger._fetch_node(client, node, days=90, limit=120, timeout_seconds=4))

    assert first[1] == "connected"
    name, status, records, issue, meta = second
    assert client.calls == 0
    assert name == "demo-laptop"
    assert status == "connected"
    assert issue is None
    assert records[0]["total_tokens"] == 2222
    assert meta["summary"]["total_tokens"] == 2222
    assert meta["ledger_cache_status"] == "fresh_http"
    assert meta["stale_ledger_cache"] is False


def test_fetch_remote_gateway_node_cache_is_scoped_by_window_url(tmp_path, monkeypatch):
    import fleet_ledger

    monkeypatch.setattr(fleet_ledger, "AGENT_LEDGER_FILE_CACHE_DIR", tmp_path)
    monkeypatch.setattr(fleet_ledger, "AGENT_LEDGER_HTTP_CACHE_FRESH_SECONDS", 300)

    class FakeResponse:
        def __init__(self, tokens):
            self.tokens = tokens

        def raise_for_status(self):
            return None

        def json(self):
            return {
                "totals": {"sessions": 1, "known_token_sessions": 1, "total_tokens": self.tokens},
                "recent_sessions": [
                    {"agent": "Codex", "project": "Gateway", "total_tokens": self.tokens, "token_status": "ok"},
                ],
            }

    class WindowAwareClient:
        def __init__(self):
            self.urls = []

        async def get(self, url, timeout=None):
            self.urls.append(url)
            return FakeResponse(3000 if "days=30" in url else 9000)

    node = {"name": "demo-laptop", "base_url": "http://192.0.2.63:8002", "timeout_seconds": 60}
    client = WindowAwareClient()

    first = asyncio.run(fleet_ledger._fetch_node(client, node, days=30, limit=120, timeout_seconds=4))
    second = asyncio.run(fleet_ledger._fetch_node(client, node, days=90, limit=120, timeout_seconds=4))

    assert first[4]["summary"]["total_tokens"] == 3000
    assert second[4]["summary"]["total_tokens"] == 9000
    assert client.urls == [
        "http://192.0.2.63:8002/agent-ledger?days=30&limit=120",
        "http://192.0.2.63:8002/agent-ledger?days=90&limit=120",
    ]


def test_build_fleet_ledger_reports_partial_node_health(tmp_path, monkeypatch):
    import fleet_ledger
    missing_export_path = tmp_path / "missing-agent-ledger.json"
    config_path = tmp_path / "nodes.json"
    config_path.write_text(json.dumps({
        "schema_version": 1,
        "nodes": [
            {"name": "mba", "type": "local_agent_ledger", "enabled": True},
            {
                "name": "company-main",
                "type": "agent_ledger_file",
                "ledger_path": str(missing_export_path),
                "enabled": True,
            },
        ],
    }), encoding="utf-8")
    monkeypatch.setattr(fleet_ledger, "CONFIG_PATH", config_path)
    monkeypatch.setattr(
        fleet_ledger,
        "_build_local_agent_records",
        lambda days, limit: (_ for _ in ()).throw(AssertionError("cache should be reused")),
    )
    cached_ledger = {
        "totals": {"sessions": 1, "agents": 1, "projects": 1, "total_tokens": 1000, "known_token_sessions": 1},
        "recent_sessions": [
            {
                "agent": "Codex",
                "project": "Smart Agent Ledger",
                "model": "gpt-5",
                "total_tokens": 1000,
                "known_token_sessions": 1,
                "token_status": "ok",
            }
        ],
    }

    data = asyncio.run(build_fleet_ledger(local_agent_ledger=cached_ledger))

    assert data["totals"]["configured_nodes"] == 2
    assert data["totals"]["connected_nodes"] == 1
    assert data["totals"]["data_complete"] is False
    assert data["totals"]["node_issue_count"] == 1
    assert data["node_health"]["status"] == "partial"
    assert data["node_health"]["complete"] is False
    assert data["node_health"]["unavailable_nodes"] == ["company-main"]


def test_build_fleet_ledger_marks_cached_http_node_as_degraded(tmp_path, monkeypatch):
    import fleet_ledger
    config_path = tmp_path / "nodes.json"
    config_path.write_text(json.dumps({
        "schema_version": 1,
        "nodes": [
            {"name": "demo-laptop", "base_url": "http://100.64.0.9:8002", "enabled": True},
        ],
    }), encoding="utf-8")
    monkeypatch.setattr(fleet_ledger, "CONFIG_PATH", config_path)

    async def fake_fetch_node(client, node, days, limit, timeout_seconds):
        return (
            "demo-laptop",
            "connected",
            [
                {
                    "agent": "Codex",
                    "project": "Smart Agent Ledger",
                    "model": "gpt-5",
                    "total_tokens": 2222,
                    "known_token_sessions": 1,
                    "token_status": "ok",
                }
            ],
            None,
            {
                "source_type": "smart_gateway",
                "summary": {
                    "sessions": 1,
                    "known_token_sessions": 1,
                    "total_tokens": 2222,
                },
                "stale_ledger_cache": True,
                "ledger_cache_status": "stale_http",
                "ledger_cache_age_seconds": 7200,
            },
        )

    monkeypatch.setattr(fleet_ledger, "_fetch_node", fake_fetch_node)

    data = asyncio.run(build_fleet_ledger(days=30))

    assert data["totals"]["total_tokens"] == 2222
    assert data["totals"]["current_data_nodes"] == 1
    assert data["totals"]["stale_nodes"] == 1
    assert data["totals"]["data_complete"] is False
    assert data["totals"]["node_issue_count"] == 1
    assert data["nodes"][0]["current_data_included"] is True
    assert data["nodes"][0]["stale_ledger_cache"] is True
    assert data["node_health"]["status"] == "partial"
    assert data["node_health"]["complete"] is False
    assert data["node_health"]["current_data_node_count"] == 1
    assert data["node_health"]["stale_node_count"] == 1
    assert data["node_health"]["stale_nodes"] == ["demo-laptop"]
    assert data["node_health"]["excluded_nodes"] == ["demo-laptop"]
    assert data["data_trust"]["scope"] == "fleet"
    assert data["data_trust"]["status"] == "partial"
    assert data["data_trust"]["score"] < 100
    assert data["data_trust"]["stale_nodes"] == ["demo-laptop"]
    assert "has_stale_nodes" in data["data_trust"]["reasons"]


def test_build_fleet_ledger_limits_cached_local_records_without_changing_summary(tmp_path, monkeypatch):
    import fleet_ledger
    config_path = tmp_path / "nodes.json"
    config_path.write_text(json.dumps({
        "schema_version": 1,
        "nodes": [{"name": "mba", "type": "local_agent_ledger", "enabled": True}],
    }), encoding="utf-8")
    monkeypatch.setattr(fleet_ledger, "CONFIG_PATH", config_path)
    cached_ledger = {
        "totals": {"sessions": 2, "agents": 1, "projects": 1, "total_tokens": 3000, "known_token_sessions": 2},
        "recent_sessions": [
            {
                "agent": "Codex",
                "session_id": "s1",
                "project": "Smart Agent Ledger",
                "total_tokens": 1000,
                "known_token_sessions": 1,
                "token_status": "ok",
            },
            {
                "agent": "Codex",
                "session_id": "s2",
                "project": "Smart Agent Ledger",
                "total_tokens": 2000,
                "known_token_sessions": 1,
                "token_status": "ok",
            },
        ],
    }

    data = asyncio.run(build_fleet_ledger(limit=1, local_agent_ledger=cached_ledger))

    assert data["nodes"][0]["records"] == 2
    assert data["nodes"][0]["sample_records"] == 1
    assert data["totals"]["records"] == 2
    assert data["totals"]["row_sample_records"] == 1
    assert data["totals"]["total_tokens"] == 3000
    assert data["totals"]["row_sample_total_tokens"] == 1000


# ── 节点注册 / 移除 (#2 Fleet 接入) ─────────────────────────────────────────


class TestRegisterNode:
    def test_adds_new_node(self, tmp_path, monkeypatch):
        import fleet_ledger
        monkeypatch.setattr(fleet_ledger, "CONFIG_PATH", tmp_path / "nodes.json")
        result = register_node("dev-1", "http://192.0.2.100:8001")
        assert result["action"] == "added"
        assert result["node"]["name"] == "dev-1"
        # 验证已写入磁盘
        config = _load_config()
        assert len(config["nodes"]) == 1
        assert config["nodes"][0]["base_url"] == "http://192.0.2.100:8001"
        assert config["nodes"][0]["enabled"] is True

    def test_updates_existing_node_by_name(self, tmp_path, monkeypatch):
        import fleet_ledger
        config_path = tmp_path / "nodes.json"
        monkeypatch.setattr(fleet_ledger, "CONFIG_PATH", config_path)
        register_node("dev-1", "http://10.0.0.1:8001")
        # 再次注册同名, 更新 base_url
        result = register_node("dev-1", "http://10.0.0.2:8001", enabled=False)
        assert result["action"] == "updated"
        config = _load_config()
        assert len(config["nodes"]) == 1  # 没有重复
        assert config["nodes"][0]["base_url"] == "http://10.0.0.2:8001"
        assert config["nodes"][0]["enabled"] is False

    def test_updates_existing_node_by_base_url(self, tmp_path, monkeypatch):
        import fleet_ledger
        monkeypatch.setattr(fleet_ledger, "CONFIG_PATH", tmp_path / "nodes.json")
        register_node("dev-1", "http://10.0.0.1:8001")
        # 同 base_url 不同 name → 更新而非新增
        result = register_node("dev-1-renamed", "http://10.0.0.1:8001")
        assert result["action"] == "updated"
        config = _load_config()
        assert len(config["nodes"]) == 1

    def test_adds_multiple_nodes(self, tmp_path, monkeypatch):
        import fleet_ledger
        monkeypatch.setattr(fleet_ledger, "CONFIG_PATH", tmp_path / "nodes.json")
        register_node("dev-1", "http://10.0.0.1:8001")
        register_node("dev-2", "http://10.0.0.2:8001")
        register_node("dev-3", "http://10.0.0.3:8001")
        config = _load_config()
        assert len(config["nodes"]) == 3

    def test_preserves_other_fields(self, tmp_path, monkeypatch):
        import fleet_ledger
        config_path = tmp_path / "nodes.json"
        config_path.write_text(json.dumps({
            "schema_version": 1,
            "nodes": [{"name": "dev-1", "base_url": "http://10.0.0.1:8001", "custom": "keep"}],
            "authorized_networks": ["10.0.0.0/24"],
        }))
        monkeypatch.setattr(fleet_ledger, "CONFIG_PATH", config_path)
        register_node("dev-1", "http://10.0.0.9:8001")
        config = _load_config()
        assert config["authorized_networks"] == ["10.0.0.0/24"]  # 保留
        assert config["nodes"][0].get("custom") == "keep"  # 保留额外字段

    def test_ledger_url_optional(self, tmp_path, monkeypatch):
        import fleet_ledger
        monkeypatch.setattr(fleet_ledger, "CONFIG_PATH", tmp_path / "nodes.json")
        result = register_node("dev-1", "http://10.0.0.1:8001", ledger_url="http://10.0.0.1:8001/custom")
        assert result["node"]["ledger_url"] == "http://10.0.0.1:8001/custom"

    def test_register_node_keeps_candidate_addresses_and_timeout(self, tmp_path, monkeypatch):
        import fleet_ledger

        monkeypatch.setattr(fleet_ledger, "CONFIG_PATH", tmp_path / "nodes.json")
        result = register_node(
            "demo-laptop",
            "http://192.0.2.63:8002",
            base_url_candidates=["http://demo-laptop.local:8002", "http://100.64.1.2:8002"],
            host="192.0.2.63",
            role="agent_ledger_readonly_collector",
            timeout_seconds=60,
        )

        assert result["node"]["base_url_candidates"] == ["http://demo-laptop.local:8002", "http://100.64.1.2:8002"]
        assert result["node"]["host"] == "192.0.2.63"
        assert result["node"]["role"] == "agent_ledger_readonly_collector"
        assert result["node"]["timeout_seconds"] == 60


class TestRemoveNode:
    def test_removes_by_name(self, tmp_path, monkeypatch):
        import fleet_ledger
        monkeypatch.setattr(fleet_ledger, "CONFIG_PATH", tmp_path / "nodes.json")
        register_node("dev-1", "http://10.0.0.1:8001")
        register_node("dev-2", "http://10.0.0.2:8001")
        result = remove_node("dev-1")
        assert result["removed"] == 1
        config = _load_config()
        assert len(config["nodes"]) == 1
        assert config["nodes"][0]["name"] == "dev-2"

    def test_remove_nonexistent(self, tmp_path, monkeypatch):
        import fleet_ledger
        monkeypatch.setattr(fleet_ledger, "CONFIG_PATH", tmp_path / "nodes.json")
        register_node("dev-1", "http://10.0.0.1:8001")
        result = remove_node("ghost")
        assert result["removed"] == 0
        config = _load_config()
        assert len(config["nodes"]) == 1  # 未变

    def test_remove_from_empty_config(self, tmp_path, monkeypatch):
        import fleet_ledger
        monkeypatch.setattr(fleet_ledger, "CONFIG_PATH", tmp_path / "nodes.json")
        result = remove_node("anything")
        assert result["removed"] == 0
