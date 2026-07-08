#!/usr/bin/env python3
import datetime as dt
import glob
import json
import logging
import os
import time
import pathlib
import re
import shutil
import sqlite3
import subprocess
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import unquote, urlparse

from project_attribution import normalize_project_name, project_from_cwd
from utils import epoch_from_iso as _epoch_from_iso, estimate_cost_usd as _estimate_cost_usd, iso_from_epoch as _iso_from_epoch, iso_from_ms as _iso_from_ms, load_env_file, load_model_pricing as _load_model_pricing, parse_iso as _parse_iso, safe_float as _safe_float, safe_int as _safe_int, utc_now as _now

log = logging.getLogger("agent_ledger")


HOME = pathlib.Path.home()
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent
DATA_DIR = pathlib.Path(os.getenv("SMART_GATEWAY_DATA_DIR", PROJECT_ROOT / "data"))
GATEWAY_EVENT_LOG = DATA_DIR / "agent-events.jsonl"
PRIVATE_LITELLM_ENV = HOME / ".config/smart-agent-ledger/litellm.env"
INFRASTRUCTURE_COMPONENTS = {"LiteLLM"}
# P1.2: 日志轮转阈值 (50MB)
LOG_ROTATE_MAX_BYTES = 50 * 1024 * 1024
# P6: Trae turn-based token 估算常量
TRAE_INPUT_TOKENS_PER_TURN = 2000
TRAE_OUTPUT_TOKENS_PER_TURN = 1000


