def _fleet_payload():
    return {
        "totals": {
            "configured_nodes": 2,
            "connected_nodes": 2,
            "data_complete": True,
            "total_tokens": 1_500_000,
            "real_total_tokens": 1_000_000,
            "estimated_total_tokens": 500_000,
            "known_token_records": 3,
            "unavailable_token_records": 1,
            "known_cost_usd": 12.5,
            "activity_sessions": 42,
            "n8n_workflows": 4,
            "n8n_active_workflows": 2,
            "n8n_executions": 99,
            "n8n_non_success": 1,
            "node_issue_count": 0,
        },
        "node_health": {"status": "complete"},
        "agent_token_rank": [{"agent": "Codex", "total_tokens": 1_000_000, "sessions": 2}],
        "project_token_rank": [{"project": "Gateway", "total_tokens": 1_500_000, "sessions": 3}],
        "node_token_rank": [{"node": "main collector", "total_tokens": 1_500_000, "sessions": 3}],
        "access_issues": [],
    }


def test_build_monthly_usage_report_contains_core_sections():
    from usage_report import build_monthly_usage_report

    body = build_monthly_usage_report(
        _fleet_payload(),
        {"plans": [{"name": "ChatGPT Pro", "status": "ok", "renewal_at": "2026-07-08"}]},
        month="2026-06",
        days=30,
    )

    assert "# AI 用量月报 2026-06" in body
    assert "真实 Token" in body
    assert "估算 Token" in body
    assert "Top Agent" in body
    assert "Gateway" in body
    assert "ChatGPT Pro" in body
    assert "n8n 活动" in body


def test_write_monthly_usage_report_writes_markdown(tmp_path):
    from usage_report import write_monthly_usage_report

    result = write_monthly_usage_report(_fleet_payload(), {}, month="2026-06", days=30, output_dir=tmp_path)

    path = tmp_path / "monthly-usage-2026-06.md"
    assert result["path"] == str(path)
    assert result["total_tokens"] == 1_500_000
    assert path.exists()
    assert path.read_text(encoding="utf-8").startswith("# AI 用量月报 2026-06")


def test_monthly_usage_report_endpoint(monkeypatch):
    import gateway
    from fastapi.testclient import TestClient

    async def fake_fleet_ledger(days, limit):
        assert days == 30
        assert limit == 120
        return _fleet_payload()

    async def fake_subscription_ledger():
        return {"plans": []}

    def fake_write_report(fleet, subscriptions, *, month, days):
        assert fleet["totals"]["total_tokens"] == 1_500_000
        assert subscriptions == {"plans": []}
        assert days == 30
        return {
            "path": "reports/monthly-usage-2026-06.md",
            "month": month or "2026-06",
            "bytes": 123,
            "total_tokens": 1_500_000,
        }

    monkeypatch.setattr(gateway, "fleet_ledger", fake_fleet_ledger)
    monkeypatch.setattr(gateway, "subscription_ledger", fake_subscription_ledger)
    monkeypatch.setattr(gateway, "write_monthly_usage_report", fake_write_report)

    response = TestClient(gateway.app).post("/reports/monthly-usage?days=30&limit=120")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["path"] == "reports/monthly-usage-2026-06.md"
