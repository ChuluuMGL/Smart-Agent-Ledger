#!/usr/bin/env python3
"""Smart Agent Ledger Agent Ledger — 聚合/库存/编排 (采集器已拆分至 agent_collectors.py)。"""
from agent_collectors import *  # noqa: F401,F403  — collectors + utils
from utils import dedupe_session_rows

TOKEN_ESTIMATED_STATUSES = {
    "estimated_from_heartbeat",
    "estimated_from_turn_count",
    "local_token_estimate_only",
}


def _token_quality(row: Dict[str, Any]) -> str:
    if not _tokens_are_known(row):
        return "unavailable"
    status = str(row.get("token_status") or "").lower()
    confidence = str(row.get("confidence") or "").lower()
    if (
        status in TOKEN_ESTIMATED_STATUSES
        or status.startswith("estimated_")
        or "estimate" in status
        or "estimation" in confidence
    ):
        return "estimated"
    return "real"


def _token_breakdown_from_records(rows: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    breakdown = {
        "real_token_records": 0,
        "real_total_tokens": 0,
        "estimated_token_records": 0,
        "estimated_total_tokens": 0,
        "unavailable_token_records": 0,
        "included_token_records": 0,
        "included_total_tokens": 0,
    }
    for row in rows:
        quality = _token_quality(row)
        tokens = _safe_int(row.get("total_tokens"))
        if quality == "real":
            breakdown["real_token_records"] += 1
            breakdown["real_total_tokens"] += tokens
        elif quality == "estimated":
            breakdown["estimated_token_records"] += 1
            breakdown["estimated_total_tokens"] += tokens
        else:
            breakdown["unavailable_token_records"] += 1
    breakdown["included_token_records"] = breakdown["real_token_records"] + breakdown["estimated_token_records"]
    breakdown["included_total_tokens"] = breakdown["real_total_tokens"] + breakdown["estimated_total_tokens"]
    return breakdown


def _session_sort_key(row: Dict[str, Any]) -> float:
    return _epoch_from_iso(row.get("ended_at") or row.get("started_at")) or 0


def _aggregate_by(rows: Iterable[Dict[str, Any]], field: str) -> List[Dict[str, Any]]:
    groups: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        key = row.get(field) or "unknown"
        group = groups.setdefault(
            key,
            {
                field: key,
                "sessions": 0,
                "agents": set(),
                "projects": set(),
                "tasks": 0,
                "messages": 0,
                "tool_calls": 0,
                "total_tokens": 0,
                "known_token_sessions": 0,
                "known_cost_usd": 0.0,
                "known_cost_sessions": 0,
                "unknown_cost_sessions": 0,
                "lines_added": 0,
                "lines_removed": 0,
                "files_changed": 0,
                "active_sessions": 0,
                "latest_at": None,
                "latest_task": None,
            },
        )
        group["sessions"] += _safe_int(row.get("session_count") or 1)
        group["agents"].add(row.get("agent") or "unknown")
        group["projects"].add(row.get("project") or "unknown")
        group["tasks"] += 1
        group["messages"] += _safe_int(row.get("message_count"))
        group["tool_calls"] += _safe_int(row.get("tool_call_count"))
        group["total_tokens"] += _safe_int(row.get("total_tokens"))
        if _tokens_are_known(row):
            group["known_token_sessions"] += 1
        group["lines_added"] += _safe_int(row.get("lines_added"))
        group["lines_removed"] += _safe_int(row.get("lines_removed"))
        group["files_changed"] += _safe_int(row.get("files_changed"))
        cost = _row_cost(row)
        if cost is None:
            group["unknown_cost_sessions"] += 1
        else:
            group["known_cost_sessions"] += 1
            group["known_cost_usd"] += cost
        if row.get("status") in {"active", "recent"}:
            group["active_sessions"] += 1
        current_ts = _session_sort_key(row)
        previous_ts = _epoch_from_iso(group["latest_at"])
        if not previous_ts or current_ts >= previous_ts:
            group["latest_at"] = row.get("ended_at") or row.get("started_at")
            group["latest_task"] = row.get("task")
    output = []
    for group in groups.values():
        group["agents"] = sorted(group["agents"])
        group["projects"] = sorted(group["projects"])
        group["known_cost_usd"] = round(group["known_cost_usd"], 6)
        output.append(group)
    return sorted(output, key=lambda x: (x.get("active_sessions", 0), x.get("latest_at") or ""), reverse=True)


def _claude_inventory_extra() -> Dict[str, Any]:
    path = HOME / ".claude/stats-cache.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(errors="ignore"))
    except (json.JSONDecodeError, OSError):
        return {}
    token_total = 0
    for model_stats in (data.get("modelUsage") or {}).values():
        if isinstance(model_stats, dict):
            for key, value in model_stats.items():
                if "token" in key.lower():
                    token_total += _safe_int(value)
    last_date = data.get("lastComputedDate")
    last_seen = None
    if last_date:
        try:
            last_seen = dt.datetime.strptime(last_date, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).isoformat()
        except (json.JSONDecodeError, OSError):
            last_seen = None
    return {
        "all_time_sessions": _safe_int(data.get("totalSessions")),
        "all_time_messages": _safe_int(data.get("totalMessages")),
        "all_time_tokens": token_total,
        "cache_last_computed": last_date,
        "last_seen": last_seen,
    }


def _inventory_status(installed: bool, record_count: int, collector_status: str) -> str:
    if record_count > 0:
        return "connected"
    if not installed:
        return "not_found"
    if collector_status == "pending_schema_mapping":
        return "installed_not_connected"
    return "installed_no_recent_records"


def build_agent_inventory(rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    row_list = list(rows)
    grouped: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {
            "record_count": 0,
            "active_sessions": 0,
            "projects": set(),
            "total_tokens": 0,
            "known_token_sessions": 0,
            "known_cost_usd": 0.0,
            "known_cost_sessions": 0,
            "lines_added": 0,
            "lines_removed": 0,
            "files_changed": 0,
            "last_seen": None,
        }
    )
    for row in row_list:
        agent = row.get("agent") or "unknown"
        group = grouped[agent]
        group["record_count"] += _safe_int(row.get("session_count") or 1)
        group["active_sessions"] += 1 if row.get("status") in {"active", "recent", "running", "in_progress"} else 0
        group["projects"].add(row.get("project") or "unknown")
        group["total_tokens"] += _safe_int(row.get("total_tokens"))
        if _tokens_are_known(row):
            group["known_token_sessions"] += 1
        group["lines_added"] += _safe_int(row.get("lines_added"))
        group["lines_removed"] += _safe_int(row.get("lines_removed"))
        group["files_changed"] += _safe_int(row.get("files_changed"))
        cost = _row_cost(row)
        if cost is not None:
            group["known_cost_sessions"] += 1
            group["known_cost_usd"] += cost
        current_ts = row.get("ended_at") or row.get("started_at")
        previous_ts = _epoch_from_iso(group["last_seen"])
        if current_ts and (not previous_ts or (_epoch_from_iso(current_ts) or 0) >= previous_ts):
            group["last_seen"] = current_ts

    claude_extra = _claude_inventory_extra()
    known_agents = [
        {
            "agent": "Codex",
            "component_type": "agent",
            "paths": [HOME / ".codex", HOME / ".codex/sessions"],
            "raw_path": str(HOME / ".codex/sessions"),
            "collector_status": "parsed",
            "note": "读取 ~/.codex/sessions 的本机会话 JSONL；金额只做本地 token 估算。",
        },
        {
            "agent": "Hermes",
            "component_type": "agent",
            "paths": [HOME / ".hermes", HOME / ".hermes/state.db"],
            "raw_path": str(HOME / ".hermes/state.db"),
            "collector_status": "parsed",
            "note": "读取 Hermes state.db，含会话和 token；当前成本字段没有可靠金额来源时显示不可用。",
        },
        {
            "agent": "OpenClaw",
            "component_type": "agent",
            "paths": [HOME / ".openclaw", HOME / ".openclaw/agents/main/sessions/sessions.json", HOME / ".openclaw/tasks/runs.sqlite"],
            "raw_path": str(HOME / ".openclaw"),
            "collector_status": "parsed",
            "note": "读取 OpenClaw session 索引和任务运行库；任务库不一定包含 token。",
        },
        {
            "agent": "Claude Code",
            "component_type": "agent",
            "paths": [HOME / ".claude", HOME / ".claude/stats-cache.json"],
            "raw_path": str(HOME / ".claude/stats-cache.json"),
            "collector_status": "parsed_cache",
            "note": "本地缓存只给聚合统计；近期窗口内没有活动时不会进入任务账本。",
            **claude_extra,
        },
        {
            "agent": "Antigravity",
            "component_type": "agent",
            "paths": [
                HOME / ".antigravity",
                HOME / "Library/Application Support/Antigravity",
                HOME / "Library/Application Support/Antigravity IDE",
            ],
            "raw_path": str(HOME / "Library/Application Support/Antigravity IDE"),
            "collector_status": "pending_schema_mapping",
            "note": "已发现 IDE 数据和日志，但还没接入可靠的任务/token 表结构。",
        },
        {
            "agent": "Cursor",
            "component_type": "agent",
            "paths": [
                HOME / ".cursor",
                HOME / "Library/Application Support/Cursor",
                HOME / ".local/bin/cursor-agent",
                HOME / ".local/share/cursor-agent",
            ],
            "raw_path": str(HOME / "Library/Application Support/Cursor"),
            "collector_status": "parsed_metadata",
            "note": "读取 Cursor workspaceStorage 的 composer 元数据；只采标题、时间、项目和代码改动量，不采 prompt 正文。",
        },
        {
            "agent": "Trae",
            "component_type": "agent",
            "paths": [
                HOME / ".trae",
                HOME / ".trae-aicc",
                HOME / "Library/Application Support/Trae",
                HOME / "Library/Application Support/TRAE SOLO",
            ],
            "raw_path": str(HOME / "Library/Application Support/Trae"),
            "collector_status": "turn_count_estimation",
            "note": "Trae workspaceStorage (session/model discovery) + git snapshot tags (turn counting)。Tokens 从 turn 计数估算；费用从 pricing table 计算。",
        },
        {
            "agent": "LiteLLM",
            "component_type": "infrastructure",
            "paths": [PRIVATE_LITELLM_ENV],
            "raw_path": str(PRIVATE_LITELLM_ENV),
            "collector_status": "metering_optional",
            "note": "LiteLLM 是计量/路由组件，不是执行任务的 Agent；需要 litellm.env 里的 DATABASE_URL 才能读取 SpendLogs。",
        },
    ]
    inventory = []
    for item in known_agents:
        agent = item["agent"]
        group = grouped.get(agent, {})
        installed = _path_exists_any(item["paths"])
        record_count = _safe_int(group.get("record_count"))
        status = _inventory_status(installed, record_count, item["collector_status"])
        last_seen = group.get("last_seen") or item.get("last_seen") or _latest_mtime_iso(item["paths"])
        projects = sorted(group.get("projects") or [])
        inventory.append(
            {
                "agent": agent,
                "component_type": item.get("component_type", "agent"),
                "installed": installed,
                "status": status,
                "collector_status": item["collector_status"],
                "record_count": record_count,
                "active_sessions": _safe_int(group.get("active_sessions")),
                "projects": projects,
                "total_tokens": _safe_int(group.get("total_tokens") or item.get("all_time_tokens")),
                "known_token_sessions": _safe_int(group.get("known_token_sessions")),
                "known_cost_usd": round(float(group.get("known_cost_usd") or 0), 6),
                "known_cost_sessions": _safe_int(group.get("known_cost_sessions")),
                "lines_added": _safe_int(group.get("lines_added")),
                "lines_removed": _safe_int(group.get("lines_removed")),
                "files_changed": _safe_int(group.get("files_changed")),
                "last_seen": last_seen,
                "raw_path": item["raw_path"],
                "note": item["note"],
                "all_time_sessions": item.get("all_time_sessions"),
                "all_time_messages": item.get("all_time_messages"),
                "cache_last_computed": item.get("cache_last_computed"),
            }
        )
    seen = {item["agent"] for item in inventory}
    for agent, group in grouped.items():
        if agent in seen:
            continue
        inventory.append(
            {
                "agent": agent,
                "component_type": "agent",
                "installed": True,
                "status": "connected",
                "collector_status": "runtime",
                "record_count": _safe_int(group.get("record_count")),
                "active_sessions": _safe_int(group.get("active_sessions")),
                "projects": sorted(group.get("projects") or []),
                "total_tokens": _safe_int(group.get("total_tokens")),
                "known_token_sessions": _safe_int(group.get("known_token_sessions")),
                "known_cost_usd": round(float(group.get("known_cost_usd") or 0), 6),
                "known_cost_sessions": _safe_int(group.get("known_cost_sessions")),
                "lines_added": _safe_int(group.get("lines_added")),
                "lines_removed": _safe_int(group.get("lines_removed")),
                "files_changed": _safe_int(group.get("files_changed")),
                "last_seen": group.get("last_seen"),
                "raw_path": None,
                "note": "来自运行期账本记录。",
            }
        )
    status_rank = {"connected": 0, "installed_no_recent_records": 1, "installed_not_connected": 2, "not_found": 3}
    return sorted(inventory, key=lambda item: (status_rank.get(item["status"], 9), item["agent"]))


def collect_sessions(days: int = 30) -> tuple:
    """采集所有 agent 的会话, 返回 (rows, access_issues)。

    rows 已按时间倒序排序, 并已根据单价表填充 estimated_cost_usd。
    供 build_agent_ledger (聚合) 和 query_sessions (明细筛选/分页) 复用。
    """
    rows: List[Dict[str, Any]] = []
    access_issues: List[Dict[str, Any]] = []
    collectors = [
        ("gateway", collect_gateway_events),
        ("hermes", collect_hermes_sessions),
        ("codex", collect_codex_sessions),
        ("claude_code", collect_claude_cache),
        ("claude_history", collect_claude_history),
        ("openclaw", collect_openclaw_sessions),
        ("cursor", collect_cursor_sessions),
        ("trae", collect_trae_sessions),           # P3.4
        ("antigravity", collect_antigravity_sessions),  # P3.4
        ("litellm", collect_litellm_usage),
    ]
    # P1.1: 并行采集，总耗时 = max(单个 collector)，而非 sum(所有)
    with ThreadPoolExecutor(max_workers=len(collectors)) as pool:
        futures = {pool.submit(collector, days): name for name, collector in collectors}
        for future in as_completed(futures):
            name = futures[future]
            try:
                rows.extend(future.result())
            except Exception as exc:
                access_issues.append({"source": name, "issue": str(exc)})
    rows = sorted(dedupe_session_rows(rows), key=_session_sort_key, reverse=True)
    pricing = _load_model_pricing(DATA_DIR)
    _estimate_missing_costs(rows, pricing)
    return rows, access_issues


def query_sessions(
    days: int = 30,
    agent: Optional[str] = None,
    project: Optional[str] = None,
    min_tokens: int = 0,
    sort: str = "time",
    page: int = 1,
    page_size: int = 50,
    rows: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """会话明细查询 — 支持筛选 + 排序 + 分页 (供管理员后台 /admin/sessions)。

    参数:
        rows: 预采集的 rows (复用缓存); 为 None 时内部调用 collect_sessions
    返回: {sessions, total, page, page_size, has_more}
    """
    if rows is None:
        rows, _ = collect_sessions(days)
    # 筛选
    if agent:
        rows = [r for r in rows if (r.get("agent") or "") == agent]
    if project:
        rows = [r for r in rows if (r.get("project") or "") == project]
    if min_tokens > 0:
        rows = [r for r in rows if _safe_int(r.get("total_tokens")) >= min_tokens]
    # 排序 (默认 time, 按时间倒序)
    if sort == "token":
        rows = sorted(rows, key=lambda r: _safe_int(r.get("total_tokens")), reverse=True)
    elif sort == "cost":
        rows = sorted(rows, key=lambda r: (_row_cost(r) or 0), reverse=True)
    else:  # time (默认): 按 _session_sort_key 倒序, 不依赖输入顺序
        rows = sorted(rows, key=_session_sort_key, reverse=True)
    total = len(rows)
    page = max(1, page)
    page_size = max(1, min(page_size, 500))
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "sessions": rows[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_more": end < total,
    }


def build_agent_ledger(days: int = 30, limit: int = 100) -> Dict[str, Any]:
    rows, access_issues = collect_sessions(days)
    rows = dedupe_session_rows(rows)
    limited = rows[:limit]
    known_cost = 0.0
    known_cost_sessions = 0
    unknown_cost = 0
    raw_total_tokens = 0
    known_token_sessions = 0
    lines_added = 0
    lines_removed = 0
    files_changed = 0
    for row in rows:
        raw_total_tokens += _safe_int(row.get("total_tokens"))
        if _tokens_are_known(row):
            known_token_sessions += 1
        lines_added += _safe_int(row.get("lines_added"))
        lines_removed += _safe_int(row.get("lines_removed"))
        files_changed += _safe_int(row.get("files_changed"))
        cost = _row_cost(row)
        if cost is None:
            unknown_cost += 1
        else:
            known_cost_sessions += 1
            known_cost += cost
    token_breakdown = _token_breakdown_from_records(rows)
    total_tokens = token_breakdown["included_total_tokens"]
    known_token_sessions = token_breakdown["included_token_records"]
    agent_rows = [row for row in rows if _is_agent_row(row)]
    infrastructure_rows = [row for row in rows if not _is_agent_row(row)]
    return {
        "generated_at": _now().isoformat(),
        "window_days": days,
        "totals": {
            "sessions": len(rows),
            "agents": len({r.get("agent") for r in agent_rows if r.get("agent")}),
            "projects": len({r.get("project") for r in agent_rows if r.get("project")}),
            "total_tokens": total_tokens,
            "raw_total_tokens": raw_total_tokens,
            "known_token_sessions": known_token_sessions,
            "real_total_tokens": token_breakdown["real_total_tokens"],
            "real_token_sessions": token_breakdown["real_token_records"],
            "estimated_total_tokens": token_breakdown["estimated_total_tokens"],
            "estimated_token_sessions": token_breakdown["estimated_token_records"],
            "unavailable_token_sessions": token_breakdown["unavailable_token_records"],
            "token_breakdown": token_breakdown,
            "known_cost_usd": round(known_cost, 6),
            "known_cost_sessions": known_cost_sessions,
            "unknown_cost_sessions": unknown_cost,
            "lines_added": lines_added,
            "lines_removed": lines_removed,
            "files_changed": files_changed,
            "active_sessions": sum(1 for r in agent_rows if r.get("status") in {"active", "recent"}),
            "infrastructure_components": len(INFRASTRUCTURE_COMPONENTS),
            "infrastructure_records": len(infrastructure_rows),
        },
        "by_agent": _aggregate_by(agent_rows, "agent"),
        "by_project": _aggregate_by(agent_rows, "project"),
        "by_task": _aggregate_by(agent_rows, "task"),
        "by_model": _aggregate_by(agent_rows, "model"),
        "agent_inventory": build_agent_inventory(rows),
        "recent_sessions": limited,
        "access_issues": access_issues,
        "notes": [
            "Codex token totals include input, cached input, output, and reasoning output from local token_count events.",
            "Codex cost is a local token estimate, not a billing number.",
            "Codex local JSONL may not cover cloud-side or other-device usage shown in official usage dashboards.",
            "Project/task are exact only when the agent sends metadata; otherwise they are inferred from cwd or local logs.",
            "Antigravity is shown as installed until a reliable local task/token schema is mapped.",
            "Trae tokens estimated from git snapshot turn count (~2000 input + 1000 output tokens per turn); costs from pricing table.",
            "Cursor metadata is sourced from workspaceStorage composer data; token and cost are intentionally shown as unavailable.",
            "LiteLLM is treated as metering/routing infrastructure, not as an executing Agent.",
            "LiteLLM spend requires DATABASE_URL in ~/.config/smart-agent-ledger/litellm.env.",
        ],
    }
