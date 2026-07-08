"""测试 agent_ledger.py 中的 _aggregate_by 聚合逻辑。"""
import pytest

from agent_ledger import _aggregate_by, build_agent_ledger


def _row(
    project: str = "proj-a",
    agent: str = "claude",
    task: str = "implement",
    session_count: int = 1,
    message_count: int = 10,
    tool_call_count: int = 5,
    total_tokens: int = 1000,
    token_status: str = "ok",
    lines_added: int = 0,
    lines_removed: int = 0,
    files_changed: int = 0,
    actual_cost_usd: float = None,
    estimated_cost_usd: float = None,
    cost_status: str = "ok",
    status: str = "completed",
    started_at: str = "2026-06-07T10:00:00+08:00",
    ended_at: str = "2026-06-07T11:00:00+08:00",
) -> dict:
    """构建一行聚合输入数据。"""
    row = {
        "project": project,
        "agent": agent,
        "task": task,
        "session_count": session_count,
        "message_count": message_count,
        "tool_call_count": tool_call_count,
        "total_tokens": total_tokens,
        "token_status": token_status,
        "lines_added": lines_added,
        "lines_removed": lines_removed,
        "files_changed": files_changed,
        "cost_status": cost_status,
        "status": status,
        "started_at": started_at,
        "ended_at": ended_at,
    }
    if actual_cost_usd is not None:
        row["actual_cost_usd"] = actual_cost_usd
    if estimated_cost_usd is not None:
        row["estimated_cost_usd"] = estimated_cost_usd
    return row


def test_build_agent_ledger_dedupes_cumulative_session_rows(monkeypatch):
    rows = [
        {
            "agent": "Codex",
            "session_id": "codex-session",
            "project": "Smart Agent Ledger",
            "task": "first snapshot",
            "total_tokens": 100,
            "raw_total_tokens": 100,
            "token_status": "codex_token_count_event_window_full",
            "ended_at": "2026-06-10T00:00:00+00:00",
        },
        {
            "agent": "Codex",
            "session_id": "codex-session",
            "project": "Smart Agent Ledger",
            "task": "latest snapshot",
            "total_tokens": 250,
            "raw_total_tokens": 250,
            "token_status": "codex_token_count_event_window_full",
            "ended_at": "2026-06-11T00:00:00+00:00",
        },
        {
            "agent": "n8n",
            "session_id": "workflow-run",
            "project": "n8n flow",
            "task": "provider call",
            "total_tokens": 20,
            "token_status": "n8n_reported",
            "ended_at": "2026-06-11T01:00:00+00:00",
        },
        {
            "agent": "n8n",
            "session_id": "workflow-run",
            "project": "n8n flow",
            "task": "provider call",
            "total_tokens": 30,
            "token_status": "n8n_reported",
            "ended_at": "2026-06-11T02:00:00+00:00",
        },
    ]
    monkeypatch.setattr("agent_ledger.collect_sessions", lambda days: (rows, []))

    data = build_agent_ledger(days=30, limit=20)

    assert data["totals"]["sessions"] == 3
    assert data["totals"]["total_tokens"] == 300
    assert len(data["recent_sessions"]) == 3


def test_build_agent_ledger_reports_token_breakdown(monkeypatch):
    rows = [
        _row(agent="Codex", total_tokens=1000, token_status="codex_token_count_event_window_full"),
        _row(agent="Trae", total_tokens=400, token_status="estimated_from_turn_count"),
        _row(agent="Cursor", total_tokens=0, token_status="pending_schema_mapping"),
    ]
    monkeypatch.setattr("agent_ledger.collect_sessions", lambda days: (rows, []))

    data = build_agent_ledger(days=30, limit=20)

    assert data["totals"]["total_tokens"] == 1400
    assert data["totals"]["real_total_tokens"] == 1000
    assert data["totals"]["estimated_total_tokens"] == 400
    assert data["totals"]["unavailable_token_sessions"] == 1
    assert data["totals"]["token_breakdown"] == {
        "real_token_records": 1,
        "real_total_tokens": 1000,
        "estimated_token_records": 1,
        "estimated_total_tokens": 400,
        "unavailable_token_records": 1,
        "included_token_records": 2,
        "included_total_tokens": 1400,
    }
    assert data["data_trust"]["scope"] == "local"
    assert data["data_trust"]["status"] == "partial"
    assert data["data_trust"]["score"] > 0
    assert data["data_trust"]["included_token_records"] == 2
    assert "includes_estimated_tokens" in data["data_trust"]["reasons"]


# ── _aggregate_by 按 project ───────────────────────────────────────────────


