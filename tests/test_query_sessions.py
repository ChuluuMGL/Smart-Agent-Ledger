"""测试 agent_ledger.query_sessions — 会话明细筛选/排序/分页 (#11)。"""
import pytest

from agent_ledger import query_sessions

# 预构造测试数据 (避免依赖真实采集)
ROWS = [
    {"agent": "Codex", "project": "AppA", "total_tokens": 5000,
     "estimated_cost_usd": 1.5, "cost_status": "pricing_table_estimate",
     "started_at": "2026-06-10T10:00:00Z"},
    {"agent": "Codex", "project": "AppB", "total_tokens": 1000,
     "estimated_cost_usd": 0.3, "cost_status": "pricing_table_estimate",
     "started_at": "2026-06-11T10:00:00Z"},
    {"agent": "Hermes", "project": "AppA", "total_tokens": 200,
     "started_at": "2026-06-09T10:00:00Z"},
    {"agent": "Hermes", "project": "AppC", "total_tokens": 50000,
     "estimated_cost_usd": 8.0, "cost_status": "pricing_table_estimate",
     "started_at": "2026-06-12T10:00:00Z"},
]


class TestFiltering:
    def test_no_filter_returns_all(self):
        r = query_sessions(rows=ROWS, page_size=100)
        assert r["total"] == 4

    def test_filter_by_agent(self):
        r = query_sessions(agent="Codex", rows=ROWS, page_size=100)
        assert r["total"] == 2
        assert all(s["agent"] == "Codex" for s in r["sessions"])

    def test_filter_by_project(self):
        r = query_sessions(project="AppA", rows=ROWS, page_size=100)
        assert r["total"] == 2
        assert all(s["project"] == "AppA" for s in r["sessions"])

    def test_filter_min_tokens(self):
        r = query_sessions(min_tokens=1000, rows=ROWS, page_size=100)
        assert r["total"] == 3  # 5000, 1000, 50000
        assert all(s["total_tokens"] >= 1000 for s in r["sessions"])

    def test_filter_combination(self):
        r = query_sessions(agent="Codex", project="AppA", rows=ROWS, page_size=100)
        assert r["total"] == 1
        assert r["sessions"][0]["total_tokens"] == 5000

    def test_filter_no_match(self):
        r = query_sessions(agent="Nonexistent", rows=ROWS, page_size=100)
        assert r["total"] == 0
        assert r["sessions"] == []


class TestSorting:
    def test_sort_by_token_desc(self):
        r = query_sessions(sort="token", rows=ROWS, page_size=100)
        tokens = [s["total_tokens"] for s in r["sessions"]]
        assert tokens == sorted(tokens, reverse=True)
        assert tokens[0] == 50000

    def test_sort_by_cost_desc(self):
        r = query_sessions(sort="cost", rows=ROWS, page_size=100)
        costs = [s.get("estimated_cost_usd") or 0 for s in r["sessions"]]
        assert costs == sorted(costs, reverse=True)
        assert costs[0] == 8.0

    def test_sort_default_time_desc(self):
        r = query_sessions(sort="time", rows=ROWS, page_size=100)
        # Hermes AppC 2026-06-12 最新
        assert r["sessions"][0]["started_at"] == "2026-06-12T10:00:00Z"


class TestPagination:
    def test_page_size_limit(self):
        r = query_sessions(rows=ROWS, page=1, page_size=2)
        assert len(r["sessions"]) == 2
        assert r["total"] == 4
        assert r["has_more"] is True

    def test_second_page(self):
        r = query_sessions(rows=ROWS, page=2, page_size=2)
        assert len(r["sessions"]) == 2
        assert r["has_more"] is False

    def test_last_partial_page(self):
        r = query_sessions(rows=ROWS, page=2, page_size=3)
        assert len(r["sessions"]) == 1  # 4 total, 3 per page → page 2 has 1
        assert r["has_more"] is False

    def test_beyond_last_page_empty(self):
        r = query_sessions(rows=ROWS, page=10, page_size=2)
        assert r["sessions"] == []
        assert r["has_more"] is False

    def test_page_size_capped_at_500(self):
        r = query_sessions(rows=ROWS, page_size=99999)
        assert r["page_size"] == 500

    def test_page_minimum_1(self):
        r = query_sessions(rows=ROWS, page=0, page_size=10)
        assert r["page"] == 1


class TestResponseStructure:
    def test_returns_all_fields(self):
        r = query_sessions(rows=ROWS, page=1, page_size=10)
        assert set(r.keys()) == {"sessions", "total", "page", "page_size", "has_more"}

    def test_empty_input(self):
        r = query_sessions(rows=[], page=1, page_size=10)
        assert r["total"] == 0
        assert r["sessions"] == []
        assert r["has_more"] is False
