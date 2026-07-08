"""Monthly usage report generation for Smart Agent Ledger."""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from fleet_ledger import build_fleet_ledger
from subscription_ledger import build_subscription_ledger
from utils import utc_now


PROJECT_ROOT = Path(__file__).resolve().parent
REPORTS_DIR = PROJECT_ROOT / "reports"


def _fmt_int(value: Any) -> str:
    try:
        return f"{int(value or 0):,}"
    except (TypeError, ValueError):
        return "0"


def _fmt_tokens(value: Any) -> str:
    try:
        num = float(value or 0)
    except (TypeError, ValueError):
        return "0"
    abs_num = abs(num)
    if abs_num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.2f}B"
    if abs_num >= 1_000_000:
        return f"{num / 1_000_000:.2f}M"
    if abs_num >= 1_000:
        return f"{num / 1_000:.1f}K"
    return str(int(num))


def _fmt_money(value: Any) -> str:
    try:
        num = float(value or 0)
    except (TypeError, ValueError):
        return "$0.00"
    return f"${num:,.2f}"


def _table(headers: List[str], rows: Iterable[Iterable[Any]]) -> str:
    body = [list(map(lambda value: str(value), row)) for row in rows]
    if not body:
        body = [["-" for _ in headers]]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in body:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def _top_rows(rows: List[Dict[str, Any]], label_field: str, value_field: str = "total_tokens", limit: int = 8) -> List[List[str]]:
    output = []
    for row in rows[:limit]:
        label = row.get(label_field) or row.get("node") or row.get("agent") or row.get("project") or "unknown"
        value = _fmt_tokens(row.get(value_field)) if value_field == "total_tokens" else _fmt_int(row.get(value_field))
        records = _fmt_int(row.get("sessions") or row.get("records") or row.get("known_token_sessions"))
        output.append([label, value, records])
    return output


def _issue_rows(fleet: Dict[str, Any]) -> List[List[str]]:
    issues = []
    for item in fleet.get("access_issues") or []:
        if isinstance(item, dict):
            issues.append([item.get("node") or "unknown", item.get("issue") or "-"])
    if issues:
        return issues
    return [["无", "-"]]


def _subscription_rows(subscriptions: Optional[Dict[str, Any]], limit: int = 6) -> List[List[str]]:
    if not isinstance(subscriptions, dict):
        return [["不可用", "-", "-"]]
    rows = []
    for item in (subscriptions.get("plans") or subscriptions.get("items") or [])[:limit]:
        if not isinstance(item, dict):
            continue
        rows.append([
            item.get("name") or item.get("plan_name") or item.get("id") or "unknown",
            item.get("status") or "-",
            item.get("renewal_at") or item.get("next_renewal_at") or "-",
        ])
    return rows or [["无", "-", "-"]]