class TestAggregateByProject:
    def test_single_row(self):
        rows = [_row(project="proj-a")]
        result = _aggregate_by(rows, "project")
        assert len(result) == 1
        assert result[0]["project"] == "proj-a"
        assert result[0]["sessions"] == 1
        assert result[0]["messages"] == 10

    def test_two_projects(self):
        rows = [
            _row(project="proj-a", message_count=5),
            _row(project="proj-b", message_count=15),
        ]
        result = _aggregate_by(rows, "project")
        assert len(result) == 2
        projects = {r["project"] for r in result}
        assert projects == {"proj-a", "proj-b"}

    def test_same_project_merged(self):
        rows = [
            _row(project="proj-a", message_count=5, total_tokens=100),
            _row(project="proj-a", message_count=10, total_tokens=200),
        ]
        result = _aggregate_by(rows, "project")
        assert len(result) == 1
        assert result[0]["sessions"] == 2
        assert result[0]["messages"] == 15
        assert result[0]["total_tokens"] == 300

    def test_agents_collected_per_project(self):
        rows = [
            _row(project="proj-a", agent="claude"),
            _row(project="proj-a", agent="cursor"),
        ]
        result = _aggregate_by(rows, "project")
        assert result[0]["agents"] == ["claude", "cursor"]

    def test_unknown_field_defaults(self):
        """字段缺失时用 "unknown" 作为 key。"""
        rows = [_row(project=None)]
        result = _aggregate_by(rows, "project")
        assert result[0]["project"] == "unknown"


# ── _aggregate_by 按其他字段 ───────────────────────────────────────────────


class TestAggregateByAgent:
    def test_group_by_agent(self):
        rows = [
            _row(agent="claude", project="p1"),
            _row(agent="cursor", project="p2"),
            _row(agent="claude", project="p1"),
        ]
        result = _aggregate_by(rows, "agent")
        assert len(result) == 2
        claude_group = next(r for r in result if r["agent"] == "claude")
        assert claude_group["sessions"] == 2
        assert claude_group["projects"] == ["p1"]


class TestAggregateByTask:
    def test_group_by_task(self):
        rows = [
            _row(task="debug", agent="claude"),
            _row(task="refactor", agent="cursor"),
        ]
        result = _aggregate_by(rows, "task")
        assert len(result) == 2
        tasks = {r["task"] for r in result}
        assert tasks == {"debug", "refactor"}


# ── 成本聚合 ────────────────────────────────────────────────────────────────


class TestAggregateCost:
    def test_known_cost_summed(self):
        rows = [
            _row(actual_cost_usd=0.05),
            _row(actual_cost_usd=0.10),
        ]
        result = _aggregate_by(rows, "project")
        assert result[0]["known_cost_usd"] == pytest.approx(0.15)
        assert result[0]["known_cost_sessions"] == 2

    def test_unknown_cost_tracked(self):
        rows = [
            _row(actual_cost_usd=None, estimated_cost_usd=None, cost_status="unknown"),
        ]
        result = _aggregate_by(rows, "project")
        assert result[0]["unknown_cost_sessions"] == 1
        assert result[0]["known_cost_sessions"] == 0

    def test_mixed_cost(self):
        rows = [
            _row(actual_cost_usd=0.05),
            _row(actual_cost_usd=None, estimated_cost_usd=None, cost_status="unknown"),
        ]
        result = _aggregate_by(rows, "project")
        assert result[0]["known_cost_sessions"] == 1
        assert result[0]["unknown_cost_sessions"] == 1


# ── token 状态 ──────────────────────────────────────────────────────────────


class TestAggregateTokens:
    def test_tokens_known(self):
        rows = [_row(total_tokens=500, token_status="ok")]
        result = _aggregate_by(rows, "project")
        assert result[0]["known_token_sessions"] == 1

    def test_tokens_not_available(self):
        rows = [_row(total_tokens=0, token_status="not_available")]
        result = _aggregate_by(rows, "project")
        assert result[0]["known_token_sessions"] == 0


# ── active sessions ────────────────────────────────────────────────────────


class TestAggregateActiveSessions:
    def test_active_sessions_counted(self):
        rows = [
            _row(status="active"),
            _row(status="completed"),
            _row(status="recent"),
        ]
        result = _aggregate_by(rows, "project")
        assert result[0]["active_sessions"] == 2  # active + recent

    def test_no_active_sessions(self):
        rows = [_row(status="completed")]
        result = _aggregate_by(rows, "project")
        assert result[0]["active_sessions"] == 0


# ── 排序 ────────────────────────────────────────────────────────────────────


