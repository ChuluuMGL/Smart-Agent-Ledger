#!/usr/bin/env python3
"""采集器: 从各 AI 工具本地数据收集用量记录 (从 agent_ledger.py 拆分)。"""
from collector_utils import *  # noqa: F401,F403  — 共享工具/常量/stdlib

def collect_gateway_events(days: int) -> List[Dict[str, Any]]:
    # P1.2: 读取当前文件和轮转文件
    event_files = _gateway_event_files()
    if not event_files:
        return []
    cutoff = _now() - dt.timedelta(days=days)
    rows: List[Dict[str, Any]] = []
    for log_path in event_files:
        try:
            with log_path.open(errors="ignore") as f:
                for line in f:
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    ts = event.get("timestamp")
                    if not _within_window(ts, cutoff):
                        continue
                    project = normalize_project_name(
                        event.get("project") or project_from_cwd(event.get("project_path")),
                        source_path=event.get("project_path"),
                        task=event.get("task"),
                    )
                    cost_value = _safe_float(event.get("estimated_cost_usd"))
                    total_tokens = _safe_int(event.get("total_tokens"))
                    rows.append(
                        {
                            "agent": event.get("agent") or "Gateway Client",
                            "source": event.get("source") or "gateway",
                            "source_node": event.get("source_node"),
                            "session_id": event.get("session_id") or event.get("request_id"),
                            "project": project,
                            "project_path": event.get("project_path"),
                            "task": _shorten(event.get("task") or "Gateway request", 140),
                            "status": event.get("status") or "recorded",
                            "started_at": ts,
                            "ended_at": ts,
                            "model": event.get("model"),
                            "provider": event.get("provider"),
                            "input_tokens": _safe_int(event.get("input_tokens")),
                            "output_tokens": _safe_int(event.get("output_tokens")),
                            "total_tokens": total_tokens,
                            "token_status": "gateway_reported" if total_tokens > 0 else "unknown",
                            "estimated_cost_usd": cost_value,
                            "actual_cost_usd": _safe_float(event.get("actual_cost_usd")),
                            "cost_status": event.get("cost_status") or ("gateway_reported" if cost_value is not None else "unknown"),
                            "message_count": _safe_int(event.get("media_units")) or 1,
                            "session_count": _safe_int(event.get("session_count")) or 1,
                            "tool_call_count": 0,
                            "duration_ms": _safe_int(event.get("duration_ms")),
                            "media_units": _safe_int(event.get("media_units")),
                            "video_seconds": _safe_float(event.get("video_seconds")),
                            "image_count": _safe_int(event.get("image_count")),
                            "n8n_workflow_id": event.get("n8n_workflow_id"),
                            "n8n_execution_id": event.get("n8n_execution_id"),
                            "provider_task_id": event.get("provider_task_id"),
                            "confidence": event.get("confidence") or "reported_by_gateway",
                            "raw_path": str(log_path),
                        }
                    )
        except Exception:
            continue
    return rows


def collect_hermes_sessions(days: int) -> List[Dict[str, Any]]:
    db = HOME / ".hermes/state.db"
    if not db.exists():
        return []
    cutoff = (_now() - dt.timedelta(days=days)).timestamp()
    query = """
    select
      id, source, model, billing_provider, started_at, ended_at, end_reason,
      message_count, tool_call_count, input_tokens, output_tokens,
      cache_read_tokens, cache_write_tokens, reasoning_tokens,
      estimated_cost_usd, actual_cost_usd, cost_status, title, cwd,
      handoff_platform, handoff_error
    from sessions
    where started_at >= ?
    order by started_at desc
    """
    rows: List[Dict[str, Any]] = []
    try:
        con = sqlite3.connect(db)
        con.row_factory = sqlite3.Row
        for row in con.execute(query, (cutoff,)):
            tokens = sum(
                _safe_int(row[k])
                for k in [
                    "input_tokens",
                    "output_tokens",
                    "cache_read_tokens",
                    "cache_write_tokens",
                    "reasoning_tokens",
                ]
            )
            status = "active" if row["ended_at"] is None else (row["end_reason"] or "ended")
            rows.append(
                {
                    "agent": "Hermes",
                    "source": row["source"] or "hermes",
                    "session_id": row["id"],
                    "project": project_from_cwd(row["cwd"]),
                    "project_path": row["cwd"],
                    "task": _safe_title(row["title"], "Hermes session"),
                    "status": status,
                    "started_at": _iso_from_epoch(row["started_at"]),
                    "ended_at": _iso_from_epoch(row["ended_at"]),
                    "model": row["model"],
                    "provider": row["billing_provider"],
                    "input_tokens": _safe_int(row["input_tokens"]),
                    "output_tokens": _safe_int(row["output_tokens"]),
                    "total_tokens": tokens,
                    "token_status": "hermes_state_db" if tokens > 0 else "unknown",
                    "estimated_cost_usd": _safe_float(row["estimated_cost_usd"]),
                    "actual_cost_usd": _safe_float(row["actual_cost_usd"]),
                    "cost_status": row["cost_status"] or "unknown",
                    "message_count": _safe_int(row["message_count"]),
                    "tool_call_count": _safe_int(row["tool_call_count"]),
                    "handoff_platform": row["handoff_platform"],
                    "handoff_error": row["handoff_error"],
                    "confidence": "parsed_local_db",
                    "raw_path": str(db),
                }
            )
    except Exception:
        return []
    finally:
        try:
            con.close()
        except sqlite3.Error:
            pass
    return rows