def build_monthly_usage_report(
    fleet: Dict[str, Any],
    subscriptions: Optional[Dict[str, Any]] = None,
    *,
    month: Optional[str] = None,
    days: int = 30,
    generated_at: Optional[dt.datetime] = None,
) -> str:
    generated = generated_at or utc_now()
    month_label = month or generated.strftime("%Y-%m")
    totals = fleet.get("totals") if isinstance(fleet.get("totals"), dict) else {}
    health = fleet.get("node_health") if isinstance(fleet.get("node_health"), dict) else {}
    connected = f"{totals.get('connected_nodes', 0)}/{totals.get('configured_nodes', 0)}"
    lines = [
        f"# AI 用量月报 {month_label}",
        "",
        f"- 生成时间：{generated.isoformat()}",
        f"- 统计窗口：近 {days} 天",
        f"- 节点完整度：{connected}",
        f"- 数据状态：{'完整' if totals.get('data_complete') else health.get('status', 'partial')}",
        "",
        "## 总览",
        "",
        _table(
            ["指标", "数值"],
            [
                ["总 Token", _fmt_tokens(totals.get("total_tokens"))],
                ["真实 Token", _fmt_tokens(totals.get("real_total_tokens"))],
                ["估算 Token", _fmt_tokens(totals.get("estimated_total_tokens"))],
                ["Token 记录", _fmt_int(totals.get("known_token_records"))],
                ["不可用 Token 记录", _fmt_int(totals.get("unavailable_token_records"))],
                ["估算成本", _fmt_money(totals.get("known_cost_usd"))],
                ["活动次数", _fmt_int(totals.get("activity_sessions"))],
            ],
        ),
        "",
        "## Top Agent",
        "",
        _table(["Agent", "Token", "记录"], _top_rows(fleet.get("agent_token_rank") or [], "agent")),
        "",
        "## Top 项目",
        "",
        _table(["项目", "Token", "记录"], _top_rows(fleet.get("project_token_rank") or [], "project")),
        "",
        "## Top 设备",
        "",
        _table(["设备", "Token", "记录"], _top_rows(fleet.get("node_token_rank") or [], "node")),
        "",
        "## n8n 活动",
        "",
        _table(
            ["指标", "数值"],
            [
                ["工作流", _fmt_int(totals.get("n8n_workflows"))],
                ["活跃工作流", _fmt_int(totals.get("n8n_active_workflows"))],
                ["执行次数", _fmt_int(totals.get("n8n_executions"))],
                ["非成功", _fmt_int(totals.get("n8n_non_success"))],
            ],
        ),
        "",
        "## 异常节点",
        "",
        _table(["节点", "问题"], _issue_rows(fleet)),
        "",
        "## 订阅提醒",
        "",
        _table(["计划", "状态", "续费/到期"], _subscription_rows(subscriptions)),
        "",
        "## 下月建议",
        "",
    ]
    if totals.get("node_issue_count"):
        lines.append("- 优先处理异常节点，避免月报口径缺数据。")
    if totals.get("estimated_total_tokens"):
        lines.append("- 保持真实 token 和估算 token 拆分展示，不把估算混成账单口径。")
    if totals.get("n8n_executions") and not totals.get("n8n_non_success"):
        lines.append("- n8n 当前可继续按 activity-only 观察；只有接入真实 usage 后再进入成本统计。")
    if not any(line.startswith("- ") for line in lines[-3:]):
        lines.append("- 当前数据状态稳定，下一步可按项目归因继续优化月度管理口径。")
    lines.append("")
    return "\n".join(lines)


def monthly_report_path(month: Optional[str] = None, output_dir: Path | str = REPORTS_DIR) -> Path:
    label = month or utc_now().strftime("%Y-%m")
    safe_label = "".join(ch for ch in label if ch.isdigit() or ch == "-")[:7] or utc_now().strftime("%Y-%m")
    return Path(output_dir).expanduser() / f"monthly-usage-{safe_label}.md"


def write_monthly_usage_report(
    fleet: Dict[str, Any],
    subscriptions: Optional[Dict[str, Any]] = None,
    *,
    month: Optional[str] = None,
    days: int = 30,
    output_dir: Path | str = REPORTS_DIR,
) -> Dict[str, Any]:
    path = monthly_report_path(month=month, output_dir=output_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    body = build_monthly_usage_report(fleet, subscriptions, month=month, days=days)
    path.write_text(body, encoding="utf-8")
    totals = fleet.get("totals") if isinstance(fleet.get("totals"), dict) else {}
    return {
        "path": str(path),
        "month": month or utc_now().strftime("%Y-%m"),
        "bytes": path.stat().st_size,
        "total_tokens": totals.get("total_tokens"),
        "real_total_tokens": totals.get("real_total_tokens"),
        "estimated_total_tokens": totals.get("estimated_total_tokens"),
        "connected_nodes": totals.get("connected_nodes"),
        "configured_nodes": totals.get("configured_nodes"),
    }


async def generate_monthly_usage_report(days: int = 30, limit: int = 120, month: Optional[str] = None) -> Dict[str, Any]:
    fleet = await build_fleet_ledger(days=days, limit=limit)
    subscriptions = await asyncio.to_thread(build_subscription_ledger)
    return await asyncio.to_thread(
        write_monthly_usage_report,
        fleet,
        subscriptions,
        month=month,
        days=days,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a Markdown monthly usage report.")
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--limit", type=int, default=120)
    parser.add_argument("--month", default=None)
    args = parser.parse_args()
    result = asyncio.run(generate_monthly_usage_report(days=args.days, limit=args.limit, month=args.month))
    print(result["path"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