class TestAggregateSortOrder:
    def test_sorted_by_active_sessions_desc(self):
        rows = [
            _row(project="inactive", status="completed", started_at="2026-06-07T10:00:00+08:00", ended_at="2026-06-07T11:00:00+08:00"),
            _row(project="active", status="active", started_at="2026-06-07T10:00:00+08:00", ended_at="2026-06-07T11:00:00+08:00"),
        ]
        result = _aggregate_by(rows, "project")
        assert result[0]["project"] == "active"

    def test_empty_input(self):
        result = _aggregate_by([], "project")
        assert result == []


# ── Trae collector helpers ──────────────────────────────────────────────────


class TestTraeModelNameCleaning:
    """测试 _clean_trae_model_name 的 N_-_ 前缀剥离。"""

    def test_strip_numeric_prefix(self):
        from agent_ledger import _clean_trae_model_name

        assert _clean_trae_model_name("1_-_gpt-5") == "gpt-5"
        assert _clean_trae_model_name("1_-_gemini-3-pro") == "gemini-3-pro"
        assert _clean_trae_model_name("1_-_gpt-5.3-codex") == "gpt-5.3-codex"
        assert _clean_trae_model_name("2_-_kimi-k2-0905") == "kimi-k2-0905"

    def test_none_returns_none(self):
        from agent_ledger import _clean_trae_model_name

        assert _clean_trae_model_name(None) is None

    def test_empty_returns_none(self):
        from agent_ledger import _clean_trae_model_name

        assert _clean_trae_model_name("") is None

    def test_no_prefix_returns_as_is(self):
        from agent_ledger import _clean_trae_model_name

        assert _clean_trae_model_name("gpt-5") == "gpt-5"
        assert _clean_trae_model_name("gemini-3-pro") == "gemini-3-pro"


class TestTraeSnapshotTurns:
    """测试 _trae_snapshot_turns 从 git snapshot tags 计数 turns。"""

    def test_counts_before_tags(self, tmp_path):
        from agent_ledger import _trae_snapshot_turns

        tags_dir = tmp_path / "abc123" / "v2" / ".git" / "refs" / "tags"
        tags_dir.mkdir(parents=True)
        (tags_dir / "before-chat-turn-001").touch()
        (tags_dir / "before-chat-turn-002").touch()
        (tags_dir / "after-chat-turn-001").touch()
        (tags_dir / "after-chat-turn-002").touch()
        result = _trae_snapshot_turns(tmp_path, "abc123")
        assert result["turns"] == 2
        assert result["started_at"] is not None
        assert result["ended_at"] is not None

    def test_no_v2_dir_returns_zero(self, tmp_path):
        from agent_ledger import _trae_snapshot_turns

        result = _trae_snapshot_turns(tmp_path, "nonexistent")
        assert result["turns"] == 0
        assert result["started_at"] is None
        assert result["ended_at"] is None

    def test_empty_tags_dir_returns_zero(self, tmp_path):
        from agent_ledger import _trae_snapshot_turns

        tags_dir = tmp_path / "abc123" / "v2" / ".git" / "refs" / "tags"
        tags_dir.mkdir(parents=True)
        result = _trae_snapshot_turns(tmp_path, "abc123")
        assert result["turns"] == 0


class TestTraeCollector:
    """测试 collect_trae_sessions 整体行为。"""

    def test_returns_empty_if_no_trae_dir(self, monkeypatch, tmp_path):
        """如果没有 Trae 目录，返回空列表。"""
        from agent_ledger import collect_trae_sessions

        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
        result = collect_trae_sessions(30)
        assert result == []

    def test_real_trae_data_structure(self):
        """集成测试：如果有真实 Trae 数据，验证行结构。"""
        from agent_ledger import collect_trae_sessions

        rows = collect_trae_sessions(365)
        if not rows:
            pytest.skip("No Trae data on this machine")

        for row in rows:
            assert row["agent"] in ("Trae", "TRAE SOLO")
            assert "session_id" in row
            assert row["source"] == "snapshot+workspaceStorage"
            assert row["token_status"] in (
                "estimated_from_turn_count",
                "pending_schema_mapping",
            )
            assert isinstance(row["total_tokens"], int)
            assert isinstance(row["input_tokens"], int)
            assert isinstance(row["output_tokens"], int)
            assert row["total_tokens"] == row["input_tokens"] + row["output_tokens"]
            assert row["confidence"] in (
                "turn_count_estimation",
                "workspace_metadata",
            )
            # 必须有的标准字段
            for field in (
                "agent", "source", "session_id", "project", "task",
                "status", "started_at", "ended_at", "model", "provider",
                "token_status", "cost_status", "raw_path",
            ):
                assert field in row, f"Missing field: {field}"
