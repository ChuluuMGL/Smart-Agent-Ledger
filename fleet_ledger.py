#!/usr/bin/env python3
import asyncio
import csv
from contextlib import suppress
import hashlib
import io
import json
import os
import pathlib
import subprocess
from typing import Any, Dict, Iterable, List, Optional, Tuple

import httpx

from project_attribution import normalize_project_name
from utils import dedupe_session_rows, epoch_from_iso, parse_iso, safe_int as _safe_int, safe_read_json, utc_now as _now


PROJECT_ROOT = pathlib.Path(__file__).resolve().parent
CONFIG_PATH = PROJECT_ROOT / "data" / "company-agent-nodes.json"
LOCAL_AGENT_NODE_TYPES = {"local_agent_ledger", "self_agent_ledger"}
AGENT_LEDGER_FILE_NODE_TYPES = {"agent_ledger_file", "icloud_agent_ledger_file"}
REAL_TOKEN_SOURCE_TYPES = {"local_agent_ledger", "agent_ledger_file", "smart_gateway"}
ACTIVITY_ONLY_SOURCE_TYPES = {"n8n_ssh"}
TOKEN_UNAVAILABLE_STATUSES = {
    "not_available",
    "unknown",
    "status_only",
    "pending_schema_mapping",
    "server_side_only",
}
TOKEN_ESTIMATED_STATUSES = {
    "estimated_from_heartbeat",
    "estimated_from_turn_count",
    "local_token_estimate_only",
}
AGENT_LEDGER_FILE_CACHE_DIR = pathlib.Path(
    os.getenv("SMART_GATEWAY_AGENT_LEDGER_FILE_CACHE_DIR")
    or pathlib.Path.home() / "Library/Caches/Smart Agent Ledger/agent-ledger-files"
)
AGENT_LEDGER_FILE_CACHE_MAX_AGE_SECONDS = max(
    60,
    _safe_int(os.getenv("SMART_GATEWAY_AGENT_LEDGER_FILE_CACHE_MAX_AGE_SECONDS"), 24 * 60 * 60),
)
AGENT_LEDGER_FILE_EXPORT_MAX_AGE_SECONDS = max(
    60,
    _safe_int(os.getenv("SMART_GATEWAY_AGENT_LEDGER_FILE_EXPORT_MAX_AGE_SECONDS"), 36 * 60 * 60),
)
AGENT_LEDGER_HTTP_CACHE_FRESH_SECONDS = max(
    0,
    _safe_int(os.getenv("SMART_GATEWAY_AGENT_LEDGER_HTTP_CACHE_FRESH_SECONDS"), 5 * 60),
)
AGENT_LEDGER_HTTP_TIMEOUT_MAX_SECONDS = max(
    1,
    _safe_int(os.getenv("SMART_GATEWAY_AGENT_LEDGER_HTTP_TIMEOUT_MAX_SECONDS"), 8),
)
AGENT_LEDGER_HTTP_STALE_REFRESH_TIMEOUT_SECONDS = max(
    1,
    _safe_int(os.getenv("SMART_GATEWAY_AGENT_LEDGER_HTTP_STALE_REFRESH_TIMEOUT_SECONDS"), 2),
)

N8N_SQLITE_REMOTE_SCRIPT = r"""set -eu
DB="$1"
DAYS="$2"
LIMIT="$3"
TAB="$(printf '\t')"

if ! command -v sqlite3 >/dev/null 2>&1; then
  echo "sqlite3 is not installed" >&2
  exit 127
fi
if [ ! -r "$DB" ]; then
  echo "n8n database is not readable: $DB" >&2
  exit 2
fi

run_sql() {
  sqlite3 -readonly -header -separator "$TAB" "$DB" "$1"
}

echo "__SUMMARY__"
run_sql "
SELECT
  (SELECT COUNT(*) FROM workflow_entity WHERE COALESCE(isArchived, 0) = 0) AS workflows,
  (SELECT COUNT(*) FROM workflow_entity WHERE active = 1 AND COALESCE(isArchived, 0) = 0) AS active_workflows,
  (SELECT COUNT(*) FROM execution_entity e WHERE e.deletedAt IS NULL AND datetime(e.startedAt) >= datetime('now', '-' || $DAYS || ' days')) AS executions,
  (SELECT COALESCE(SUM(CASE WHEN e.status = 'success' THEN 1 ELSE 0 END), 0) FROM execution_entity e WHERE e.deletedAt IS NULL AND datetime(e.startedAt) >= datetime('now', '-' || $DAYS || ' days')) AS success,
  (SELECT COALESCE(SUM(CASE WHEN COALESCE(e.status, '') != 'success' THEN 1 ELSE 0 END), 0) FROM execution_entity e WHERE e.deletedAt IS NULL AND datetime(e.startedAt) >= datetime('now', '-' || $DAYS || ' days')) AS non_success,
  (SELECT MAX(e.startedAt) FROM execution_entity e WHERE e.deletedAt IS NULL AND datetime(e.startedAt) >= datetime('now', '-' || $DAYS || ' days')) AS latest_at
"

echo "__WORKFLOWS__"
run_sql "
SELECT
  e.workflowId AS workflow_id,
  COALESCE(w.name, e.workflowId, 'unknown') AS workflow,
  COUNT(*) AS executions,
  SUM(CASE WHEN e.status = 'success' THEN 1 ELSE 0 END) AS success,
  SUM(CASE WHEN COALESCE(e.status, '') != 'success' THEN 1 ELSE 0 END) AS non_success,
  ROUND(AVG(CASE WHEN e.stoppedAt IS NOT NULL THEN (julianday(e.stoppedAt) - julianday(e.startedAt)) * 86400 ELSE NULL END), 3) AS avg_duration_seconds,
  MIN(e.startedAt) AS first_at,
  MAX(e.startedAt) AS latest_at
FROM execution_entity e
LEFT JOIN workflow_entity w ON w.id = e.workflowId
WHERE e.deletedAt IS NULL
  AND datetime(e.startedAt) >= datetime('now', '-' || $DAYS || ' days')
GROUP BY e.workflowId, w.name
ORDER BY executions DESC, latest_at DESC
LIMIT $LIMIT
"

echo "__RECENT__"
run_sql "
SELECT
  e.id AS execution_id,
  e.workflowId AS workflow_id,
  COALESCE(w.name, e.workflowId, 'unknown') AS workflow,
  e.status AS status,
  e.mode AS mode,
  e.startedAt AS started_at,
  e.stoppedAt AS stopped_at,
  ROUND(CASE WHEN e.stoppedAt IS NOT NULL THEN (julianday(e.stoppedAt) - julianday(e.startedAt)) * 86400 ELSE NULL END, 3) AS duration_seconds
FROM execution_entity e
LEFT JOIN workflow_entity w ON w.id = e.workflowId
WHERE e.deletedAt IS NULL
  AND datetime(e.startedAt) >= datetime('now', '-' || $DAYS || ' days')
ORDER BY e.startedAt DESC
LIMIT $LIMIT
"

echo "__DAILY__"
run_sql "
SELECT
  date(e.startedAt) AS date,
  e.workflowId AS workflow_id,
  COALESCE(w.name, e.workflowId, 'unknown') AS workflow,
  COUNT(*) AS executions,
  SUM(CASE WHEN e.status = 'success' THEN 1 ELSE 0 END) AS success,
  SUM(CASE WHEN COALESCE(e.status, '') != 'success' THEN 1 ELSE 0 END) AS non_success,
  MAX(e.startedAt) AS latest_at
FROM execution_entity e
LEFT JOIN workflow_entity w ON w.id = e.workflowId
WHERE e.deletedAt IS NULL
  AND datetime(e.startedAt) >= datetime('now', '-' || $DAYS || ' days')
GROUP BY date(e.startedAt), e.workflowId, w.name
ORDER BY date DESC, executions DESC
LIMIT $LIMIT
"
"""


def _load_config() -> Dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {"schema_version": 1, "nodes": [], "authorized_networks": []}
    data = safe_read_json(CONFIG_PATH, default=None)
    if data is None:
        return {"schema_version": 1, "nodes": [], "authorized_networks": [], "load_error": "read failed"}
    if not isinstance(data, dict):
        return {"schema_version": 1, "nodes": [], "authorized_networks": [], "load_error": "config root must be an object"}
    data.setdefault("nodes", [])
    data.setdefault("authorized_networks", [])
    return data


