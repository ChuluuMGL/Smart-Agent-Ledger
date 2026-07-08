"""测试 collector_utils.py 中的纯逻辑工具函数 (从 agent_ledger.py 拆分)。"""
import datetime as dt
import pathlib

import pytest

from collector_utils import (
    UNKNOWN_COST_STATUSES,
    _content_text,
    _cost_is_known,
    _is_agent_row,
    _path_exists_any,
    _path_from_file_uri,
    _row_cost,
    _safe_title,
    _shorten,
    _strip_environment_context,
    _tokens_are_known,
    _within_window,
    normalize_project_name,
    project_from_cwd,
)


# ── 文本工具 ────────────────────────────────────────────────────────────────


class TestShorten:
    def test_short_text_unchanged(self):
        assert _shorten("hello") == "hello"

    def test_exact_limit_unchanged(self):
        assert _shorten("a" * 120, limit=120) == "a" * 120

    def test_truncated_with_ellipsis(self):
        result = _shorten("a" * 200, limit=50)
        assert len(result) == 49 + 1  # 49 chars + …
        assert result.endswith("…")

    def test_collapses_whitespace(self):
        assert _shorten("hello    world") == "hello world"

    def test_strips_outer_whitespace(self):
        assert _shorten("  hi  ") == "hi"

    def test_none_becomes_empty(self):
        assert _shorten(None) == ""

    def test_non_string_coerced(self):
        assert _shorten(12345) == "12345"


class TestStripEnvironmentContext:
    def test_removes_environment_context_tags(self):
        text = "before <environment_context>secret</environment_context> after"
        assert _strip_environment_context(text) == "before after"

    def test_removes_generic_tags(self):
        assert _strip_environment_context("a <foo>bar</foo> b") == "a bar b"

    def test_collapses_whitespace(self):
        assert _strip_environment_context("a   b") == "a b"

    def test_case_insensitive(self):
        text = "<ENVIRONMENT_CONTEXT>x</ENVIRONMENT_CONTEXT>y"
        assert _strip_environment_context(text) == "y"


class TestContentText:
    def test_string_passthrough(self):
        assert _content_text("hello") == "hello"

    def test_list_of_dicts(self):
        content = [{"text": "a"}, {"text": "b"}]
        assert _content_text(content) == "a b"

    def test_list_uses_content_key(self):
        content = [{"content": "x"}]
        assert _content_text(content) == "x"

    def test_dict(self):
        assert _content_text({"text": "hi"}) == "hi"
        assert _content_text({"content": "yo"}) == "yo"

    def test_none(self):
        assert _content_text(None) == ""

    def test_list_of_mixed(self):
        assert _content_text([{"text": "a"}, "b"]) == "a b"


class TestSafeTitle:
    def test_normal_text(self):
        assert _safe_title("Hello World", "fallback") == "Hello World"

    def test_think_prefix_returns_fallback(self):
        assert _safe_title("<think>reasoning", "fallback") == "fallback"

    def test_empty_returns_fallback(self):
        assert _safe_title("", "fallback") == "fallback"

    def test_strips_tags(self):
        assert _safe_title("<tool>a</tool>b", "fallback") == "a b"


# ── 路径 / 项目名 ───────────────────────────────────────────────────────────