def _codex_token_usage(payload: Dict[str, Any]) -> Dict[str, int]:
    info = payload.get("info") or {}
    usage = info.get("total_token_usage") or {}
    input_tokens = _safe_int(usage.get("input_tokens"))
    cached_input_tokens = _safe_int(usage.get("cached_input_tokens"))
    output_tokens = _safe_int(usage.get("output_tokens"))
    reasoning_output_tokens = _safe_int(usage.get("reasoning_output_tokens"))
    return {
        "input_tokens": input_tokens + cached_input_tokens,
        "output_tokens": output_tokens + reasoning_output_tokens,
        "cached_input_tokens": cached_input_tokens,
        "reasoning_output_tokens": reasoning_output_tokens,
        "raw_total_tokens": _safe_int(usage.get("total_tokens")),
        "total_tokens": input_tokens + cached_input_tokens + output_tokens + reasoning_output_tokens,
    }


def _subtract_token_usage(current: Dict[str, int], baseline: Dict[str, int]) -> Dict[str, int]:
    keys = ["input_tokens", "output_tokens", "cached_input_tokens", "reasoning_output_tokens", "raw_total_tokens", "total_tokens"]
    return {key: max(0, _safe_int(current.get(key)) - _safe_int(baseline.get(key))) for key in keys}


def collect_codex_sessions(days: int) -> List[Dict[str, Any]]:
    root = HOME / ".codex/sessions"
    if not root.exists():
        return []
    cutoff = _now() - dt.timedelta(days=days)
    rows: List[Dict[str, Any]] = []
    paths = sorted(glob.glob(str(root / "**/*.jsonl"), recursive=True), key=os.path.getmtime, reverse=True)
    for path_text in paths:
        path = pathlib.Path(path_text)
        try:
            if dt.datetime.fromtimestamp(path.stat().st_mtime, dt.timezone.utc) < cutoff:
                continue
        except OSError:
            pass
        session_id = None
        source = None
        cwd = None
        model_provider = None
        started_at = None
        latest_at = None
        first_user = None
        user_messages = 0
        tool_calls = 0
        best_tokens = {
            "input_tokens": 0,
            "output_tokens": 0,
            "cached_input_tokens": 0,
            "reasoning_output_tokens": 0,
            "raw_total_tokens": 0,
            "total_tokens": 0,
        }
        baseline_tokens = dict(best_tokens)
        has_token_after_cutoff = False
        try:
            with path.open(errors="ignore") as f:
                for line in f:
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    ts = obj.get("timestamp")
                    if ts:
                        latest_at = ts
                    payload = obj.get("payload") or {}
                    if obj.get("type") == "session_meta":
                        session_id = payload.get("id") or session_id
                        cwd = payload.get("cwd") or cwd
                        source = payload.get("originator") or payload.get("source") or source
                        model_provider = payload.get("model_provider") or model_provider
                        started_at = payload.get("timestamp") or ts or started_at
                    elif obj.get("type") == "turn_context":
                        cwd = payload.get("cwd") or cwd
                    elif obj.get("type") == "response_item":
                        if payload.get("role") == "user":
                            user_messages += 1
                            if first_user is None:
                                first_user = payload.get("content")
                        if payload.get("type") in {"function_call", "tool_call"}:
                            tool_calls += 1
                    elif obj.get("type") == "event_msg" and payload.get("type") == "token_count":
                        usage = _codex_token_usage(payload)
                        parsed_ts = _parse_iso(ts)
                        if parsed_ts and parsed_ts < cutoff:
                            if usage["total_tokens"] >= baseline_tokens["total_tokens"]:
                                baseline_tokens = usage
                        else:
                            has_token_after_cutoff = True
                            if usage["total_tokens"] >= best_tokens["total_tokens"]:
                                best_tokens = usage
        except Exception:
            continue
        if not session_id and not latest_at:
            continue
        effective_ts = latest_at or started_at
        if not _within_window(effective_ts, cutoff):
            continue
        if has_token_after_cutoff:
            best_tokens = _subtract_token_usage(best_tokens, baseline_tokens)
        latest_dt = _parse_iso(latest_at)
        status = "recent" if latest_dt and (_now() - latest_dt) <= dt.timedelta(minutes=30) else "recorded"
        # Codex 的 model_provider 通常是 "openai"（提供商名），映射为具体模型名
        resolved_model = model_provider
        if model_provider == "openai":
            resolved_model = "codex-mini"
        rows.append(
            {
                "agent": "Codex",
                "source": source or "codex",
                "session_id": session_id or path.stem,
                "project": project_from_cwd(cwd),
                "project_path": cwd,
                "task": _safe_title(first_user, "Codex session"),
                "status": status,
                "started_at": started_at or effective_ts,
                "ended_at": latest_at,
                "model": resolved_model,
                "provider": model_provider,
                "input_tokens": best_tokens["input_tokens"],
                "output_tokens": best_tokens["output_tokens"],
                "cached_input_tokens": best_tokens["cached_input_tokens"],
                "reasoning_output_tokens": best_tokens["reasoning_output_tokens"],
                "raw_total_tokens": best_tokens["raw_total_tokens"],
                "total_tokens": best_tokens["total_tokens"],
                "token_status": "codex_token_count_event_window_full" if best_tokens["total_tokens"] > 0 else "unknown",
                "estimated_cost_usd": None,
                "cost_status": "local_token_estimate_only",
                "message_count": user_messages,
                "tool_call_count": tool_calls,
                "confidence": "parsed_local_jsonl",
                "raw_path": str(path),
            }
        )
    return rows


