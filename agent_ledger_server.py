#!/usr/bin/env python3
"""Read-only agent ledger service for collector-only Macs."""
import asyncio
import copy
import datetime as dt
import json
import os
import pathlib
import time
from contextlib import suppress
from typing import Any, Dict, Optional

from fastapi import FastAPI

from agent_ledger import build_agent_ledger
from utils import safe_int as _safe_int, safe_read_json, utc_now as _now


app = FastAPI(title="Smart LLM Agent Ledger Read-only")

READONLY_LEDGER_CACHE_TTL_SECONDS = _safe_int(os.getenv("AGENT_LEDGER_READONLY_CACHE_TTL_SECONDS"), 60)
READONLY_LEDGER_FIRST_RESPONSE_TIMEOUT_SECONDS = float(
    os.getenv("AGENT_LEDGER_READONLY_FIRST_RESPONSE_TIMEOUT_SECONDS") or "6"
)
READONLY_LEDGER_DISK_CACHE_DIR = pathlib.Path(
    os.getenv("AGENT_LEDGER_READONLY_CACHE_DIR")
    or pathlib.Path.home() / "Library/Caches/Smart Agent Ledger/agent-ledger-readonly"
)
READONLY_LEDGER_CACHE: Dict[tuple, Dict[str, Any]] = {}
READONLY_LEDGER_TASKS: Dict[tuple, asyncio.Task] = {}


def _bounded_int(value: Any, default: int, minimum: int, maximum: int) -> int:
    parsed = _safe_int(value, default)
    if parsed <= 0:
        parsed = default
    return max(minimum, min(parsed, maximum))


def _cache_path(days: int, limit: int) -> pathlib.Path:
    return READONLY_LEDGER_DISK_CACHE_DIR / f"agent-ledger-{days}d-{limit}.json"


def _empty_agent_ledger(days: int, limit: int) -> Dict[str, Any]:
    return {
        "generated_at": _now().isoformat(),
        "service": "agent-ledger-readonly",
        "window_days": days,
        "totals": {
            "sessions": 0,
            "agents": 0,
            "projects": 0,
            "known_token_sessions": 0,
            "total_tokens": 0,
        },
        "recent_sessions": [],
        "_requested_limit": limit,
        "_refreshing": True,
    }


def _cache_agent_ledger_data(cache_key: tuple, data: Dict[str, Any]) -> None:
    payload = copy.deepcopy(data)
    payload.setdefault("service", "agent-ledger-readonly")
    payload.setdefault("window_days", cache_key[0])
    entry = {"ts": time.time(), "data": payload}
    READONLY_LEDGER_CACHE[cache_key] = entry
    with suppress(OSError, TypeError):
        READONLY_LEDGER_DISK_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        disk_payload = {"cached_at": _now().isoformat(), "data": payload}
        tmp = _cache_path(*cache_key).with_suffix(".json.tmp")
        tmp.write_text(json.dumps(disk_payload, ensure_ascii=False), encoding="utf-8")
        tmp.replace(_cache_path(*cache_key))


def _disk_cache_entry(cache_key: tuple) -> Optional[Dict[str, Any]]:
    payload = safe_read_json(_cache_path(*cache_key), default=None)
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), dict):
        return None
    cached_at = payload.get("cached_at")
    cached_ts = None
    if isinstance(cached_at, str):
        with suppress(ValueError):
            cached_ts = dt.datetime.fromisoformat(cached_at).timestamp()
    return {"ts": cached_ts or 0, "data": payload["data"]}


def _cache_entry(cache_key: tuple) -> Optional[Dict[str, Any]]:
    return READONLY_LEDGER_CACHE.get(cache_key) or _disk_cache_entry(cache_key)


def _decorate_response(
    data: Dict[str, Any],
    cache_key: tuple,
    *,
    cache_ts: Optional[float] = None,
    stale: bool = False,
    refreshing: bool = False,
    error: Optional[str] = None,
) -> Dict[str, Any]:
    result = copy.deepcopy(data)
    result.setdefault("service", "agent-ledger-readonly")
    result.setdefault("window_days", cache_key[0])
    result.setdefault("recent_sessions", [])
    result.setdefault("totals", {})
    if cache_ts is not None:
        result["_cache_age_seconds"] = max(0, int(time.time() - cache_ts))
    if stale:
        result["_stale"] = True
        result["_ledger_cache_fallback"] = True
        result["_ledger_cache_status"] = "stale_readonly"
    if refreshing:
        result["_refreshing"] = True
    if error:
        result["_last_refresh_failed"] = True
        result["_ledger_cache_issue"] = error
    return result


async def _finish_task(cache_key: tuple, task: asyncio.Task) -> Dict[str, Any]:
    try:
        data = await task
    finally:
        READONLY_LEDGER_TASKS.pop(cache_key, None)
    if isinstance(data, dict):
        _cache_agent_ledger_data(cache_key, data)
        return _decorate_response(data, cache_key)
    return _empty_agent_ledger(*cache_key)


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "service": "agent-ledger-readonly",
        "ts": _now().isoformat(),
    }


@app.get("/agent-ledger")
async def agent_ledger(days: int = 90, limit: int = 1000) -> Dict[str, Any]:
    safe_days = _bounded_int(days, 90, 1, 3660)
    safe_limit = _bounded_int(limit, 1000, 1, 2000)
    cache_key = (safe_days, safe_limit)
    cached = _cache_entry(cache_key)
    if cached and time.time() - cached["ts"] < READONLY_LEDGER_CACHE_TTL_SECONDS:
        return _decorate_response(cached["data"], cache_key, cache_ts=cached["ts"])

    task = READONLY_LEDGER_TASKS.get(cache_key)
    if task is not None and task.done():
        return await _finish_task(cache_key, task)
    if task is None:
        task = asyncio.create_task(asyncio.to_thread(build_agent_ledger, days=safe_days, limit=safe_limit))
        READONLY_LEDGER_TASKS[cache_key] = task

    try:
        data = await asyncio.wait_for(
            asyncio.shield(task),
            timeout=READONLY_LEDGER_FIRST_RESPONSE_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        if cached:
            return _decorate_response(
                cached["data"],
                cache_key,
                cache_ts=cached["ts"],
                stale=True,
                refreshing=True,
            )
        return _decorate_response(_empty_agent_ledger(safe_days, safe_limit), cache_key, stale=True, refreshing=True)
    except Exception as exc:
        READONLY_LEDGER_TASKS.pop(cache_key, None)
        if cached:
            return _decorate_response(
                cached["data"],
                cache_key,
                cache_ts=cached["ts"],
                stale=True,
                refreshing=False,
                error=str(exc),
            )
        return _decorate_response(_empty_agent_ledger(safe_days, safe_limit), cache_key, error=str(exc))

    READONLY_LEDGER_TASKS.pop(cache_key, None)
    if isinstance(data, dict):
        _cache_agent_ledger_data(cache_key, data)
        return _decorate_response(data, cache_key)
    return _empty_agent_ledger(safe_days, safe_limit)