class TestProjectFromCwd:
    def test_ai_workspace_marker(self):
        cwd = "/Users/x/AI-Workspace/shared/projects/Smart-Agent-Ledger"
        assert project_from_cwd(cwd) == "Smart-Agent-Ledger"

    def test_documents_work_projects_marker(self):
        cwd = "/home/u/Documents/Work/Projects/MyApp"
        assert project_from_cwd(cwd) == "MyApp"

    def test_clients_marker_takes_two_parts(self):
        cwd = "/home/u/Documents/Work/Clients/ACME/Website"
        assert project_from_cwd(cwd) == "ACME/Website"

    def test_no_marker_returns_dirname(self):
        assert project_from_cwd("/tmp/random-project") == "random-project"

    def test_none_returns_unknown(self):
        assert project_from_cwd(None) == "unknown"

    def test_empty_returns_unknown(self):
        assert project_from_cwd("") == "unknown"

    def test_root_returns_unknown(self):
        assert project_from_cwd("/") == "unknown"

    def test_project_aliases_normalize_workspace_path(self, tmp_path, monkeypatch):
        import project_attribution

        alias_path = tmp_path / "project-aliases.json"
        alias_path.write_text(
            """
{
  "aliases": [
    {
      "canonical": "Gateway",
      "match_names": ["Smart-Agent-Ledger"],
      "path_contains": ["Smart Agent Ledger"]
    }
  ]
}
""".strip(),
            encoding="utf-8",
        )
        monkeypatch.setattr(project_attribution, "PROJECT_ALIASES_PATH", alias_path)
        project_attribution._ALIASES_CACHE.clear()
        project_attribution._ALIASES_CACHE.update({"mtime": None, "rules": []})

        cwd = "/Users/x/AI-Workspace/shared/projects/Smart Agent Ledger"
        assert project_from_cwd(cwd) == "Gateway"

    def test_project_aliases_normalize_explicit_project(self, tmp_path, monkeypatch):
        import project_attribution

        alias_path = tmp_path / "project-aliases.json"
        alias_path.write_text(
            '{"aliases": [{"canonical": "Client Site", "match_names": ["Website"]}]}',
            encoding="utf-8",
        )
        monkeypatch.setattr(project_attribution, "PROJECT_ALIASES_PATH", alias_path)
        project_attribution._ALIASES_CACHE.clear()
        project_attribution._ALIASES_CACHE.update({"mtime": None, "rules": []})

        assert normalize_project_name("Website") == "Client Site"


class TestPathExistsAny:
    def test_existing_path(self, tmp_path):
        f = tmp_path / "a.txt"
        f.write_text("x")
        assert _path_exists_any([f]) is True

    def test_one_of_many_exists(self, tmp_path):
        missing = tmp_path / "no1"
        exists = tmp_path / "yes"
        exists.write_text("x")
        assert _path_exists_any([missing, exists]) is True

    def test_none_exist(self, tmp_path):
        assert _path_exists_any([tmp_path / "a", tmp_path / "b"]) is False

    def test_empty_iterable(self):
        assert _path_exists_any([]) is False


class TestPathFromFileUri:
    def test_file_uri(self):
        assert _path_from_file_uri("file:///Users/x/proj") == "/Users/x/proj"

    def test_plain_path(self):
        assert _path_from_file_uri("/Users/x/proj") == "/Users/x/proj"

    def test_none(self):
        assert _path_from_file_uri(None) is None

    def test_empty(self):
        assert _path_from_file_uri("") is None

    def test_encoded_uri(self):
        # %20 = space
        assert _path_from_file_uri("file:///Users/x/my%20proj") == "/Users/x/my proj"


# ── 时间窗口 ────────────────────────────────────────────────────────────────


class TestWithinWindow:
    def test_recent_is_within(self):
        cutoff = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
        recent = "2026-06-01T00:00:00Z"
        assert _within_window(recent, cutoff) is True

    def test_old_is_outside(self):
        cutoff = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
        old = "2025-01-01T00:00:00Z"
        assert _within_window(old, cutoff) is False

    def test_none_outside(self):
        cutoff = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
        assert _within_window(None, cutoff) is False

    def test_invalid_outside(self):
        cutoff = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
        assert _within_window("not-a-date", cutoff) is False


# ── 费用 / token 行判断 ─────────────────────────────────────────────────────