def _save_config(config: Dict[str, Any]) -> None:
    """Atomically write the team-node config file."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = CONFIG_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(CONFIG_PATH)


REGISTER_NODE_EXTRA_FIELDS = {
    "type",
    "host",
    "role",
    "base_url_candidates",
    "base_urls",
    "fallback_base_urls",
    "ledger_url_candidates",
    "fallback_ledger_urls",
    "timeout_seconds",
}


def register_node(
    name: str,
    base_url: str,
    enabled: bool = True,
    ledger_url: Optional[str] = None,
    **extra: Any,
) -> Dict[str, Any]:
    """Register or update a Fleet team node.

    - name 已存在则更新, 不存在则追加
    - 写入后配合 #9 mtime 热重载, fleet_ledger 下次拉取自动包含新节点
    返回: {"name": ..., "action": "added"|"updated", "node": {...}}
    """
    config = _load_config()
    nodes = config.setdefault("nodes", [])
    node = {
        "name": name,
        "base_url": base_url,
        "enabled": enabled,
    }
    if ledger_url:
        node["ledger_url"] = ledger_url
    for key in REGISTER_NODE_EXTRA_FIELDS:
        value = extra.get(key)
        if value is not None and value != "":
            node[key] = value
    # 查找是否已存在同名节点
    action = "added"
    for i, existing in enumerate(nodes):
        if isinstance(existing, dict) and (existing.get("name") == name or existing.get("base_url") == base_url):
            node = {**existing, **node}  # 合并, 保留额外字段
            nodes[i] = node
            action = "updated"
            break
    else:
        nodes.append(node)
    _save_config(config)
    return {"name": name, "action": action, "node": node}


def remove_node(name: str) -> Dict[str, Any]:
    """按 name 移除一个 Fleet 节点。"""
    config = _load_config()
    nodes = config.get("nodes") or []
    before = len(nodes)
    config["nodes"] = [n for n in nodes if not (isinstance(n, dict) and n.get("name") == name)]
    removed = before - len(config["nodes"])
    if removed > 0:
        _save_config(config)
    return {"name": name, "removed": removed}


def _node_url(node: Dict[str, Any], days: int, limit: int) -> Optional[str]:
    urls = _node_url_candidates(node, days, limit)
    return urls[0] if urls else None


def _dedupe_strings(values: Iterable[Any]) -> List[str]:
    seen: set[str] = set()
    output: List[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        output.append(text)
    return output


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _agent_ledger_url_from_base(base_url: str, days: int, limit: int) -> str:
    return str(base_url).rstrip("/") + f"/agent-ledger?days={days}&limit={limit}"


def _node_url_candidates(node: Dict[str, Any], days: int, limit: int) -> List[str]:
    node_type = str(node.get("type") or "").lower()
    if node_type == "n8n_ssh" or node_type in LOCAL_AGENT_NODE_TYPES or node_type in AGENT_LEDGER_FILE_NODE_TYPES:
        return []
    ledger_urls = _dedupe_strings(
        [node.get("ledger_url")]
        + _as_list(node.get("ledger_url_candidates"))
        + _as_list(node.get("fallback_ledger_urls"))
    )
    if ledger_urls:
        return ledger_urls
    base_urls = _dedupe_strings(
        [node.get("base_url")]
        + _as_list(node.get("base_urls"))
        + _as_list(node.get("base_url_candidates"))
        + _as_list(node.get("fallback_base_urls"))
    )
    return [_agent_ledger_url_from_base(base_url, days, limit) for base_url in base_urls]


def _node_operator_label(node: Dict[str, Any], name: Any) -> str:
    text = " ".join(
        str(value or "")
        for value in (name, node.get("name"), node.get("host"), node.get("base_url"))
    ).lower()
    if "demo-laptop" in text or "mac air" in text:
        return "collector laptop"
    if "demo-main" in text or "main collector" in text:
        return "main collector"
    return "该节点"


def _remote_node_issue(node: Dict[str, Any], name: Any, attempted_urls: List[str], errors: List[str]) -> str:
    label = _node_operator_label(node, name)
    last_error = errors[-1] if errors else "unknown error"
    url_text = "、".join(attempted_urls) if attempted_urls else "未生成可用地址"
    return (
        f"{label} 不可达：已尝试 {url_text}。"
        "请确认两台机器在同一 Wi-Fi、只读账本服务 8002 正在运行，"
        "或更新 data/company-agent-nodes.json 的 base_url/base_url_candidates。"
        f"最后错误：{last_error}"
    )


def _tokens_are_known(row: Dict[str, Any]) -> bool:
    if _safe_int(row.get("known_token_sessions")) > 0:
        return True
    if str(row.get("token_status") or "") in TOKEN_UNAVAILABLE_STATUSES:
        return False
    return _safe_int(row.get("total_tokens")) > 0


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


def _empty_token_breakdown() -> Dict[str, int]:
    return {
        "real_token_records": 0,
        "real_total_tokens": 0,
        "estimated_token_records": 0,
        "estimated_total_tokens": 0,
        "unavailable_token_records": 0,
        "included_token_records": 0,
        "included_total_tokens": 0,
    }


def _token_breakdown_from_records(records: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    breakdown = _empty_token_breakdown()
    for row in records:
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


def _build_fleet_data_trust(
    *,
    nodes_configured: int,
    connected_nodes: int,
    current_data_nodes: int,
    stale_nodes: List[str],
    unavailable_nodes: List[str],
    access_issues: List[Dict[str, Any]],
    token_breakdown: Dict[str, int],
    total_records: int,
    excluded_stale_records: int,
    excluded_stale_total_tokens: int,
) -> Dict[str, Any]:
    included_records = _safe_int(token_breakdown.get("included_token_records"))
    real_records = _safe_int(token_breakdown.get("real_token_records"))
    estimated_records = _safe_int(token_breakdown.get("estimated_token_records"))
    unavailable_records = _safe_int(token_breakdown.get("unavailable_token_records"))
    reasons: List[str] = []

    if nodes_configured <= 0:
        status = "not_configured"
        reasons.append("no_team_nodes_configured")
    elif current_data_nodes <= 0:
        status = "unavailable"
        reasons.append("no_current_team_node_data")
    elif stale_nodes or unavailable_nodes or access_issues:
        status = "partial"
        if stale_nodes:
            reasons.append("has_stale_nodes")
        if unavailable_nodes:
            reasons.append("has_unavailable_nodes")
        if access_issues:
            reasons.append("has_access_issues")
    elif included_records <= 0:
        status = "no_token_data"
        reasons.append("no_reliable_token_records")
    elif estimated_records > 0 or unavailable_records > 0:
        status = "partial"
        if estimated_records > 0:
            reasons.append("includes_estimated_tokens")
        if unavailable_records > 0:
            reasons.append("some_records_without_tokens")
    else:
        status = "complete"

    if nodes_configured <= 0:
        score = 0
    else:
        node_score = (current_data_nodes / max(nodes_configured, 1)) * 45
        token_score = (included_records / max(total_records, included_records, 1)) * 30 if total_records or included_records else 0
        real_score = (real_records / max(included_records, 1)) * 20 if included_records else 0
        freshness_score = 5 if not stale_nodes and not unavailable_nodes else 0
        score = round(node_score + token_score + real_score + freshness_score)
        if access_issues:
            score = max(0, score - min(25, len(access_issues) * 5))
        if status == "no_token_data":
            score = min(score, 35)
        if status == "unavailable":
            score = min(score, 20)

    return {
        "scope": "fleet",
        "status": status,
        "score": max(0, min(100, score)),
        "configured_nodes": nodes_configured,
        "connected_nodes": connected_nodes,
        "current_data_nodes": current_data_nodes,
        "stale_nodes": stale_nodes,
        "unavailable_nodes": unavailable_nodes,
        "access_issue_count": len(access_issues),
        "window_records": total_records,
        "included_token_records": included_records,
        "real_token_records": real_records,
        "estimated_token_records": estimated_records,
        "unavailable_token_records": unavailable_records,
        "excluded_stale_records": excluded_stale_records,
        "excluded_stale_total_tokens": excluded_stale_total_tokens,
        "reasons": reasons,
        "token_breakdown": token_breakdown,
    }


def _normalize_token_breakdown(summary: Dict[str, Any], records: List[Dict[str, Any]]) -> Dict[str, int]:
    raw = summary.get("token_breakdown")
    if isinstance(raw, dict):
        breakdown = _empty_token_breakdown()
        for key in breakdown:
            breakdown[key] = _safe_int(raw.get(key))
        if breakdown["included_token_records"] <= 0:
            breakdown["included_token_records"] = (
                breakdown["real_token_records"] + breakdown["estimated_token_records"]
            )
        if breakdown["included_total_tokens"] <= 0:
            breakdown["included_total_tokens"] = (
                breakdown["real_total_tokens"] + breakdown["estimated_total_tokens"]
            )
        return breakdown

    # Legacy node summaries predate the explicit real/estimated split. Keep
    # their old total compatible, but mark it as real only when no better row
    # sample exists.
    summary_known_records = _safe_int(summary.get("known_token_sessions"))
    summary_total_tokens = _safe_int(summary.get("total_tokens"))
    if summary_known_records > 0 or summary_total_tokens > 0:
        sample_breakdown = _token_breakdown_from_records(records)
        breakdown = _empty_token_breakdown()
        if sample_breakdown["estimated_token_records"] > 0 and sample_breakdown["real_token_records"] <= 0:
            breakdown["estimated_token_records"] = summary_known_records
            breakdown["estimated_total_tokens"] = summary_total_tokens
        else:
            breakdown["real_token_records"] = summary_known_records
            breakdown["real_total_tokens"] = summary_total_tokens
        breakdown["included_token_records"] = summary_known_records
        breakdown["included_total_tokens"] = summary_total_tokens
        return breakdown

    return _token_breakdown_from_records(records)


def _rank(rows: Iterable[Dict[str, Any]], fields: List[str], limit: int = 20) -> List[Dict[str, Any]]:
    groups: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        if not _tokens_are_known(row):
            continue
        key = " | ".join(str(row.get(field) or "unknown") for field in fields)
        group = groups.setdefault(
            key,
            {
                **{field: row.get(field) or "unknown" for field in fields},
                "sessions": 0,
                "total_tokens": 0,
                "known_token_sessions": 0,
                "known_cost_usd": 0.0,
                "known_cost_sessions": 0,
                "nodes": set(),
                "agents": set(),
                "projects": set(),
                "tasks": set(),
            },
        )
        group["sessions"] += _safe_int(row.get("sessions") or row.get("session_count") or 1)
        group["total_tokens"] += _safe_int(row.get("total_tokens"))
        group["known_token_sessions"] += _safe_int(row.get("known_token_sessions") or 1)
        row_quality = _token_quality(row)
        previous_quality = group.get("token_quality")
        if previous_quality and previous_quality != row_quality:
            group["token_quality"] = "mixed"
        else:
            group["token_quality"] = row_quality
        # 聚合费用（每行可能有 estimated_cost_usd 或 known_cost_usd）
        row_cost = float(row.get("known_cost_usd") or row.get("estimated_cost_usd") or 0)
        if row_cost > 0:
            group["known_cost_usd"] += row_cost
            group["known_cost_sessions"] += 1
        group["nodes"].add(row.get("node") or "unknown")
        group["agents"].add(row.get("agent") or "unknown")
        group["projects"].add(row.get("project") or "unknown")
        group["tasks"].add(row.get("task") or "unknown")
    output = []
    for group in groups.values():
        group["nodes"] = sorted(group["nodes"])
        group["agents"] = sorted(group["agents"])
        group["projects"] = sorted(group["projects"])
        group["tasks"] = sorted(group["tasks"])
        group["known_cost_usd"] = round(group["known_cost_usd"], 6)
        output.append(group)
    return sorted(output, key=lambda item: item["total_tokens"], reverse=True)[:limit]


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _bounded_int(value: Any, default: int, minimum: int, maximum: int) -> int:
    parsed = _safe_int(value)
    if parsed <= 0:
        parsed = default
    return max(minimum, min(parsed, maximum))


def _activity_count(row: Dict[str, Any]) -> int:
    return _safe_int(
        row.get("activity_count")
        or row.get("executions")
        or row.get("sessions")
        or row.get("session_count")
        or 1
    )


def _activity_rank(rows: Iterable[Dict[str, Any]], fields: List[str], limit: int = 20) -> List[Dict[str, Any]]:
    groups: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        count = _activity_count(row)
        if count <= 0:
            continue
        key = " | ".join(str(row.get(field) or "unknown") for field in fields)
        group = groups.setdefault(
            key,
            {
                **{field: row.get(field) or "unknown" for field in fields},
                "sessions": 0,
                "records": 0,
                "nodes": set(),
                "agents": set(),
                "projects": set(),
                "tasks": set(),
                "latest_at": "",
                "n8n_success": 0,
                "n8n_non_success": 0,
            },
        )
        group["sessions"] += count
        group["records"] += 1
        group["nodes"].add(row.get("node") or "unknown")
        group["agents"].add(row.get("agent") or "unknown")
        group["projects"].add(row.get("project") or "unknown")
        group["tasks"].add(row.get("task") or "unknown")
        latest = str(row.get("latest_at") or row.get("ended_at") or row.get("started_at") or "")
        if latest > group["latest_at"]:
            group["latest_at"] = latest
        group["n8n_success"] += _safe_int(row.get("n8n_success"))
        group["n8n_non_success"] += _safe_int(row.get("n8n_non_success"))
    output = []
    for group in groups.values():
        group["nodes"] = sorted(group["nodes"])
        group["agents"] = sorted(group["agents"])
        group["projects"] = sorted(group["projects"])
        group["tasks"] = sorted(group["tasks"])
        output.append(group)
    return sorted(output, key=lambda item: item["sessions"], reverse=True)[:limit]


def _date_key_from_row(row: Dict[str, Any]) -> str:
    for field in ("date", "latest_at", "ended_at", "started_at", "created_at"):
        value = str(row.get(field) or "").strip()
        if len(value) >= 10 and value[4] == "-" and value[7] == "-":
            return value[:10]
    return ""


def _activity_timeline(rows: Iterable[Dict[str, Any]], limit: int = 500) -> List[Dict[str, Any]]:
    groups: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        date_key = _date_key_from_row(row)
        if not date_key:
            continue
        agent = str(row.get("agent") or "unknown")
        count = _activity_count(row)
        if count <= 0:
            continue
        key = f"{date_key} | {agent}"
        group = groups.setdefault(
            key,
            {
                "date": date_key,
                "agent": agent,
                "activity": 0,
                "total_tokens": 0,
                "known_token_sessions": 0,
                "known_cost_usd": 0.0,
                "known_cost_sessions": 0,
                "nodes": set(),
                "projects": set(),
                "latest_at": "",
                "n8n_success": 0,
                "n8n_non_success": 0,
            },
        )
        group["activity"] += count
        if _tokens_are_known(row):
            group["total_tokens"] += _safe_int(row.get("total_tokens"))
            group["known_token_sessions"] += _safe_int(row.get("known_token_sessions") or 1)
        row_cost = _safe_float(row.get("known_cost_usd") or row.get("estimated_cost_usd") or row.get("actual_cost_usd"))
        if row_cost > 0:
            group["known_cost_usd"] += row_cost
            group["known_cost_sessions"] += 1
        group["nodes"].add(row.get("node") or "unknown")
        group["projects"].add(row.get("project") or row.get("task") or "unknown")
        latest = str(row.get("latest_at") or row.get("ended_at") or row.get("started_at") or "")
        if latest > group["latest_at"]:
            group["latest_at"] = latest
        group["n8n_success"] += _safe_int(row.get("n8n_success"))
        group["n8n_non_success"] += _safe_int(row.get("n8n_non_success"))

    output = []
    for group in groups.values():
        group["nodes"] = sorted(group["nodes"])
        group["projects"] = sorted(group["projects"])
        group["known_cost_usd"] = round(group["known_cost_usd"], 6)
        output.append(group)
    return sorted(output, key=lambda item: (item["date"], item["agent"]))[:limit]


def _with_project_attribution(row: Dict[str, Any]) -> Dict[str, Any]:
    project = normalize_project_name(
        row.get("project") or "unknown",
        source_path=row.get("project_path") or row.get("raw_path"),
        task=row.get("task"),
    )
    return {**row, "project": project}


def _parse_tsv_table(lines: List[str]) -> List[Dict[str, str]]:
    if not lines:
        return []
    payload = "\n".join(lines).strip()
    if not payload:
        return []
    reader = csv.DictReader(io.StringIO(payload), delimiter="\t")
    return [dict(row) for row in reader if any(value not in (None, "") for value in row.values())]


def _parse_sectioned_tsv(output: str) -> Dict[str, List[Dict[str, str]]]:
    raw_sections: Dict[str, List[str]] = {}
    current: Optional[str] = None
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if line.startswith("__") and line.endswith("__"):
            current = line.strip("_").lower()
            raw_sections.setdefault(current, [])
            continue
        if current is not None:
            raw_sections[current].append(raw_line)
    return {name: _parse_tsv_table(lines) for name, lines in raw_sections.items()}


def _annotate_node_data_quality(status_row: Dict[str, Any]) -> Dict[str, Any]:
    status = str(status_row.get("status") or "").lower()
    source_type = str(status_row.get("source_type") or "").lower()
    status_row["current_data_included"] = False
    if status != "connected":
        status_row["data_quality"] = "unavailable"
        status_row["token_included"] = False
        return status_row
    if status_row.get("export_stale"):
        status_row["data_quality"] = "stale"
        status_row["token_included"] = False
        return status_row
    status_row["current_data_included"] = True
    if source_type in ACTIVITY_ONLY_SOURCE_TYPES:
        status_row["data_quality"] = "activity_only"
        status_row["token_included"] = False
        return status_row
    if _safe_int(status_row.get("real_token_total")) > 0 or _safe_int(status_row.get("real_token_records")) > 0:
        status_row["data_quality"] = "real"
        status_row["token_included"] = True
        return status_row
    if _safe_int(status_row.get("estimated_token_total")) > 0 or _safe_int(status_row.get("estimated_token_records")) > 0:
        status_row["data_quality"] = "estimated"
        status_row["token_included"] = True
        return status_row
    if source_type in REAL_TOKEN_SOURCE_TYPES:
        status_row["data_quality"] = "real"
        status_row["token_included"] = True
        return status_row
    status_row["data_quality"] = "unavailable"
    status_row["token_included"] = False
    return status_row


def _run_n8n_ssh_query(node: Dict[str, Any], days: int, limit: int, timeout_seconds: float) -> Dict[str, Any]:
    host = str(node.get("host") or "").strip()
    if not host:
        raise RuntimeError("missing host")
    user = str(node.get("user") or "root").strip() or "root"
    key_path_raw = str(node.get("ssh_key_path") or "").strip()
    if not key_path_raw:
        raise RuntimeError("missing ssh_key_path")
    key_path = pathlib.Path(key_path_raw).expanduser()
    if not key_path.exists():
        raise RuntimeError(f"ssh_key_path not found: {key_path}")

    db_path = str(node.get("db_path") or "/root/.n8n/database.sqlite")
    port = _bounded_int(node.get("port") or 22, 22, 1, 65535)
    days = _bounded_int(days, 30, 1, 3660)
    limit = _bounded_int(limit, 100, 1, 500)
    timeout = float(node.get("timeout_seconds") or timeout_seconds or 4.0)
    connect_timeout = _bounded_int(node.get("ssh_connect_timeout") or min(timeout, 10), 5, 1, 30)

    command = [
        "ssh",
        "-i",
        str(key_path),
        "-p",
        str(port),
        "-o",
        "IdentitiesOnly=yes",
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=accept-new",
        "-o",
        f"ConnectTimeout={connect_timeout}",
        f"{user}@{host}",
        "bash",
        "-s",
        "--",
        db_path,
        str(days),
        str(limit),
    ]
    try:
        proc = subprocess.run(
            command,
            input=N8N_SQLITE_REMOTE_SCRIPT,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"n8n ssh query timed out after {timeout:g}s") from exc

    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or f"ssh exited {proc.returncode}").strip().splitlines()
        raise RuntimeError(detail[-1][:300] if detail else f"ssh exited {proc.returncode}")
    return {
        "sections": _parse_sectioned_tsv(proc.stdout),
        "queried_at": _now().isoformat(),
    }


def _n8n_records_from_sections(sections: Dict[str, List[Dict[str, str]]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    summary_raw = (sections.get("summary") or [{}])[0]
    summary = {
        "workflows": _safe_int(summary_raw.get("workflows")),
        "active_workflows": _safe_int(summary_raw.get("active_workflows")),
        "executions": _safe_int(summary_raw.get("executions")),
        "success": _safe_int(summary_raw.get("success")),
        "non_success": _safe_int(summary_raw.get("non_success")),
        "latest_at": summary_raw.get("latest_at") or "",
    }
    records: List[Dict[str, Any]] = []
    for row in sections.get("workflows") or []:
        executions = _safe_int(row.get("executions"))
        if executions <= 0:
            continue
        workflow = row.get("workflow") or row.get("workflow_id") or "unknown"
        project = normalize_project_name(workflow, task=workflow)
        workflow_id = row.get("workflow_id") or workflow
        non_success = _safe_int(row.get("non_success"))
        records.append(
            {
                "session_id": f"n8n:{workflow_id}",
                "agent": "n8n",
                "source": "n8n_sqlite",
                "source_type": "n8n_ssh",
                "project": project,
                "task": workflow,
                "status": "ok" if non_success == 0 else "warn",
                "sessions": executions,
                "session_count": executions,
                "activity_count": executions,
                "message_count": executions,
                "started_at": row.get("first_at") or row.get("latest_at") or "",
                "ended_at": row.get("latest_at") or row.get("first_at") or "",
                "latest_at": row.get("latest_at") or "",
                "total_tokens": 0,
                "known_token_sessions": 0,
                "token_status": "not_available",
                "cost_status": "not_available",
                "known_cost_usd": 0.0,
                "n8n_workflow_id": workflow_id,
                "n8n_success": _safe_int(row.get("success")),
                "n8n_non_success": non_success,
                "n8n_avg_duration_seconds": _safe_float(row.get("avg_duration_seconds")),
            }
        )
    return records, summary


def _n8n_timeline_records_from_sections(sections: Dict[str, List[Dict[str, str]]]) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for row in sections.get("daily") or []:
        executions = _safe_int(row.get("executions"))
        if executions <= 0:
            continue
        workflow = row.get("workflow") or row.get("workflow_id") or "unknown"
        project = normalize_project_name(workflow, task=workflow)
        workflow_id = row.get("workflow_id") or workflow
        non_success = _safe_int(row.get("non_success"))
        records.append(
            {
                "session_id": f"n8n:daily:{row.get('date') or 'unknown'}:{workflow_id}",
                "agent": "n8n",
                "source": "n8n_sqlite_daily",
                "source_type": "n8n_ssh",
                "project": project,
                "task": workflow,
                "status": "ok" if non_success == 0 else "warn",
                "date": row.get("date") or "",
                "started_at": row.get("date") or row.get("latest_at") or "",
                "ended_at": row.get("latest_at") or row.get("date") or "",
                "latest_at": row.get("latest_at") or row.get("date") or "",
                "sessions": executions,
                "session_count": executions,
                "activity_count": executions,
                "message_count": executions,
                "total_tokens": 0,
                "known_token_sessions": 0,
                "token_status": "not_available",
                "cost_status": "not_available",
                "known_cost_usd": 0.0,
                "n8n_workflow_id": workflow_id,
                "n8n_success": _safe_int(row.get("success")),
                "n8n_non_success": non_success,
            }
        )
    return records


def _node_summary_token_total(status_row: Dict[str, Any]) -> Optional[int]:
    summary = status_row.get("summary")
    if not isinstance(summary, dict):
        return None
    if _safe_int(summary.get("known_token_sessions")) <= 0 and _safe_int(summary.get("total_tokens")) <= 0:
        return None
    return _safe_int(summary.get("total_tokens"))


def _node_summary_token_breakdown(status_row: Dict[str, Any]) -> Optional[Dict[str, int]]:
    summary = status_row.get("summary")
    if not isinstance(summary, dict):
        return None
    raw = summary.get("token_breakdown")
    if not isinstance(raw, dict):
        return None
    breakdown = _empty_token_breakdown()
    for key in breakdown:
        breakdown[key] = _safe_int(raw.get(key))
    if breakdown["included_token_records"] <= 0:
        breakdown["included_token_records"] = breakdown["real_token_records"] + breakdown["estimated_token_records"]
    if breakdown["included_total_tokens"] <= 0:
        breakdown["included_total_tokens"] = breakdown["real_total_tokens"] + breakdown["estimated_total_tokens"]
    return breakdown


def _node_summary_known_token_records(status_row: Dict[str, Any]) -> Optional[int]:
    summary = status_row.get("summary")
    if not isinstance(summary, dict):
        return None
    known = _safe_int(summary.get("known_token_sessions"))
    return known if known > 0 else None


def _node_summary_record_count(status_row: Dict[str, Any]) -> Optional[int]:
    summary = status_row.get("summary")
    if not isinstance(summary, dict):
        return None
    sessions = _safe_int(summary.get("sessions"))
    return sessions if sessions > 0 else None


def _node_summary_cost(status_row: Dict[str, Any]) -> Optional[float]:
    summary = status_row.get("summary")
    if not isinstance(summary, dict):
        return None
    cost = _safe_float(summary.get("known_cost_usd"), default=0.0)
    sessions = _safe_int(summary.get("known_cost_sessions"))
    if cost <= 0 and sessions <= 0:
        return None
    return cost


def _node_summary_cost_sessions(status_row: Dict[str, Any]) -> Optional[int]:
    summary = status_row.get("summary")
    if not isinstance(summary, dict):
        return None
    sessions = _safe_int(summary.get("known_cost_sessions"))
    return sessions if sessions > 0 else None


def _latest_node_time(status_row: Dict[str, Any], records: List[Dict[str, Any]]) -> str:
    candidates: List[str] = []
    summary = status_row.get("summary")
    if isinstance(summary, dict):
        candidates.extend(str(summary.get(field) or "") for field in ("latest_at", "ended_at", "started_at"))
    candidates.extend(str(status_row.get(field) or "") for field in ("latest_at", "exported_at", "queried_at"))
    for row in records:
        candidates.extend(str(row.get(field) or "") for field in ("latest_at", "ended_at", "started_at", "date"))
    candidates = [value for value in candidates if value]
    if not candidates:
        return ""
    return max(candidates, key=lambda value: epoch_from_iso(value) or 0)


def _node_known_cost(status_row: Dict[str, Any], records: List[Dict[str, Any]]) -> float:
    summary_cost = _node_summary_cost(status_row)
    if summary_cost is not None:
        return round(summary_cost, 6)
    total = 0.0
    for row in records:
        total += _safe_float(row.get("known_cost_usd") or row.get("estimated_cost_usd"), default=0.0)
    return round(total, 6)


def _add_node_dashboard_metrics(status_row: Dict[str, Any], records: List[Dict[str, Any]], issue: Optional[str]) -> Dict[str, Any]:
    sample_records = _safe_int(status_row.get("records"))
    summary_records = _node_summary_record_count(status_row)
    if summary_records is not None:
        status_row["sample_records"] = sample_records
        status_row["records"] = summary_records
    token_total = _node_summary_token_total(status_row)
    if token_total is None:
        token_total = sum(_safe_int(row.get("total_tokens")) for row in records if _tokens_are_known(row))
    known_token_records = _node_summary_known_token_records(status_row)
    if known_token_records is None:
        known_token_records = sum(1 for row in records if _tokens_are_known(row))
    token_breakdown = _node_summary_token_breakdown(status_row)
    if token_breakdown is None:
        summary = status_row.get("summary") if isinstance(status_row.get("summary"), dict) else {}
        token_breakdown = _normalize_token_breakdown(summary, records)
    status_row["token_total"] = token_total
    status_row["known_token_records"] = known_token_records
    status_row["real_token_total"] = token_breakdown["real_total_tokens"]
    status_row["real_token_records"] = token_breakdown["real_token_records"]
    status_row["estimated_token_total"] = token_breakdown["estimated_total_tokens"]
    status_row["estimated_token_records"] = token_breakdown["estimated_token_records"]
    status_row["unavailable_token_records"] = token_breakdown["unavailable_token_records"]
    status_row["token_breakdown"] = token_breakdown
    status_row["known_cost_usd"] = _node_known_cost(status_row, records)
    status_row["activity_count"] = sum(_activity_count(row) for row in records)
    status_row["latest_at"] = _latest_node_time(status_row, records)
    if issue:
        status_row["issue"] = issue
    return status_row


def _summary_from_records(records: List[Dict[str, Any]], totals: Dict[str, Any]) -> Dict[str, Any]:
    known_cost = 0.0
    known_cost_sessions = 0
    unknown_cost_sessions = 0
    for row in records:
        cost = row.get("known_cost_usd")
        if cost is None:
            cost = row.get("estimated_cost_usd")
        if cost is None:
            cost = row.get("actual_cost_usd")
        if cost is None:
            unknown_cost_sessions += 1
        else:
            known_cost_sessions += 1
            known_cost += _safe_float(cost)
    token_breakdown = _token_breakdown_from_records(records)
    return {
        "sessions": len(records),
        "agents": len({row.get("agent") for row in records if row.get("agent")}),
        "projects": len({row.get("project") for row in records if row.get("project")}),
        "known_token_sessions": token_breakdown["included_token_records"],
        "total_tokens": token_breakdown["included_total_tokens"],
        "token_breakdown": token_breakdown,
        "real_token_sessions": token_breakdown["real_token_records"],
        "real_total_tokens": token_breakdown["real_total_tokens"],
        "estimated_token_sessions": token_breakdown["estimated_token_records"],
        "estimated_total_tokens": token_breakdown["estimated_total_tokens"],
        "unavailable_token_sessions": token_breakdown["unavailable_token_records"],
        "known_cost_usd": round(known_cost, 6),
        "known_cost_sessions": known_cost_sessions,
        "unknown_cost_sessions": unknown_cost_sessions,
        "dedupe_adjusted": True,
        "raw_sessions": _safe_int(totals.get("sessions")) or len(records),
        "raw_total_tokens": _safe_int(totals.get("total_tokens")),
    }


def _record_epoch(row: Dict[str, Any]) -> Optional[float]:
    for field in ("latest_at", "ended_at", "started_at", "created_at", "date"):
        timestamp = epoch_from_iso(str(row.get(field) or ""))
        if timestamp is not None:
            return timestamp
    return None


def _filter_records_by_days(
    records: List[Dict[str, Any]],
    days: Optional[int],
    *,
    now_epoch: Optional[float] = None,
) -> Tuple[List[Dict[str, Any]], bool]:
    if not days:
        return records, False
    cutoff = (now_epoch if now_epoch is not None else _now().timestamp()) - max(1, _safe_int(days)) * 24 * 60 * 60
    filtered = []
    changed = False
    for row in records:
        timestamp = _record_epoch(row)
        if timestamp is not None and timestamp < cutoff:
            changed = True
            continue
        filtered.append(row)
    return filtered, changed


def _local_records_from_ledger(
    ledger: Dict[str, Any],
    *,
    days: Optional[int] = None,
    now_epoch: Optional[float] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    raw_records = [row for row in (ledger.get("recent_sessions") or []) if isinstance(row, dict)]
    raw_records, window_filtered = _filter_records_by_days(raw_records, days, now_epoch=now_epoch)
    records = dedupe_session_rows(raw_records)
    totals = ledger.get("totals") if isinstance(ledger.get("totals"), dict) else {}
    if window_filtered or len(records) != len(raw_records):
        return records, _summary_from_records(records, totals)
    summary = {
        "sessions": _safe_int(totals.get("sessions")),
        "agents": _safe_int(totals.get("agents")),
        "projects": _safe_int(totals.get("projects")),
        "known_token_sessions": _safe_int(totals.get("known_token_sessions")),
        "total_tokens": _safe_int(totals.get("total_tokens")),
        "known_cost_usd": round(_safe_float(totals.get("known_cost_usd")), 6),
        "known_cost_sessions": _safe_int(totals.get("known_cost_sessions")),
        "unknown_cost_sessions": _safe_int(totals.get("unknown_cost_sessions")),
    }
    token_breakdown = _normalize_token_breakdown(summary | {"token_breakdown": totals.get("token_breakdown")}, records)
    summary.update({
        "token_breakdown": token_breakdown,
        "real_token_sessions": token_breakdown["real_token_records"],
        "real_total_tokens": token_breakdown["real_total_tokens"],
        "estimated_token_sessions": token_breakdown["estimated_token_records"],
        "estimated_total_tokens": token_breakdown["estimated_total_tokens"],
        "unavailable_token_sessions": token_breakdown["unavailable_token_records"],
    })
    return records, summary


def _build_local_agent_records(days: int, limit: int) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    from agent_ledger import build_agent_ledger

    return _local_records_from_ledger(build_agent_ledger(days=days, limit=limit))


async def _fetch_n8n_ssh_node(
    node: Dict[str, Any],
    days: int,
    limit: int,
    timeout_seconds: float,
) -> Tuple[str, str, List[Dict[str, Any]], Optional[str], Dict[str, Any]]:
    name = node.get("name") or node.get("host") or "n8n"
    try:
        result = await asyncio.to_thread(_run_n8n_ssh_query, node, days, limit, timeout_seconds)
        records, summary = _n8n_records_from_sections(result["sections"])
        timeline_records = _n8n_timeline_records_from_sections(result["sections"])
        return (
            str(name),
            "connected",
            records,
            None,
            {
                "source_type": "n8n_ssh",
                "summary": summary,
                "timeline_records": timeline_records,
                "queried_at": result.get("queried_at"),
            },
        )
    except Exception as exc:
        return (str(name), "unreachable", [], str(exc), {"source_type": "n8n_ssh"})


async def _fetch_local_agent_node(
    node: Dict[str, Any],
    days: int,
    limit: int,
    timeout_seconds: float,
) -> Tuple[str, str, List[Dict[str, Any]], Optional[str], Dict[str, Any]]:
    name = node.get("name") or "local-agent-ledger"
    cached_ledger = node.get("_local_agent_ledger_data")
    if isinstance(cached_ledger, dict):
        records, summary = _local_records_from_ledger(cached_ledger)
        return (
            str(name),
            "connected",
            records[:limit],
            None,
            {
                "source_type": "local_agent_ledger",
                "summary": summary,
                "cache_age_seconds": cached_ledger.get("_cache_age_seconds"),
            },
        )
    if node.get("_skip_local_agent_scan"):
        return (
            str(name),
            "refreshing",
            [],
            "local agent ledger is refreshing",
            {"source_type": "local_agent_ledger"},
        )
    timeout = float(node.get("timeout_seconds") or max(float(timeout_seconds or 4.0), 25.0))
    try:
        records, summary = await asyncio.wait_for(
            asyncio.to_thread(_build_local_agent_records, days, limit),
            timeout=timeout,
        )
        return (
            str(name),
            "connected",
            records,
            None,
            {
                "source_type": "local_agent_ledger",
                "summary": summary,
            },
        )
    except asyncio.TimeoutError:
        return (
            str(name),
            "unreachable",
            [],
            f"local agent ledger timed out after {timeout:g}s",
            {"source_type": "local_agent_ledger"},
        )
    except Exception as exc:
        return (str(name), "unreachable", [], str(exc), {"source_type": "local_agent_ledger"})


def _resolve_ledger_path(raw_path: Any) -> pathlib.Path:
    path = pathlib.Path(str(raw_path or "")).expanduser()
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def _agent_ledger_file_cache_path(ledger_path: pathlib.Path) -> pathlib.Path:
    digest = hashlib.sha256(str(ledger_path).encode("utf-8")).hexdigest()[:32]
    return AGENT_LEDGER_FILE_CACHE_DIR / f"{digest}.json"


def _cache_agent_ledger_file_data(ledger_path: pathlib.Path, data: Dict[str, Any]) -> None:
    cache_path = _agent_ledger_file_cache_path(ledger_path)
    payload = {
        "cached_at": _now().isoformat(),
        "ledger_path": str(ledger_path),
        "data": data,
    }
    with suppress(OSError, TypeError):
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = cache_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        tmp.replace(cache_path)


def _load_cached_agent_ledger_file_data(ledger_path: pathlib.Path) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
    payload = safe_read_json(_agent_ledger_file_cache_path(ledger_path), default=None)
    if not isinstance(payload, dict):
        return None
    data = payload.get("data")
    if not isinstance(data, dict):
        return None
    cached_at = parse_iso(payload.get("cached_at"))
    if cached_at is None:
        return None
    age_seconds = int(max(0, (_now() - cached_at).total_seconds()))
    if age_seconds > AGENT_LEDGER_FILE_CACHE_MAX_AGE_SECONDS:
        return None
    return data, {**payload, "age_seconds": age_seconds}


def _remote_agent_ledger_cache_path(node: Dict[str, Any], urls: List[str]) -> pathlib.Path:
    node_key = str(node.get("cache_key") or node.get("name") or node.get("host") or "")
    key = node_key + "\n" + "\n".join(urls)
    digest = hashlib.sha256(("http\n" + key).encode("utf-8")).hexdigest()[:32]
    return AGENT_LEDGER_FILE_CACHE_DIR / f"http-{digest}.json"


def _cache_remote_agent_ledger_data(node: Dict[str, Any], urls: List[str], resolved_url: str, data: Dict[str, Any]) -> None:
    cache_path = _remote_agent_ledger_cache_path(node, urls)
    payload = {
        "cached_at": _now().isoformat(),
        "cache_key": str(node.get("cache_key") or node.get("name") or node.get("host") or ""),
        "resolved_url": resolved_url,
        "attempted_urls": urls,
        "data": data,
    }
    with suppress(OSError, TypeError):
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = cache_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        tmp.replace(cache_path)


def _load_cached_remote_agent_ledger_data(node: Dict[str, Any], urls: List[str]) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
    payload = safe_read_json(_remote_agent_ledger_cache_path(node, urls), default=None)
    if not isinstance(payload, dict):
        return None
    data = payload.get("data")
    if not isinstance(data, dict):
        return None
    cached_at = parse_iso(payload.get("cached_at"))
    if cached_at is None:
        return None
    age_seconds = int(max(0, (_now() - cached_at).total_seconds()))
    if age_seconds > AGENT_LEDGER_FILE_CACHE_MAX_AGE_SECONDS:
        return None
    return data, {**payload, "age_seconds": age_seconds}


def _read_agent_ledger_file_with_cache(ledger_path: pathlib.Path) -> Tuple[Optional[Dict[str, Any]], Optional[str], Dict[str, Any]]:
    try:
        data = safe_read_json(ledger_path, None)
    except Exception as exc:
        data = None
        read_issue = str(exc)
    else:
        read_issue = f"ledger file is missing or invalid: {ledger_path}"

    if isinstance(data, dict):
        _cache_agent_ledger_file_data(ledger_path, data)
        return data, None, {"ledger_cache_status": "fresh"}

    cached = _load_cached_agent_ledger_file_data(ledger_path)
    if cached is None:
        return None, read_issue, {}
    cached_data, cache_meta = cached
    return (
        cached_data,
        None,
        {
            "ledger_cache_status": "stale",
            "stale_ledger_cache": True,
            "ledger_cache_cached_at": cache_meta.get("cached_at"),
            "ledger_cache_age_seconds": cache_meta.get("age_seconds"),
            "ledger_cache_issue": read_issue,
        },
    )


async def _fetch_agent_ledger_file_node(
    node: Dict[str, Any],
    days: int,
) -> Tuple[str, str, List[Dict[str, Any]], Optional[str], Dict[str, Any]]:
    name = node.get("name") or node.get("host") or "agent-ledger-file"
    raw_path = node.get("ledger_path") or node.get("path") or node.get("file_path")
    if not raw_path:
        return (str(name), "missing_url", [], "missing ledger_path", {"source_type": "agent_ledger_file"})
    ledger_path = _resolve_ledger_path(raw_path)
    data, issue, cache_meta = await asyncio.to_thread(_read_agent_ledger_file_with_cache, ledger_path)
    if not isinstance(data, dict):
        return (
            str(name),
            "unreachable",
            [],
            issue or f"ledger file is missing or invalid: {ledger_path}",
            {"source_type": "agent_ledger_file", "ledger_path": str(ledger_path)},
        )
    now = _now()
    records, summary = _local_records_from_ledger(data, days=days, now_epoch=now.timestamp())
    exported_at = data.get("generated_at")
    export_age_seconds = None
    export_timestamp = epoch_from_iso(str(exported_at or ""))
    if export_timestamp is not None:
        export_age_seconds = max(0, int(now.timestamp() - export_timestamp))
    max_export_age = max(
        60,
        _safe_int(node.get("max_export_age_seconds"), AGENT_LEDGER_FILE_EXPORT_MAX_AGE_SECONDS),
    )
    freshness_issue = None
    operator_hint = None
    if export_age_seconds is not None and export_age_seconds > max_export_age:
        freshness_issue = (
            f"ledger export is stale: generated_at={exported_at}, "
            f"age_seconds={export_age_seconds}, max_age_seconds={max_export_age}"
        )
        operator_hint = (
            "建议优先在该机器安装只读账本服务，让主节点主动拉取 /agent-ledger；"
            "如果继续使用 shared directory 文件备用，请恢复每小时导出或手动重新导出后刷新。"
        )
    return (
        str(name),
        "connected",
        records,
        freshness_issue,
        {
            "source_type": "agent_ledger_file",
            "ledger_path": str(ledger_path),
            "summary": summary,
            "exported_at": exported_at,
            "export_age_seconds": export_age_seconds,
            "max_export_age_seconds": max_export_age,
            "export_stale": bool(freshness_issue),
            "operator_hint": operator_hint,
            **cache_meta,
        },
    )


async def _fetch_node(
    client: httpx.AsyncClient,
    node: Dict[str, Any],
    days: int,
    limit: int,
    timeout_seconds: float,
) -> Tuple[str, str, List[Dict[str, Any]], Optional[str], Dict[str, Any]]:
    """并发拉取单个节点的 ledger 数据。返回 (name, status, records, issue, meta)。"""
    name = node.get("name") or node.get("host") or node.get("base_url") or "unknown"
    if node.get("enabled") is False:
        return (name, "disabled", [], None, {})
    node_type = str(node.get("type") or "").lower()
    if node_type in LOCAL_AGENT_NODE_TYPES:
        return await _fetch_local_agent_node(node, days, limit, timeout_seconds=timeout_seconds)
    if node_type in AGENT_LEDGER_FILE_NODE_TYPES:
        return await _fetch_agent_ledger_file_node(node, days=days)
    if node_type == "n8n_ssh":
        return await _fetch_n8n_ssh_node(node, days, limit, timeout_seconds=timeout_seconds)
    urls = _node_url_candidates(node, days, limit)
    if not urls:
        return (name, "missing_url", [], "missing ledger_url or base_url", {})
    node_timeout = min(
        float(node.get("timeout_seconds") or timeout_seconds or 4.0),
        float(AGENT_LEDGER_HTTP_TIMEOUT_MAX_SECONDS),
    )
    cached = _load_cached_remote_agent_ledger_data(node, urls)
    fresh_cache_seconds = max(
        0,
        _safe_int(
            node.get("http_cache_fresh_seconds") or node.get("cache_fresh_seconds"),
            AGENT_LEDGER_HTTP_CACHE_FRESH_SECONDS,
        ),
    )
    if cached is not None and fresh_cache_seconds > 0:
        cached_data, cache_meta = cached
        if int(cache_meta.get("age_seconds") or 0) <= fresh_cache_seconds:
            records, summary = _local_records_from_ledger(cached_data)
            return (
                name,
                "connected",
                records,
                None,
                {
                    "source_type": "smart_gateway",
                    "summary": summary,
                    "queried_at": _now().isoformat(),
                    "resolved_url": cache_meta.get("resolved_url"),
                    "attempted_urls": [],
                    "ledger_cache_status": "fresh_http",
                    "stale_ledger_cache": False,
                    "ledger_cache_cached_at": cache_meta.get("cached_at"),
                    "ledger_cache_age_seconds": cache_meta.get("age_seconds"),
                },
            )
    if cached is not None:
        node_timeout = min(node_timeout, float(AGENT_LEDGER_HTTP_STALE_REFRESH_TIMEOUT_SECONDS))
    attempted_urls: List[str] = []
    errors: List[str] = []
    for url in urls:
        attempted_urls.append(url)
        try:
            resp = await client.get(url, timeout=node_timeout)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, dict) and isinstance(data.get("recent_sessions"), list):
                _cache_remote_agent_ledger_data(node, urls, url, data)
                records, summary = _local_records_from_ledger(data)
                remote_cache_status = data.get("_ledger_cache_status")
                remote_cache_stale = bool(
                    data.get("_stale")
                    or data.get("_refreshing")
                    or data.get("_ledger_cache_fallback")
                    or data.get("_last_refresh_failed")
                )
                cache_meta = {}
                if remote_cache_stale:
                    cache_meta.update({
                        "ledger_cache_status": remote_cache_status or "stale_remote",
                        "stale_ledger_cache": True,
                        "ledger_cache_age_seconds": data.get("_cache_age_seconds"),
                        "ledger_cache_issue": data.get("_ledger_cache_issue"),
                        "operator_hint": data.get("_ledger_cache_issue")
                        or "远端只读账本服务正在后台刷新，当前显示该节点上次可用快照。",
                    })
                return (
                    name,
                    "connected",
                    records,
                    None,
                    {
                        "source_type": "smart_gateway",
                        "summary": summary,
                        "queried_at": _now().isoformat(),
                        "resolved_url": url,
                        "attempted_urls": attempted_urls,
                        **cache_meta,
                    },
                )
            return (
                name,
                "connected",
                [],
                None,
                {
                    "source_type": "smart_gateway",
                    "queried_at": _now().isoformat(),
                    "resolved_url": url,
                    "attempted_urls": attempted_urls,
                },
            )
        except (httpx.HTTPError, json.JSONDecodeError) as exc:
            errors.append(f"{url}: {exc}")
            continue
    issue = _remote_node_issue(node, name, attempted_urls, errors)
    if cached is not None:
        cached_data, cache_meta = cached
        records, summary = _local_records_from_ledger(cached_data)
        return (
            name,
            "connected",
            records,
            None,
            {
                "source_type": "smart_gateway",
                "summary": summary,
                "queried_at": _now().isoformat(),
                "resolved_url": cache_meta.get("resolved_url"),
                "attempted_urls": attempted_urls,
                "ledger_cache_status": "stale_http",
                "stale_ledger_cache": True,
                "ledger_cache_cached_at": cache_meta.get("cached_at"),
                "ledger_cache_age_seconds": cache_meta.get("age_seconds"),
                "ledger_cache_issue": issue,
                "operator_hint": issue,
            },
        )
    return (
        name,
        "unreachable",
        [],
        issue,
        {
            "source_type": "smart_gateway",
            "attempted_urls": attempted_urls,
            "operator_hint": issue,
        },
    )


async def build_fleet_ledger(
    days: int = 30,
    limit: int = 100,
    timeout_seconds: float = 4.0,
    local_agent_ledger: Optional[Dict[str, Any]] = None,
    skip_local_agent_scan: bool = False,
) -> Dict[str, Any]:
    """构建 Fleet 聚合账本 — 并发拉取所有已配置节点。

    改进: 使用 httpx.AsyncClient + asyncio.gather 并发拉取,
    N 个节点总耗时 = max(单节点延迟) 而非 sum(单节点延迟)。
    """
    config = _load_config()
    nodes = [node for node in (config.get("nodes") or []) if isinstance(node, dict)]
    fetch_nodes: List[Dict[str, Any]] = []
    for node in nodes:
        next_node = dict(node)
        node_type = str(next_node.get("type") or "").lower()
        if node_type in LOCAL_AGENT_NODE_TYPES:
            if isinstance(local_agent_ledger, dict):
                next_node["_local_agent_ledger_data"] = local_agent_ledger
            elif skip_local_agent_scan:
                next_node["_skip_local_agent_scan"] = True
        fetch_nodes.append(next_node)
    rows: List[Dict[str, Any]] = []
    excluded_stale_rows: List[Dict[str, Any]] = []
    timeline_rows: List[Dict[str, Any]] = []
    excluded_stale_timeline_rows: List[Dict[str, Any]] = []
    timeline_nodes: set[str] = set()
    node_status: List[Dict[str, Any]] = []
    access_issues: List[Dict[str, Any]] = []

    if nodes:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            results = await asyncio.gather(
                *[_fetch_node(client, node, days, limit, timeout_seconds) for node in fetch_nodes],
                return_exceptions=True,
            )

        for node, result in zip(fetch_nodes, results):
            name = node.get("name") or node.get("host") or node.get("base_url") or "unknown"
            url = _node_url(node, days, limit) or ""
            if isinstance(result, Exception):
                issue = str(result)
                status_row = _add_node_dashboard_metrics({"node": name, "status": "error", "records": 0}, [], issue)
                node_status.append(_annotate_node_data_quality(status_row))
                access_issues.append({"node": name, "issue": issue})
                continue
            n, status, records, issue, meta = result
            status_row = {"node": n, "status": status, "records": len(records)}
            if isinstance(meta, dict):
                status_row.update({
                    key: value
                    for key, value in meta.items()
                    if value is not None and key != "timeline_records"
                })
            status_row = _add_node_dashboard_metrics(status_row, records, issue)
            status_row = _annotate_node_data_quality(status_row)
            node_status.append(status_row)
            current_data_included = bool(status_row.get("current_data_included"))
            if issue:
                access_issues.append({"node": n, "issue": issue})
            if isinstance(meta, dict):
                for timeline_row in meta.get("timeline_records") or []:
                    if isinstance(timeline_row, dict):
                        row_node = str(timeline_row.get("source_node") or n)
                        timeline_nodes.add(str(n))
                        target_timeline_rows = timeline_rows if current_data_included else excluded_stale_timeline_rows
                        target_timeline_rows.append({
                            **_with_project_attribution(timeline_row),
                            "node": row_node,
                            "ingest_node": n if row_node != str(n) else None,
                            "node_host": node.get("host") or node.get("base_url") or url,
                        })
            for row in records:
                if not isinstance(row, dict):
                    continue
                row_node = str(row.get("source_node") or n)
                target_rows = rows if current_data_included else excluded_stale_rows
                target_rows.append({
                    **_with_project_attribution(row),
                    "node": row_node,
                    "ingest_node": n if row_node != str(n) else None,
                    "node_host": node.get("host") or node.get("base_url") or url,
                })

    connected_nodes = sum(1 for ns in node_status if ns["status"] == "connected")
    current_node_status = [ns for ns in node_status if ns.get("current_data_included")]
    excluded_stale_node_status = [ns for ns in node_status if ns.get("export_stale")]
    real_token_nodes = sum(1 for ns in current_node_status if ns.get("data_quality") == "real")
    estimated_token_nodes = sum(1 for ns in current_node_status if ns.get("data_quality") == "estimated")
    activity_only_nodes = sum(1 for ns in current_node_status if ns.get("data_quality") == "activity_only")
    unavailable_nodes = sum(1 for ns in node_status if ns.get("data_quality") == "unavailable")
    # 聚合费用
    fleet_cost = 0.0
    fleet_cost_sessions = 0
    for row in rows:
        row_cost = float(row.get("known_cost_usd") or row.get("estimated_cost_usd") or 0)
        if row_cost > 0:
            fleet_cost += row_cost
            fleet_cost_sessions += 1
    n8n_summaries = [
        ns.get("summary") or {}
        for ns in node_status
        if ns.get("source_type") == "n8n_ssh" and isinstance(ns.get("summary"), dict)
    ]
    trend_rows = [
        row
        for row in rows
        if not (row.get("source_type") == "n8n_ssh" and str(row.get("node") or "") in timeline_nodes)
    ] + timeline_rows
    row_token_total = sum(_safe_int(row.get("total_tokens")) for row in rows if _tokens_are_known(row))
    row_known_token_records = sum(1 for row in rows if _tokens_are_known(row))
    row_token_breakdown = _token_breakdown_from_records(rows)
    node_token_breakdown = _empty_token_breakdown()
    node_breakdown_rows = 0
    for status_row in current_node_status:
        breakdown = status_row.get("token_breakdown")
        if not isinstance(breakdown, dict):
            continue
        node_breakdown_rows += 1
        for key in node_token_breakdown:
            node_token_breakdown[key] += _safe_int(breakdown.get(key))
    summary_token_total = 0
    summary_known_token_records = 0
    summary_token_nodes = 0
    summary_records = 0
    summary_record_nodes = 0
    summary_cost_total = 0.0
    summary_cost_sessions = 0
    summary_cost_nodes = 0
    for status_row in current_node_status:
        node_records = _node_summary_record_count(status_row)
        if node_records is not None:
            summary_records += node_records
            summary_record_nodes += 1

        node_total = _node_summary_token_total(status_row)
        if node_total is not None:
            summary_token_total += node_total
            summary_token_nodes += 1
            known_records = _node_summary_known_token_records(status_row)
            if known_records is not None:
                summary_known_token_records += known_records
        node_cost = _node_summary_cost(status_row)
        if node_cost is not None:
            summary_cost_total += node_cost
            summary_cost_nodes += 1
            cost_sessions = _node_summary_cost_sessions(status_row)
            if cost_sessions is not None:
                summary_cost_sessions += cost_sessions
    excluded_stale_token_breakdown = _empty_token_breakdown()
    excluded_stale_breakdown_nodes = 0
    excluded_stale_summary_total = 0
    excluded_stale_known_records = 0
    excluded_stale_records = 0
    for status_row in excluded_stale_node_status:
        node_records = _node_summary_record_count(status_row)
        if node_records is not None:
            excluded_stale_records += node_records
        node_total = _node_summary_token_total(status_row)
        if node_total is not None:
            excluded_stale_summary_total += node_total
            known_records = _node_summary_known_token_records(status_row)
            if known_records is not None:
                excluded_stale_known_records += known_records
        breakdown = status_row.get("token_breakdown")
        if isinstance(breakdown, dict):
            excluded_stale_breakdown_nodes += 1
            for key in excluded_stale_token_breakdown:
                excluded_stale_token_breakdown[key] += _safe_int(breakdown.get(key))
    if not excluded_stale_breakdown_nodes:
        excluded_stale_token_breakdown = _token_breakdown_from_records(excluded_stale_rows)
    if excluded_stale_records <= 0:
        excluded_stale_records = len(excluded_stale_rows)
    if excluded_stale_summary_total <= 0:
        excluded_stale_summary_total = excluded_stale_token_breakdown["included_total_tokens"]
    if excluded_stale_known_records <= 0:
        excluded_stale_known_records = excluded_stale_token_breakdown["included_token_records"]

    total_tokens = summary_token_total if summary_token_nodes else row_token_total
    known_token_records = summary_known_token_records if summary_token_nodes else row_known_token_records
    token_breakdown = node_token_breakdown if node_breakdown_rows else row_token_breakdown
    if token_breakdown["included_total_tokens"] <= 0 and total_tokens > 0:
        token_breakdown["included_total_tokens"] = total_tokens
    if token_breakdown["included_token_records"] <= 0 and known_token_records > 0:
        token_breakdown["included_token_records"] = known_token_records
    record_count = summary_records if summary_record_nodes else len(rows)
    known_cost_usd = summary_cost_total if summary_cost_nodes else fleet_cost
    known_cost_sessions = summary_cost_sessions if summary_cost_nodes else fleet_cost_sessions
    current_data_nodes = [
        ns.get("node") or "unknown"
        for ns in node_status
        if ns.get("current_data_included")
    ]
    stale_nodes = [
        ns.get("node") or "unknown"
        for ns in node_status
        if ns.get("export_stale") or ns.get("stale_ledger_cache")
    ]
    unavailable_node_names = [
        ns.get("node") or "unknown"
        for ns in node_status
        if ns.get("status") in {"unreachable", "error", "missing_url"}
    ]
    health_issue_nodes = {
        str(issue.get("node") or "unknown")
        for issue in access_issues
        if isinstance(issue, dict)
    }
    health_issue_nodes.update(str(node) for node in stale_nodes)
    health_issue_nodes.update(str(node) for node in unavailable_node_names)
    node_health_status = (
        "not_configured"
        if not nodes
        else ("complete" if connected_nodes == len(nodes) and not health_issue_nodes else "partial")
    )
    node_health = {
        "status": node_health_status,
        "complete": node_health_status == "complete",
        "configured_nodes": len(nodes),
        "connected_nodes": connected_nodes,
        "current_data_nodes": current_data_nodes,
        "current_data_node_count": len(current_data_nodes),
        "stale_nodes": stale_nodes,
        "stale_node_count": len(stale_nodes),
        "issue_count": len(health_issue_nodes),
        "unavailable_nodes": unavailable_node_names,
        "excluded_nodes": sorted(set(stale_nodes + unavailable_node_names)),
    }
    data_trust = _build_fleet_data_trust(
        nodes_configured=len(nodes),
        connected_nodes=connected_nodes,
        current_data_nodes=len(current_data_nodes),
        stale_nodes=stale_nodes,
        unavailable_nodes=unavailable_node_names,
        access_issues=access_issues,
        token_breakdown=token_breakdown,
        total_records=record_count,
        excluded_stale_records=excluded_stale_records,
        excluded_stale_total_tokens=excluded_stale_summary_total,
    )
    return {
        "generated_at": _now().isoformat(),
        "window_days": days,
        "config_path": str(CONFIG_PATH),
        "authorized_networks": config.get("authorized_networks") or [],
        "discovery": config.get("discovery") or {"active_scan": False, "passive_arp": False},
        "totals": {
            "configured_nodes": len(nodes),
            "connected_nodes": connected_nodes,
            "current_data_nodes": len(current_data_nodes),
            "stale_nodes": len(stale_nodes),
            "records": record_count,
            "known_token_records": known_token_records,
            "total_tokens": total_tokens,
            "real_total_tokens": token_breakdown["real_total_tokens"],
            "real_token_records": token_breakdown["real_token_records"],
            "estimated_total_tokens": token_breakdown["estimated_total_tokens"],
            "estimated_token_records": token_breakdown["estimated_token_records"],
            "unavailable_token_records": token_breakdown["unavailable_token_records"],
            "token_breakdown": token_breakdown,
            "known_cost_usd": round(known_cost_usd, 6),
            "known_cost_sessions": known_cost_sessions,
            "token_total_source": "node_summary" if summary_token_nodes else "row_sample",
            "summary_token_nodes": summary_token_nodes,
            "summary_breakdown_nodes": node_breakdown_rows,
            "summary_record_nodes": summary_record_nodes,
            "row_sample_records": len(rows),
            "row_sample_total_tokens": row_token_total,
            "activity_sessions": sum(_activity_count(row) for row in rows),
            "excluded_stale_nodes": len(excluded_stale_node_status),
            "excluded_stale_records": excluded_stale_records,
            "excluded_stale_token_records": excluded_stale_known_records,
            "excluded_stale_total_tokens": excluded_stale_summary_total,
            "excluded_stale_real_total_tokens": excluded_stale_token_breakdown["real_total_tokens"],
            "excluded_stale_real_token_records": excluded_stale_token_breakdown["real_token_records"],
            "excluded_stale_estimated_total_tokens": excluded_stale_token_breakdown["estimated_total_tokens"],
            "excluded_stale_estimated_token_records": excluded_stale_token_breakdown["estimated_token_records"],
            "excluded_stale_activity_sessions": sum(_activity_count(row) for row in excluded_stale_rows),
            "n8n_workflows": sum(_safe_int(summary.get("workflows")) for summary in n8n_summaries),
            "n8n_active_workflows": sum(_safe_int(summary.get("active_workflows")) for summary in n8n_summaries),
            "n8n_executions": sum(_safe_int(summary.get("executions")) for summary in n8n_summaries),
            "n8n_success": sum(_safe_int(summary.get("success")) for summary in n8n_summaries),
            "n8n_non_success": sum(_safe_int(summary.get("non_success")) for summary in n8n_summaries),
            "data_complete": node_health["complete"],
            "node_issue_count": node_health["issue_count"],
            "real_token_nodes": real_token_nodes,
            "estimated_token_nodes": estimated_token_nodes,
            "activity_only_nodes": activity_only_nodes,
            "unavailable_nodes": unavailable_nodes,
        },
        "node_health": node_health,
        "data_trust": data_trust,
        "nodes": node_status,
        "agent_token_rank": _rank(rows, ["agent"]),
        "project_token_rank": _rank(rows, ["project"]),
        "task_token_rank": _rank(rows, ["project", "task"]),
        "model_token_rank": _rank(rows, ["model"]),
        "node_token_rank": _rank(rows, ["node"]),
        "node_agent_token_rank": _rank(rows, ["node", "agent"]),
        "agent_activity_rank": _activity_rank(rows, ["agent"]),
        "project_activity_rank": _activity_rank(rows, ["project"]),
        "node_activity_rank": _activity_rank(rows, ["node"]),
        "task_activity_rank": _activity_rank(rows, ["project", "task"]),
        "node_agent_activity_rank": _activity_rank(rows, ["node", "agent"]),
        "activity_timeline": _activity_timeline(trend_rows),
        "access_issues": access_issues,
        "notes": [
            "除非明确配置到 data/company-agent-nodes.json，否则不会扫描任何团队设备。",
            "路由器发现只能识别设备，token 排行必须依赖已授权的账本接口、SSH/MDM 权限，或每台电脑导出的账本。",
            "n8n_ssh 节点只统计工作流执行活动；除非 n8n 的 LLM 调用经过本项目网关，否则不会产生 token/cost 排行。",
            "缺失 token 的记录不会估算，也不会进入 token 排行。",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(asyncio.run(build_fleet_ledger()), ensure_ascii=False, indent=2))