def _shorten(value: Any, limit: int = 120) -> str:
    text = "" if value is None else str(value)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _strip_environment_context(text: str) -> str:
    text = re.sub(r"<environment_context>.*?</environment_context>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]{1,40}>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _content_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                parts.append(str(item.get("text") or item.get("content") or ""))
            else:
                parts.append(str(item))
        return " ".join(parts)
    if isinstance(content, dict):
        return str(content.get("text") or content.get("content") or "")
    return "" if content is None else str(content)


def _safe_title(value: Any, fallback: str) -> str:
    text = _content_text(value)
    if text.lstrip().lower().startswith("<think>"):
        return fallback
    text = _strip_environment_context(text)
    return _shorten(text, 140) or fallback


def _within_window(iso_value: Optional[str], cutoff: dt.datetime) -> bool:
    parsed = _parse_iso(iso_value)
    return bool(parsed and parsed >= cutoff)


def _latest_mtime_iso(paths: Iterable[pathlib.Path]) -> Optional[str]:
    latest = None
    for path in paths:
        try:
            if path.exists():
                latest = max(latest or path.stat().st_mtime, path.stat().st_mtime)
        except OSError:
            continue
    return _iso_from_epoch(latest)


def _path_exists_any(paths: Iterable[pathlib.Path]) -> bool:
    return any(path.exists() for path in paths)


UNKNOWN_COST_STATUSES = {
    "unknown",
    "local_token_estimate_only",
    "no_token_or_cost_in_cache",
    "task_status_only",
    "not_available",
    "no_cost_source",
}


def _cost_is_known(row: Dict[str, Any]) -> bool:
    cost = _safe_float(row.get("actual_cost_usd"))
    if cost is not None:
        return True
    cost = _safe_float(row.get("estimated_cost_usd"))
    if cost is None:
        return False
    return str(row.get("cost_status") or "unknown") not in UNKNOWN_COST_STATUSES


def _row_cost(row: Dict[str, Any]) -> Optional[float]:
    if not _cost_is_known(row):
        return None
    actual = _safe_float(row.get("actual_cost_usd"))
    if actual is not None:
        return actual
    return _safe_float(row.get("estimated_cost_usd"))


def _estimate_missing_costs(rows: List[Dict[str, Any]], pricing: Dict[str, Any]) -> None:
    """后处理：对有 token 但无费用的行，根据单价表填充 estimated_cost_usd。

    规则：
    - 已有费用（actual_cost_usd 或已知 estimated_cost_usd）的行不覆盖
    - 必须有 model 字段且能匹配到单价
    - 必须有 total_tokens > 0
    - 逗号分隔的多模型（如 "claude-sonnet-4, claude-opus-4"）取第一个模型估算
    """
    if not pricing.get("models"):
        return
    for row in rows:
        if _cost_is_known(row):
            continue
        if _safe_int(row.get("total_tokens")) <= 0:
            continue
        raw_model = row.get("model")
        if not raw_model or not str(raw_model).strip():
            continue
        # 处理多模型字符串（Claude Code 可能返回 "claude-sonnet-4, claude-opus-4"）
        # 跳过 <synthetic> 等非标准名称，取第一个有效模型
        model_str = None
        for part in str(raw_model).split(","):
            candidate = part.strip()
            if candidate and candidate not in {"unknown", "openai", "synthetic"} and not candidate.startswith("<"):
                model_str = candidate
                break
        if not model_str:
            continue
        input_tokens = _safe_int(row.get("input_tokens"))
        output_tokens = _safe_int(row.get("output_tokens"))
        # 如果没有单独的 input/output，按 6:4 比例拆分 total_tokens
        if input_tokens == 0 and output_tokens == 0:
            total = _safe_int(row.get("total_tokens"))
            input_tokens = int(total * 0.6)
            output_tokens = total - input_tokens
        cost = _estimate_cost_usd(model_str, input_tokens, output_tokens, pricing)
        if cost is not None:
            row["estimated_cost_usd"] = cost
            row["cost_status"] = "pricing_table_estimate"


def _tokens_are_known(row: Dict[str, Any]) -> bool:
    if str(row.get("token_status") or "") in {
        "not_available",
        "unknown",
        "status_only",
        "pending_schema_mapping",
        "server_side_only",
    }:
        return False
    return _safe_int(row.get("total_tokens")) > 0


def _is_agent_row(row: Dict[str, Any]) -> bool:
    return (row.get("agent") or "") not in INFRASTRUCTURE_COMPONENTS


def _path_from_file_uri(value: Any) -> Optional[str]:
    if not value:
        return None
    text = str(value)
    if text.startswith("file://"):
        parsed = urlparse(text)
        return unquote(parsed.path)
    return text


def _cleanup_old_event_logs(max_age_days: int = 90) -> None:
    """P8.3: 删除超过 max_age_days 天的旧轮转事件日志文件。"""
    try:
        cutoff = (_now() - dt.timedelta(days=max_age_days)).timestamp()
        for f in DATA_DIR.glob("agent-events.*.jsonl"):
            if f.stat().st_mtime < cutoff:
                f.unlink()
                log.info("已清理旧事件日志: %s", f.name)
    except OSError:
        pass


def record_gateway_event(event: Dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    # P1.2: 超过阈值时轮转日志文件
    try:
        if GATEWAY_EVENT_LOG.exists() and GATEWAY_EVENT_LOG.stat().st_size > LOG_ROTATE_MAX_BYTES:
            date_str = _now().strftime("%Y%m%d")
            rotated = DATA_DIR / f"agent-events.{date_str}.jsonl"
            # 如果同一天已有轮转文件，追加序号
            if rotated.exists():
                idx = 1
                while (DATA_DIR / f"agent-events.{date_str}.{idx}.jsonl").exists():
                    idx += 1
                rotated = DATA_DIR / f"agent-events.{date_str}.{idx}.jsonl"
            GATEWAY_EVENT_LOG.rename(rotated)
            # P8.3: 清理 >90 天的旧轮转文件
            _cleanup_old_event_logs()
    except OSError:
        pass  # 轮转失败不应阻塞事件写入
    clean = {k: v for k, v in event.items() if v is not None}
    clean.setdefault("timestamp", _now().isoformat())
    with GATEWAY_EVENT_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(clean, ensure_ascii=False, sort_keys=True) + "\n")


def _gateway_event_files() -> List[pathlib.Path]:
    """返回当前日志文件和所有轮转文件（按修改时间倒序）。"""
    files = []
    if GATEWAY_EVENT_LOG.exists():
        files.append(GATEWAY_EVENT_LOG)
    for rotated in sorted(DATA_DIR.glob("agent-events.*.jsonl"), key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True):
        files.append(rotated)
    return files


__all__ = [n for n in dir() if not n.startswith("__")]