class TestCostIsKnown:
    def test_actual_cost_known(self):
        assert _cost_is_known({"actual_cost_usd": 1.5}) is True

    def test_estimated_with_known_status(self):
        assert _cost_is_known({"estimated_cost_usd": 0.5, "cost_status": "pricing_table_estimate"}) is True

    def test_estimated_with_unknown_status(self):
        assert _cost_is_known({"estimated_cost_usd": 0.5, "cost_status": "unknown"}) is False

    def test_no_cost(self):
        assert _cost_is_known({}) is False

    def test_all_unknown_statuses_rejected(self):
        for status in UNKNOWN_COST_STATUSES:
            assert _cost_is_known({"estimated_cost_usd": 1.0, "cost_status": status}) is False


class TestRowCost:
    def test_actual_preferred(self):
        assert _row_cost({"actual_cost_usd": 2.0, "estimated_cost_usd": 1.0}) == 2.0

    def test_estimated_fallback(self):
        assert _row_cost({"estimated_cost_usd": 1.0, "cost_status": "known"}) == 1.0

    def test_unknown_returns_none(self):
        assert _row_cost({"estimated_cost_usd": 1.0, "cost_status": "unknown"}) is None

    def test_empty_returns_none(self):
        assert _row_cost({}) is None


class TestTokensAreKnown:
    def test_positive_tokens(self):
        assert _tokens_are_known({"total_tokens": 100}) is True

    def test_zero_tokens(self):
        assert _tokens_are_known({"total_tokens": 0}) is False

    def test_not_available_status(self):
        assert _tokens_are_known({"total_tokens": 100, "token_status": "not_available"}) is False

    def test_unknown_status(self):
        assert _tokens_are_known({"total_tokens": 100, "token_status": "unknown"}) is False

    def test_status_only(self):
        assert _tokens_are_known({"total_tokens": 100, "token_status": "status_only"}) is False

    def test_pending_schema_mapping(self):
        assert _tokens_are_known({"total_tokens": 100, "token_status": "pending_schema_mapping"}) is False

    def test_reported_status_with_tokens(self):
        assert _tokens_are_known({"total_tokens": 50, "token_status": "hermes_state_db"}) is True


class TestIsAgentRow:
    def test_normal_agent(self):
        assert _is_agent_row({"agent": "Codex"}) is True

    def test_infrastructure_excluded(self):
        assert _is_agent_row({"agent": "LiteLLM"}) is False

    def test_empty_agent(self):
        # empty string is not in INFRASTRUCTURE_COMPONENTS
        assert _is_agent_row({"agent": ""}) is True


# ── agent_collectors.py 纯逻辑辅助 ──────────────────────────────────────────

from agent_collectors import (
    _claude_session_usage,
    _codex_token_usage,
    _subtract_token_usage,
)


class TestCodexTokenUsage:
    def test_full_usage(self):
        payload = {"info": {"total_token_usage": {
            "input_tokens": 100,
            "cached_input_tokens": 50,
            "output_tokens": 200,
            "reasoning_output_tokens": 30,
            "total_tokens": 380,
        }}}
        result = _codex_token_usage(payload)
        assert result["input_tokens"] == 150  # 100 + 50 cached
        assert result["output_tokens"] == 230  # 200 + 30 reasoning
        assert result["cached_input_tokens"] == 50
        assert result["reasoning_output_tokens"] == 30
        assert result["raw_total_tokens"] == 380
        assert result["total_tokens"] == 380  # 150 + 230

    def test_missing_usage(self):
        assert _codex_token_usage({})["total_tokens"] == 0
        assert _codex_token_usage({"info": {}})["input_tokens"] == 0

    def test_partial_usage(self):
        payload = {"info": {"total_token_usage": {"input_tokens": 10}}}
        result = _codex_token_usage(payload)
        assert result["input_tokens"] == 10
        assert result["output_tokens"] == 0
        assert result["total_tokens"] == 10

    def test_total_includes_all_components(self):
        """total_tokens = input + cached + output + reasoning."""
        payload = {"info": {"total_token_usage": {
            "input_tokens": 1, "cached_input_tokens": 2,
            "output_tokens": 3, "reasoning_output_tokens": 4,
        }}}
        assert _codex_token_usage(payload)["total_tokens"] == 10