def collect_claude_cache(days: int) -> List[Dict[str, Any]]:
    path = HOME / ".claude/stats-cache.json"
    if not path.exists():
        return []
    cutoff_date = (_now() - dt.timedelta(days=days)).date()
    try:
        data = json.loads(path.read_text(errors="ignore"))
    except (json.JSONDecodeError, OSError):
        return []
    sessions = 0
    messages = 0
    tools = 0
    latest = None
    for day in data.get("dailyActivity", []):
        try:
            current_date = dt.datetime.strptime(day.get("date", ""), "%Y-%m-%d").date()
        except (json.JSONDecodeError, OSError):
            continue
        if current_date < cutoff_date:
            continue
        sessions += _safe_int(day.get("sessionCount"))
        messages += _safe_int(day.get("messageCount"))
        tools += _safe_int(day.get("toolCallCount"))
        latest = max(latest or current_date, current_date)
    if not (sessions or messages or tools):
        return []
    latest_iso = dt.datetime.combine(latest, dt.time.min, tzinfo=dt.timezone.utc).isoformat() if latest else None
    return [
        {
            "agent": "Claude Code",
            "source": "stats-cache",
            "session_id": f"claude-cache-{cutoff_date.isoformat()}",
            "project": "unknown",
            "project_path": None,
            "task": "Claude Code local activity cache",
            "status": "aggregate",
            "started_at": latest_iso,
            "ended_at": latest_iso,
            "model": None,
            "provider": "anthropic-compatible",
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "token_status": "not_available",
            "estimated_cost_usd": None,
            "cost_status": "no_token_or_cost_in_cache",
            "message_count": messages,
            "tool_call_count": tools,
            "session_count": sessions,
            "confidence": "aggregate_cache",
            "raw_path": str(path),
        }
    ]


def _claude_project_dir(cwd: Optional[str]) -> Optional[pathlib.Path]:
    """将 CWD 路径映射为 ~/.claude/projects/ 下的子目录。"""
    if not cwd:
        return None
    # 路径规则：所有非字母数字字符都替换为 -，且以 - 开头
    import re
    dir_name = re.sub(r"[^a-zA-Z0-9]", "-", cwd)
    p = HOME / ".claude" / "projects" / dir_name
    return p if p.is_dir() else None


def _claude_session_usage(session_jsonl: pathlib.Path) -> Dict[str, Any]:
    """从 session JSONL 文件中提取 token 用量和模型信息。"""
    total_input = 0
    total_output = 0
    models: set = set()
    try:
        with session_jsonl.open(errors="ignore") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if obj.get("type") != "assistant":
                    continue
                msg = obj.get("message", {})
                if not isinstance(msg, dict):
                    continue
                usage = msg.get("usage", {})
                if isinstance(usage, dict):
                    total_input += _safe_int(usage.get("input_tokens"))
                    total_output += _safe_int(usage.get("output_tokens"))
                    # 也计入 cache tokens
                    total_input += _safe_int(usage.get("cache_read_input_tokens"))
                    total_input += _safe_int(usage.get("cache_creation_input_tokens"))
                model = msg.get("model")
                if model:
                    models.add(str(model))
    except (OSError, UnicodeDecodeError):
        pass
    return {
        "input_tokens": total_input,
        "output_tokens": total_output,
        "total_tokens": total_input + total_output,
        "model": ", ".join(sorted(models)) if models else None,
    }


def collect_claude_history(days: int) -> List[Dict[str, Any]]:
    path = HOME / ".claude/history.jsonl"
    if not path.exists():
        return []
    cutoff_ms = int((_now() - dt.timedelta(days=days)).timestamp() * 1000)
    sessions: Dict[str, Dict[str, Any]] = {}

    active_session_ids = set()
    sessions_dir = HOME / ".claude/sessions"
    if sessions_dir.exists():
        for fpath in sessions_dir.glob("*.json"):
            try:
                sdata = json.loads(fpath.read_text(errors="ignore"))
                if sdata.get("status") in ("busy", "active", "running") and sdata.get("sessionId"):
                    active_session_ids.add(sdata["sessionId"])
            except (json.JSONDecodeError, OSError):
                continue

    try:
        with path.open(errors="ignore") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ts = obj.get("timestamp")
                if not ts or ts < cutoff_ms:
                    continue
                sid = obj.get("sessionId")
                if not sid:
                    continue
                cwd = obj.get("project")
                display = obj.get("display") or "Claude Code request"
                if sid not in sessions:
                    sessions[sid] = {
                        "agent": "Claude Code",
                        "source": "history.jsonl",
                        "session_id": sid,
                        "project": project_from_cwd(cwd),
                        "project_path": cwd,
                        "task": display,
                        "status": "recorded",
                        "min_ts": ts,
                        "max_ts": ts,
                        "message_count": 0,
                    }
                else:
                    sess = sessions[sid]
                    sess["min_ts"] = min(sess["min_ts"], ts)
                    sess["max_ts"] = max(sess["max_ts"], ts)
                    if cwd and not sess["project_path"]:
                        sess["project_path"] = cwd
                        sess["project"] = project_from_cwd(cwd)
                sessions[sid]["message_count"] += 1
    except Exception:
        return []

    rows = []
    for sid, sess in sessions.items():
        started = _iso_from_ms(sess["min_ts"])
        ended = _iso_from_ms(sess["max_ts"])
        latest_dt = _parse_iso(ended)
        status = "active" if sid in active_session_ids else ("recent" if latest_dt and (_now() - latest_dt) <= dt.timedelta(minutes=30) else "recorded")

        # 从 session JSONL 提取 token 用量和模型
        input_tokens = 0
        output_tokens = 0
        total_tokens = 0
        model = None
        token_status = "not_available"
        proj_dir = _claude_project_dir(sess["project_path"])
        if proj_dir:
            session_jsonl = proj_dir / f"{sid}.jsonl"
            if session_jsonl.exists():
                usage = _claude_session_usage(session_jsonl)
                input_tokens = usage["input_tokens"]
                output_tokens = usage["output_tokens"]
                total_tokens = usage["total_tokens"]
                model = usage["model"]
                if total_tokens > 0:
                    token_status = "claude_session_jsonl"

        rows.append(
            {
                "agent": "Claude Code",
                "source": "history.jsonl+session",
                "session_id": sid,
                "project": sess["project"],
                "project_path": sess["project_path"],
                "task": _shorten(sess["task"], 140),
                "status": status,
                "started_at": started,
                "ended_at": ended,
                "model": model,
                "provider": "anthropic-compatible",
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "token_status": token_status,
                "estimated_cost_usd": None,
                "cost_status": "usage_only_no_price_table" if total_tokens > 0 else "no_token_or_cost_in_cache",
                "message_count": sess["message_count"],
                "tool_call_count": 0,
                "confidence": "parsed_local_jsonl",
                "raw_path": str(path),
            }
        )
    return rows