class TestSubtractTokenUsage:
    def test_simple_subtraction(self):
        current = {"input_tokens": 100, "output_tokens": 50,
                    "cached_input_tokens": 0, "reasoning_output_tokens": 0,
                    "raw_total_tokens": 150, "total_tokens": 150}
        baseline = {"input_tokens": 30, "output_tokens": 10,
                     "cached_input_tokens": 0, "reasoning_output_tokens": 0,
                     "raw_total_tokens": 40, "total_tokens": 40}
        result = _subtract_token_usage(current, baseline)
        assert result["input_tokens"] == 70
        assert result["output_tokens"] == 40
        assert result["total_tokens"] == 110

    def test_floor_at_zero(self):
        """结果不应为负。"""
        current = {"input_tokens": 5, "output_tokens": 5,
                    "cached_input_tokens": 0, "reasoning_output_tokens": 0,
                    "raw_total_tokens": 10, "total_tokens": 10}
        baseline = {"input_tokens": 100, "output_tokens": 100,
                     "cached_input_tokens": 0, "reasoning_output_tokens": 0,
                     "raw_total_tokens": 200, "total_tokens": 200}
        result = _subtract_token_usage(current, baseline)
        assert all(v >= 0 for v in result.values())
        assert result["input_tokens"] == 0

    def test_all_keys_present(self):
        keys = ["input_tokens", "output_tokens", "cached_input_tokens",
                "reasoning_output_tokens", "raw_total_tokens", "total_tokens"]
        result = _subtract_token_usage({k: 0 for k in keys}, {k: 0 for k in keys})
        assert set(result.keys()) == set(keys)


class TestClaudeSessionUsage:
    def test_parses_assistant_messages(self, tmp_path):
        import json as _json
        f = tmp_path / "session.jsonl"
        lines = [
            {"type": "user", "message": {"content": "hi"}},
            {"type": "assistant", "message": {"model": "claude-sonnet-4",
                "usage": {"input_tokens": 100, "output_tokens": 50}}},
            {"type": "assistant", "message": {"model": "claude-sonnet-4",
                "usage": {"input_tokens": 20, "output_tokens": 10,
                           "cache_read_input_tokens": 5, "cache_creation_input_tokens": 3}}},
        ]
        f.write_text("\n".join(_json.dumps(l) for l in lines))
        result = _claude_session_usage(f)
        # input = 100 + 20 + 5(cache_read) + 3(cache_creation) = 128
        assert result["input_tokens"] == 128
        assert result["output_tokens"] == 60
        assert result["total_tokens"] == 188
        assert "claude-sonnet-4" in result["model"]

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.jsonl"
        f.write_text("")
        result = _claude_session_usage(f)
        assert result["input_tokens"] == 0
        assert result["output_tokens"] == 0
        assert result["model"] is None

    def test_only_user_messages(self, tmp_path):
        import json as _json
        f = tmp_path / "session.jsonl"
        f.write_text(_json.dumps({"type": "user", "message": {"content": "q"}}))
        result = _claude_session_usage(f)
        assert result["total_tokens"] == 0

    def test_multiple_models_joined(self, tmp_path):
        import json as _json
        f = tmp_path / "session.jsonl"
        lines = [
            {"type": "assistant", "message": {"model": "claude-opus-4", "usage": {"input_tokens": 1, "output_tokens": 1}}},
            {"type": "assistant", "message": {"model": "claude-haiku", "usage": {"input_tokens": 1, "output_tokens": 1}}},
        ]
        f.write_text("\n".join(_json.dumps(l) for l in lines))
        result = _claude_session_usage(f)
        assert "claude-opus-4" in result["model"]
        assert "claude-haiku" in result["model"]