def _openclaw_session_path(value: Optional[str]) -> Optional[pathlib.Path]:
    if not value:
        return None
    path = pathlib.Path(value).expanduser()
    if path.is_absolute():
        return path
    return HOME / ".openclaw" / path


def _openclaw_session_cwd(session_file: Optional[str]) -> Optional[str]:
    path = _openclaw_session_path(session_file)
    if not path or not path.exists():
        return None
    try:
        with path.open(errors="ignore") as f:
            for _ in range(40):
                line = f.readline()
                if not line:
                    break
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                cwd = obj.get("cwd") or (obj.get("session") or {}).get("cwd")
                if cwd:
                    return cwd
    except json.JSONDecodeError:
        return None
    return None


def _collect_openclaw_session_index(days: int) -> List[Dict[str, Any]]:
    path = HOME / ".openclaw/agents/main/sessions/sessions.json"
    if not path.exists():
        return []
    cutoff = _now() - dt.timedelta(days=days)
    try:
        raw = json.loads(path.read_text(errors="ignore"))
    except json.JSONDecodeError:
        return []
    entries = raw.values() if isinstance(raw, dict) else raw
    rows: List[Dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        started_at = _iso_from_ms(entry.get("startedAt") or entry.get("createdAt"))
        latest_at = _iso_from_ms(entry.get("endedAt") or entry.get("updatedAt") or entry.get("lastEventAt") or entry.get("lastUpdatedAt"))
        effective_ts = latest_at or started_at
        if not _within_window(effective_ts, cutoff):
            continue
        session_file = entry.get("sessionFile") or entry.get("path")
        cwd = entry.get("cwd") or entry.get("projectPath") or _openclaw_session_cwd(session_file)
        input_tokens = _safe_int(entry.get("inputTokens") or entry.get("input_tokens"))
        output_tokens = _safe_int(entry.get("outputTokens") or entry.get("output_tokens"))
        cache_read = _safe_int(entry.get("cacheRead") or entry.get("cacheReadTokens") or entry.get("cache_read_tokens"))
        cache_write = _safe_int(entry.get("cacheWrite") or entry.get("cacheWriteTokens") or entry.get("cache_write_tokens"))
        total_tokens = _safe_int(entry.get("totalTokens") or entry.get("total_tokens"))
        if not total_tokens:
            total_tokens = input_tokens + output_tokens + cache_read + cache_write
        cost_value = entry.get("estimatedCostUsd")
        if cost_value is None:
            cost_value = entry.get("estimated_cost_usd")
        latest_dt = _parse_iso(effective_ts)
        ended_at = _iso_from_ms(entry.get("endedAt"))
        status = entry.get("status")
        if not status:
            status = "ended" if ended_at else ("recent" if latest_dt and (_now() - latest_dt) <= dt.timedelta(minutes=30) else "recorded")
        rows.append(
            {
                "agent": "OpenClaw",
                "source": "openclaw-session",
                "session_id": entry.get("sessionId") or entry.get("id") or entry.get("key") or entry.get("sessionKey") or path.stem,
                "project": project_from_cwd(cwd),
                "project_path": cwd,
                "task": _safe_title(entry.get("title") or entry.get("label") or entry.get("task"), "OpenClaw session"),
                "status": status,
                "started_at": started_at or effective_ts,
                "ended_at": ended_at or latest_at,
                "model": entry.get("model"),
                "provider": entry.get("modelProvider") or entry.get("provider"),
                "input_tokens": input_tokens + cache_read,
                "output_tokens": output_tokens + cache_write,
                "total_tokens": total_tokens,
                "token_status": "openclaw_session_index" if total_tokens > 0 else "unknown",
                "estimated_cost_usd": _safe_float(cost_value),
                "cost_status": "openclaw_estimate" if cost_value is not None else "unknown",
                "message_count": _safe_int(entry.get("messageCount") or entry.get("messages")),
                "tool_call_count": _safe_int(entry.get("toolCallCount") or entry.get("toolCalls")),
                "confidence": "parsed_local_index",
                "raw_path": str(_openclaw_session_path(session_file) or path),
            }
        )
    return rows


def _collect_openclaw_task_runs(days: int) -> List[Dict[str, Any]]:
    db = HOME / ".openclaw/tasks/runs.sqlite"
    if not db.exists():
        return []
    cutoff_ms = int((_now() - dt.timedelta(days=days)).timestamp() * 1000)
    query = """
    select
      task_id, runtime, task_kind, source_id, owner_key, scope_kind, child_session_key,
      agent_id, run_id, label, task, status, delivery_status,
      created_at, started_at, ended_at, last_event_at, error,
      progress_summary, terminal_summary, terminal_outcome
    from task_runs
    where coalesce(last_event_at, started_at, created_at) >= ?
    order by coalesce(last_event_at, started_at, created_at) desc
    """
    rows: List[Dict[str, Any]] = []
    try:
        con = sqlite3.connect(db)
        con.row_factory = sqlite3.Row
        for row in con.execute(query, (cutoff_ms,)):
            latest_at = _iso_from_ms(row["last_event_at"] or row["ended_at"] or row["started_at"] or row["created_at"])
            task_text = row["task"] or row["label"] or row["progress_summary"] or "OpenClaw task"
            if row["progress_summary"]:
                task_text = f"{task_text} · {row['progress_summary']}"
            rows.append(
                {
                    "agent": "OpenClaw",
                    "source": "openclaw-task",
                    "session_id": row["child_session_key"] or row["run_id"] or row["task_id"],
                    "project": row["scope_kind"] or "openclaw",
                    "project_path": None,
                    "task": _shorten(task_text, 180),
                    "status": row["status"] or row["delivery_status"] or "recorded",
                    "started_at": _iso_from_ms(row["started_at"] or row["created_at"]),
                    "ended_at": _iso_from_ms(row["ended_at"]) or latest_at,
                    "model": None,
                    "provider": row["runtime"],
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "token_status": "status_only",
                    "estimated_cost_usd": None,
                    "cost_status": "task_status_only",
                    "message_count": 0,
                    "tool_call_count": 0,
                    "confidence": "task_status_only",
                    "raw_path": str(db),
                    "error": row["error"],
                    "terminal_outcome": row["terminal_outcome"],
                }
            )
    except Exception:
        return []
    finally:
        try:
            con.close()
        except sqlite3.Error:
            pass
    return rows


def collect_openclaw_sessions(days: int) -> List[Dict[str, Any]]:
    rows = _collect_openclaw_session_index(days)
    rows.extend(_collect_openclaw_task_runs(days))
    return rows


def _cursor_workspace_path(workspace_dir: pathlib.Path) -> Optional[str]:
    path = workspace_dir / "workspace.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(errors="ignore"))
    except sqlite3.Error:
        return None
    folder = data.get("folder")
    if folder:
        return _path_from_file_uri(folder)
    workspace = data.get("workspace")
    if workspace:
        return _path_from_file_uri(workspace)
    return None


def _sqlite_item_value(db: pathlib.Path, key: str) -> Optional[str]:
    try:
        con = sqlite3.connect(db)
        row = con.execute("select value from ItemTable where key = ?", (key,)).fetchone()
        return row[0] if row else None
    except sqlite3.Error:
        return None
    finally:
        try:
            con.close()
        except sqlite3.Error:
            pass


def collect_cursor_sessions(days: int) -> List[Dict[str, Any]]:
    root = HOME / "Library/Application Support/Cursor/User/workspaceStorage"
    if not root.exists():
        return []
    cutoff = _now() - dt.timedelta(days=days)
    rows: List[Dict[str, Any]] = []
    for db in sorted(root.glob("*/state.vscdb"), key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True):
        workspace_dir = db.parent
        workspace_path = _cursor_workspace_path(workspace_dir)
        raw = _sqlite_item_value(db, "composer.composerData")
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except sqlite3.Error:
            continue
        composers = data.get("allComposers") or []
        if not isinstance(composers, list):
            continue
        for composer in composers:
            if not isinstance(composer, dict):
                continue
            composer_id = composer.get("composerId")
            if not composer_id:
                continue
            started_at = _iso_from_ms(composer.get("createdAt"))
            latest_at = _iso_from_ms(composer.get("lastUpdatedAt") or composer.get("createdAt"))
            if not _within_window(latest_at or started_at, cutoff):
                continue
            if composer.get("isArchived"):
                status = "archived"
            elif composer.get("isDraft"):
                status = "draft"
            elif composer.get("hasBlockingPendingActions"):
                status = "pending_action"
            else:
                parsed_latest = _parse_iso(latest_at)
                status = "recent" if parsed_latest and (_now() - parsed_latest) <= dt.timedelta(minutes=30) else "recorded"
            name = composer.get("name") or composer.get("subtitle") or "Cursor composer"
            lines_added = _safe_int(composer.get("totalLinesAdded"))
            lines_removed = _safe_int(composer.get("totalLinesRemoved"))
            files_changed = _safe_int(composer.get("filesChangedCount"))
            detail_parts = []
            if lines_added or lines_removed:
                detail_parts.append(f"+{lines_added}/-{lines_removed} lines")
            if files_changed:
                detail_parts.append(f"{files_changed} files")
            task = _safe_title(name, "Cursor composer")
            if detail_parts:
                task = _shorten(f"{task} · {', '.join(detail_parts)}", 180)
            rows.append(
                {
                    "agent": "Cursor",
                    "source": "cursor-composer",
                    "session_id": composer_id,
                    "project": project_from_cwd(workspace_path),
                    "project_path": workspace_path,
                    "task": task,
                    "status": status,
                    "started_at": started_at or latest_at,
                    "ended_at": latest_at or started_at,
                    "model": None,
                    "provider": "cursor",
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "token_status": "not_available",
                    "estimated_cost_usd": None,
                    "cost_status": "not_available",
                    "message_count": 0,
                    "tool_call_count": 0,
                    "lines_added": lines_added,
                    "lines_removed": lines_removed,
                    "files_changed": files_changed,
                    "context_usage_percent": _safe_float(composer.get("contextUsagePercent")),
                    "confidence": "metadata_only",
                    "raw_path": str(db),
                }
            )
    return rows


def collect_litellm_usage(days: int) -> List[Dict[str, Any]]:
    env = os.environ.copy()
    env.update(load_env_file(PRIVATE_LITELLM_ENV))
    database_url = env.get("DATABASE_URL")
    # P2.3: 动态发现 psql 路径，不硬编码
    psql = shutil.which("psql")
    if not database_url or not psql:
        return []
    start = (_now() - dt.timedelta(days=days)).isoformat()
    # P2.3: 用 psql -v 传参，避免字符串拼接
    sql = """
    select
      coalesce(model, 'unknown') as model,
      count(*) as calls,
      coalesce(sum(total_tokens),0)::bigint as total_tokens,
      coalesce(sum(spend),0)::float as spend,
      max(startTime)::text as latest
    from "LiteLLM_SpendLogs"
    where startTime >= :'start_ts'::timestamptz
    group by model
    order by spend desc, total_tokens desc;
    """
    try:
        out = subprocess.check_output(
            [psql, database_url, "-Atc", sql, "-v", f"start_ts={start}"],
            text=True,
            stderr=subprocess.DEVNULL,
            env=env,
            timeout=10,
        )
    except (subprocess.SubprocessError, OSError):
        return []
    rows: List[Dict[str, Any]] = []
    for line in out.splitlines():
        parts = line.split("|")
        if len(parts) < 5:
            continue
        model, calls, total_tokens, spend, latest = parts[:5]
        rows.append(
            {
                "agent": "LiteLLM",
                "component_type": "infrastructure",
                "source": "postgres",
                "session_id": f"litellm-{model}",
                "project": "gateway-metered",
                "project_path": None,
                "task": f"LiteLLM metered traffic: {model}",
                "status": "aggregate",
                "started_at": latest,
                "ended_at": latest,
                "model": model,
                "provider": "litellm",
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": _safe_int(total_tokens),
                "token_status": "litellm_spend_logs" if _safe_int(total_tokens) > 0 else "unknown",
                "estimated_cost_usd": _safe_float(spend),
                "cost_status": "litellm_spend",
                "message_count": _safe_int(calls),
                "tool_call_count": 0,
                "confidence": "metered_proxy_db",
                "raw_path": "LiteLLM_SpendLogs",
            }
        )
    return rows


# ── P3.4: Trae / Antigravity IDE 采集器 ────────────────────────────────────

def _collect_vscode_like_ide(
    ide_name: str,
    app_support_dir: pathlib.Path,
    days: int,
) -> List[Dict[str, Any]]:
    """通用采集器：从 VS Code 架构 IDE 的 workspaceStorage 提取工作区 session 信息。"""
    if not app_support_dir.exists():
        return []
    ws_root = app_support_dir / "User" / "workspaceStorage"
    if not ws_root.exists():
        return []
    cutoff = _now() - dt.timedelta(days=days)
    rows: List[Dict[str, Any]] = []

    for ws_dir in ws_root.iterdir():
        if not ws_dir.is_dir():
            continue
        ws_json = ws_dir / "workspace.json"
        db_path = ws_dir / "state.vscdb"
        if not ws_json.exists():
            continue
        try:
            ws_data = json.loads(ws_json.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        folder = ws_data.get("folder", "")
        if not folder:
            continue
        from urllib.parse import unquote as _unquote, urlparse as _urlparse
        if folder.startswith("file://"):
            folder = _unquote(_urlparse(folder).path)
        project = pathlib.Path(folder).name if folder else "unknown"

        # 获取最新修改时间作为活跃时间
        latest_ts = None
        try:
            latest_ts = max(
                f.stat().st_mtime for f in ws_dir.iterdir() if f.is_file()
            )
        except (OSError, ValueError):
            continue
        if latest_ts is None:
            continue

        latest_dt = dt.datetime.fromtimestamp(latest_ts, dt.timezone.utc)
        if latest_dt < cutoff:
            continue

        # 尝试读取模型和 session 元数据
        model = None
        mode = None
        if db_path.exists():
            try:
                con = sqlite3.connect(str(db_path))
                cur = con.cursor()
                # 提取选中的 AI 模型
                row = cur.execute(
                    "SELECT value FROM ItemTable WHERE key LIKE '%AI.agent.model.selected_model%' LIMIT 1"
                ).fetchone()
                if row:
                    try:
                        model_data = json.loads(row[0])
                        model = model_data if isinstance(model_data, str) else str(model_data)
                    except (json.JSONDecodeError, TypeError):
                        model = str(row[0])[:60] if row[0] else None
                # 提取 agent 模式
                row = cur.execute(
                    "SELECT value FROM ItemTable WHERE key LIKE '%AI.agent.mode' LIMIT 1"
                ).fetchone()
                if row:
                    try:
                        mode = json.loads(row[0]) if isinstance(row[0], str) else str(row[0])
                    except (json.JSONDecodeError, TypeError):
                        mode = None
                con.close()
            except sqlite3.Error:
                pass

        rows.append({
            "agent": ide_name,
            "source": "workspaceStorage",
            "session_id": ws_dir.name,
            "project": project,
            "project_path": folder,
            "task": f"{ide_name} workspace: {project}",
            "status": "active" if (time.time() - latest_ts) < 86400 else "recent",
            "started_at": _iso_from_epoch(latest_ts),
            "ended_at": _iso_from_epoch(latest_ts),
            "model": model or "unknown",
            "provider": ide_name.lower(),
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "token_status": "pending_schema_mapping",
            "estimated_cost_usd": None,
            "cost_status": "not_available",
            "message_count": 0,
            "tool_call_count": 0,
            "confidence": "workspace_metadata",
            "raw_path": str(ws_dir),
            "mode": mode,
        })
    return rows


def _clean_trae_model_name(raw: Optional[str]) -> Optional[str]:
    """Strip Trae's sort-order prefix from model names.

    Trae stores models as '1_-_gpt-5', '1_-_gemini-3-pro', etc.
    The 'N_-_' prefix is a sort-order artifact, not part of the model name.
    """
    if not raw:
        return None
    cleaned = re.sub(r"^\d+_-_", "", raw)
    return cleaned if cleaned else raw


def _trae_snapshot_turns(snapshot_root: pathlib.Path, session_id: str) -> Dict[str, Any]:
    """Count chat turns from git snapshot tags for a Trae session.

    Returns dict with: turns, started_at, ended_at, raw_path.
    """
    v2_tags = snapshot_root / session_id / "v2" / ".git" / "refs" / "tags"
    if not v2_tags.is_dir():
        return {
            "turns": 0,
            "started_at": None,
            "ended_at": None,
            "raw_path": str(snapshot_root / session_id),
        }

    before_tags = sorted(v2_tags.glob("before-chat-turn-*"))
    turns = len(before_tags)

    started_ts = None
    ended_ts = None
    if before_tags:
        try:
            mtimes = [f.stat().st_mtime for f in before_tags]
            started_ts = min(mtimes)
            ended_ts = max(mtimes)
        except OSError:
            pass

    return {
        "turns": turns,
        "started_at": _iso_from_epoch(started_ts),
        "ended_at": _iso_from_epoch(ended_ts),
        "raw_path": str(v2_tags),
    }


def collect_trae_sessions(days: int) -> List[Dict[str, Any]]:
    """P6: 采集 Trae IDE session 数据，基于 snapshot turn 计数估算 token。"""
    TRAE_PATHS = [
        (pathlib.Path.home() / "Library" / "Application Support" / "Trae", "Trae"),
        (pathlib.Path.home() / "Library" / "Application Support" / "TRAE SOLO", "TRAE SOLO"),
    ]

    cutoff = _now() - dt.timedelta(days=days)
    rows: List[Dict[str, Any]] = []

    for app_dir, ide_name in TRAE_PATHS:
        if not app_dir.exists():
            continue

        ws_root = app_dir / "User" / "workspaceStorage"
        snapshot_root = app_dir / "ModularData" / "ai-agent" / "snapshot"

        if not ws_root.exists():
            continue

        # --- Phase 1: 从 workspaceStorage 提取 session 元数据 ---
        # session_id → {agent_type, model, project, project_path, workspace_dir}
        session_meta: Dict[str, Dict[str, Any]] = {}

        for ws_dir in ws_root.iterdir():
            if not ws_dir.is_dir():
                continue
            db_path = ws_dir / "state.vscdb"
            ws_json = ws_dir / "workspace.json"

            # 读取 workspace 项目路径
            folder = None
            if ws_json.exists():
                try:
                    ws_data = json.loads(ws_json.read_text(encoding="utf-8"))
                    folder = ws_data.get("folder", "")
                    if folder.startswith("file://"):
                        folder = unquote(urlparse(folder).path)
                except (json.JSONDecodeError, OSError):
                    pass
            project = pathlib.Path(folder).name if folder else "unknown"

            # 从 state.vscdb 读取 session → agent_type 映射
            if not db_path.exists():
                continue
            try:
                con = sqlite3.connect(str(db_path))
                cur = con.cursor()

                # icube_session_agent_map: {"session_id": "agent_type", ...}
                row = cur.execute(
                    "SELECT value FROM ItemTable WHERE key = 'icube_session_agent_map'"
                ).fetchone()
                if row:
                    try:
                        agent_map = json.loads(row[0])
                        for sid, agent_type in agent_map.items():
                            session_meta[sid] = {
                                "agent_type": agent_type,
                                "model": None,
                                "project": project,
                                "project_path": folder,
                                "workspace_dir": ws_dir,
                            }
                    except json.JSONDecodeError:
                        pass

                # *_ai-chat:sessionRelation:modelMap → session → {agent_type: model}
                model_rows = cur.execute(
                    "SELECT value FROM ItemTable WHERE key LIKE '%sessionRelation:modelMap'"
                ).fetchall()
                for mr in model_rows:
                    try:
                        model_map = json.loads(mr[0])
                        for sid, models_by_agent in model_map.items():
                            if sid in session_meta and isinstance(models_by_agent, dict):
                                a_type = session_meta[sid]["agent_type"]
                                raw_model = models_by_agent.get(a_type)
                                session_meta[sid]["model"] = _clean_trae_model_name(raw_model)
                    except json.JSONDecodeError:
                        pass

                con.close()
            except sqlite3.Error:
                pass

        # --- Phase 2: 从 snapshot 目录提取 turn 计数 ---
        snap_sessions: Dict[str, Dict[str, Any]] = {}
        if snapshot_root.exists():
            for snap_dir in snapshot_root.iterdir():
                if not snap_dir.is_dir():
                    continue
                sid = snap_dir.name
                turn_info = _trae_snapshot_turns(snapshot_root, sid)
                snap_sessions[sid] = turn_info

        # --- Phase 3: 合并数据源，生成行 ---
        # 以所有已发现的 session ID 为并集
        all_sids = set(session_meta.keys()) | set(snap_sessions.keys())

        for sid in all_sids:
            meta = session_meta.get(sid, {})
            snap = snap_sessions.get(sid, {"turns": 0, "started_at": None, "ended_at": None, "raw_path": None})

            turns = snap["turns"]
            agent_type = meta.get("agent_type", "unknown")
            model = meta.get("model")
            project = meta.get("project", "unknown")
            project_path = meta.get("project_path")
            workspace_dir = meta.get("workspace_dir")

            # 时间戳: 优先用 snapshot tag mtime，fallback 到 workspace 目录 mtime
            started_at = snap.get("started_at")
            ended_at = snap.get("ended_at")
            if not ended_at and workspace_dir:
                try:
                    ws_mtime = max(
                        f.stat().st_mtime for f in workspace_dir.iterdir() if f.is_file()
                    )
                    started_at = _iso_from_epoch(ws_mtime)
                    ended_at = started_at
                except (OSError, ValueError):
                    continue

            # 时间窗口过滤
            ended_dt = _parse_iso(ended_at) if ended_at else None
            if not ended_dt:
                continue
            if ended_dt < cutoff:
                started_dt = _parse_iso(started_at) if started_at else None
                if not started_dt or started_dt < cutoff:
                    continue

            # Phase 4: Token 估算
            input_tokens = turns * TRAE_INPUT_TOKENS_PER_TURN
            output_tokens = turns * TRAE_OUTPUT_TOKENS_PER_TURN
            total_tokens = input_tokens + output_tokens

            if turns > 0:
                token_status = "estimated_from_turn_count"
                cost_status = "usage_only_no_price_table"
            else:
                token_status = "pending_schema_mapping"
                cost_status = "not_available"

            # Task 描述
            task_parts = [f"{ide_name} {agent_type}"]
            if turns > 0:
                task_parts.append(f"{turns} turns")
            if model:
                task_parts.append(model)
            task = _shorten(" - ".join(task_parts), 140)

            # 状态
            if (_now() - ended_dt) <= dt.timedelta(hours=24):
                status = "active"
            elif (_now() - ended_dt) <= dt.timedelta(days=7):
                status = "recent"
            else:
                status = "recorded"

            rows.append({
                "agent": ide_name,
                "source": "snapshot+workspaceStorage",
                "session_id": sid,
                "project": project,
                "project_path": project_path,
                "task": task,
                "status": status,
                "started_at": started_at,
                "ended_at": ended_at,
                "model": model or "unknown",
                "provider": ide_name.lower().replace(" ", "-"),
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "token_status": token_status,
                "estimated_cost_usd": None,
                "cost_status": cost_status,
                "message_count": turns,
                "tool_call_count": 0,
                "confidence": "turn_count_estimation" if turns > 0 else "workspace_metadata",
                "raw_path": snap.get("raw_path") or (str(workspace_dir) if workspace_dir else ""),
            })

    return rows


def _antigravity_cloudcode_stats(days: int) -> Dict[str, Any]:
    """从 Antigravity IDE 的 cloudcode.log 统计 API 调用次数和估算 token。"""
    base = pathlib.Path.home() / "Library" / "Application Support"
    ag_dir = base / "Antigravity IDE"
    if not ag_dir.exists():
        ag_dir = base / "Antigravity"
    logs_dir = ag_dir / "logs"
    if not logs_dir.exists():
        return {"api_calls": 0, "estimated_tokens": 0}
    cutoff = _now() - dt.timedelta(days=days)
    api_calls = 0
    latest_ts = None
    daily_heartbeats: Dict[str, int] = {}
    for log_dir in logs_dir.iterdir():
        if not log_dir.is_dir():
            continue
        cc_log = log_dir / "cloudcode.log"
        if not cc_log.exists():
            continue
        try:
            mtime = dt.datetime.fromtimestamp(cc_log.stat().st_mtime, dt.timezone.utc)
            if mtime < cutoff:
                continue
            with cc_log.open(errors="ignore") as f:
                for line in f:
                    if "loadCodeAssist" in line or "fetchAvailableModels" in line:
                        api_calls += 1
                        # 提取日期
                        import re
                        m = re.match(r"(\d{4}-\d{2}-\d{2})", line)
                        if m:
                            daily_heartbeats[m.group(1)] = daily_heartbeats.get(m.group(1), 0) + 1
            if latest_ts is None or mtime > latest_ts:
                latest_ts = mtime
        except (OSError, UnicodeDecodeError):
            continue

    # 估算 token：中等估算 = 2次补全/分钟 × 800 avg tokens × 在线小时数
    estimated_tokens = 0
    for date_str, heartbeats in daily_heartbeats.items():
        hours_online = heartbeats * 5 / 60  # 每5分钟一次心跳
        estimated_tokens += int(2 * 60 * hours_online * 800)

    return {
        "api_calls": api_calls,
        "latest_activity": _iso_from_epoch(latest_ts.timestamp()) if latest_ts else None,
        "estimated_tokens": estimated_tokens,
        "days_active": len(daily_heartbeats),
    }


def collect_antigravity_sessions(days: int) -> List[Dict[str, Any]]:
    """P3.4: 采集 Antigravity IDE 工作区 session 数据 + CloudCode API 活跃度。"""
    base = pathlib.Path.home() / "Library" / "Application Support"
    ag_dir = base / "Antigravity IDE"
    if not ag_dir.exists():
        ag_dir = base / "Antigravity"
    rows = _collect_vscode_like_ide("Antigravity", ag_dir, days)
    # 补充 CloudCode API 活跃度统计 + token 估算
    cc_stats = _antigravity_cloudcode_stats(days)
    if cc_stats["api_calls"] > 0:
        est_tokens = cc_stats["estimated_tokens"]
        rows.append({
            "agent": "Antigravity",
            "source": "cloudcode.log",
            "session_id": "cloudcode-usage",
            "project": "CloudCode API",
            "project_path": None,
            "task": f"Antigravity CloudCode {cc_stats['api_calls']} calls, ~{cc_stats['days_active']}d active",
            "status": "active",
            "started_at": cc_stats.get("latest_activity"),
            "ended_at": cc_stats.get("latest_activity"),
            "model": "gemini (estimated)",
            "provider": "google",
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": est_tokens,
            "token_status": "estimated_from_heartbeat",
            "estimated_cost_usd": None,
            "cost_status": "google_cloud_billing",
            "message_count": cc_stats["api_calls"],
            "tool_call_count": 0,
            "confidence": "heartbeat_estimated",
            "raw_path": str(ag_dir / "logs"),
        })
    return rows


__all__ = [n for n in dir() if not n.startswith("__")]
