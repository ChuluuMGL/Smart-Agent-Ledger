"""公共工具函数 — 消除 agent_ledger / fleet_ledger / gateway 等模块中的重复定义。"""
import datetime as dt
import json
import pathlib
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple


def safe_read_json(path: Any, default: Any = None, encoding: str = "utf-8") -> Any:
    """安全读取 JSON 文件，解析失败返回 default。"""
    try:
        p = pathlib.Path(path)
        return json.loads(p.read_text(encoding=encoding, errors="ignore"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError, AttributeError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """安全转 int，None/空字符串/解析失败返回 default。"""
    try:
        if value is None or value == "":
            return default
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Any) -> Optional[float]:
    """安全转 float，None 或空字符串返回 None。"""
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def utc_now() -> dt.datetime:
    """返回当前 UTC 时间（带时区信息）。"""
    return dt.datetime.now(dt.timezone.utc)


def parse_iso(value: Optional[str]) -> Optional[dt.datetime]:
    """解析 ISO 格式时间字符串，失败返回 None。"""
    if not value:
        return None
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def iso_from_epoch(value: Optional[float]) -> Optional[str]:
    """Unix epoch (秒) 转 ISO 格式字符串。"""
    if value is None:
        return None
    try:
        return dt.datetime.fromtimestamp(float(value), dt.timezone.utc).isoformat()
    except (ValueError, TypeError, OSError):
        return None


def iso_from_ms(value: Optional[float]) -> Optional[str]:
    """毫秒级 epoch 转 ISO 格式字符串（自动检测秒/毫秒）。"""
    if value is None:
        return None
    try:
        numeric = float(value)
        if numeric > 10_000_000_000:
            numeric = numeric / 1000
        return dt.datetime.fromtimestamp(numeric, dt.timezone.utc).isoformat()
    except (ValueError, TypeError, OSError):
        return None


def epoch_from_iso(value: Optional[str]) -> Optional[float]:
    """ISO 格式字符串转 Unix epoch (秒)。"""
    parsed = parse_iso(value)
    return parsed.timestamp() if parsed else None


def _session_row_key(row: Dict[str, Any]) -> Optional[Tuple[str, str]]:
    session_id = row.get("session_id")
    if not session_id:
        return None
    return (str(row.get("agent") or "unknown"), str(session_id))


def _session_row_score(row: Dict[str, Any]) -> Tuple[int, int, float]:
    latest_ts = epoch_from_iso(row.get("ended_at") or row.get("started_at")) or 0
    return (
        safe_int(row.get("total_tokens")),
        safe_int(row.get("raw_total_tokens")),
        latest_ts,
    )


def dedupe_session_rows(
    rows: Iterable[Dict[str, Any]],
    *,
    excluded_token_statuses: Optional[Set[str]] = None,
) -> List[Dict[str, Any]]:
    """Collapse repeated cumulative snapshots for the same agent session.

    Codex can write several rollout files with the same session id, where each
    file contains a cumulative token counter. Summing those rows overstates
    usage, so the ledger keeps the highest-token/latest snapshot per
    (agent, session_id). Request-level records such as gateway_reported can be
    excluded because each row is a separate API call.
    """
    excluded = excluded_token_statuses or {"gateway_reported", "n8n_reported"}
    best: Dict[Tuple[str, str], Dict[str, Any]] = {}
    passthrough: List[Dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        key = _session_row_key(row)
        if key is None or row.get("token_status") in excluded:
            passthrough.append(row)
            continue
        current = best.get(key)
        if current is None or _session_row_score(row) >= _session_row_score(current):
            best[key] = row
    return sorted(
        list(best.values()) + passthrough,
        key=lambda row: epoch_from_iso(row.get("ended_at") or row.get("started_at")) or 0,
        reverse=True,
    )


def load_env_file(path: pathlib.Path) -> Dict[str, str]:
    """从 env 文件加载键值对（支持 # 行内注释）。"""
    env: Dict[str, str] = {}
    if not path.exists():
        return env
    for raw in path.read_text(errors="ignore").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def mtime_cached(path: Any, cache: Dict[str, Any], loader) -> Any:
    """基于文件修改时间的配置缓存: 文件不变返回缓存, 文件修改立即重载。

    参数:
        path: 文件路径 (str 或 pathlib.Path)
        cache: 持久字典 {"_mtime": float, "data": Any}, 由调用方持有
        loader: 无参 callable, 返回新数据
    返回:
        缓存或新加载的数据
    """
    try:
        mtime = pathlib.Path(path).stat().st_mtime
    except OSError:
        mtime = 0
    if cache.get("data") is not None and cache.get("_mtime") == mtime:
        return cache["data"]
    data = loader()
    cache["_mtime"] = mtime
    cache["data"] = data
    return data


# ---------------------------------------------------------------------------
# 模型单价 & 费用估算
# ---------------------------------------------------------------------------

import json
import time as _time
import logging

_logger = logging.getLogger(__name__)

# mtime 缓存 — 文件修改后立即重载
_PRICING_MTIME_CACHE: Dict[str, Any] = {"_mtime": 0, "data": None}


def load_model_pricing(data_dir: pathlib.Path) -> Dict[str, Any]:
    """加载模型单价表，构建 alias 反查字典 (mtime 热重载)。

    返回:
        {
            "models": { "deepseek-chat": { input_per_million, output_per_million, currency, ... } },
            "alias_map": { "deepseek_chat": "deepseek-chat", ... },
            "cny_to_usd": 0.14,
        }
    文件不存在或解析失败时返回空结构（不抛异常）。
    """
    pricing_path = data_dir / "model-pricing.json"
    return mtime_cached(pricing_path, _PRICING_MTIME_CACHE, lambda: _parse_model_pricing(pricing_path))


def _parse_model_pricing(pricing_path: pathlib.Path) -> Dict[str, Any]:
    """解析 model-pricing.json（不含缓存逻辑）。"""
    empty = {"models": {}, "alias_map": {}, "cny_to_usd": 0.14}
    if not pricing_path.exists():
        return empty
    try:
        raw = json.loads(pricing_path.read_text(errors="ignore"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError) as exc:
        _logger.warning("model-pricing.json 加载失败: %s", exc)
        return empty
    if not isinstance(raw, dict) or "models" not in raw:
        _logger.warning("model-pricing.json 格式不正确")
        return empty

    models = raw.get("models", {})
    cny_to_usd = float(raw.get("cny_to_usd") or 0.14)

    # 构建 alias → canonical name 反查表
    alias_map: Dict[str, str] = {}
    for canonical, entry in models.items():
        key_norm = _normalize_model_name(canonical)
        alias_map[key_norm] = canonical
        for alias in entry.get("aliases", []):
            alias_map[_normalize_model_name(alias)] = canonical

    return {"models": models, "alias_map": alias_map, "cny_to_usd": cny_to_usd}


def _normalize_model_name(name: str) -> str:
    """标准化模型名：lowercase + 下划线→连字符 + 去首尾空格。"""
    return name.strip().lower().replace("_", "-")


def estimate_cost_usd(
    model: Optional[str],
    input_tokens: int,
    output_tokens: int,
    pricing: Dict[str, Any],
) -> Optional[float]:
    """根据模型单价表估算单次请求的 USD 费用。

    参数:
        model: 模型名（原始格式即可，会自动标准化 + alias 匹配）
        input_tokens: 输入 token 数
        output_tokens: 输出 token 数
        pricing: load_model_pricing() 的返回值

    返回:
        float — 估算费用 (USD)；模型未找到返回 None；免费模型返回 0.0
    """
    if not model:
        return None

    alias_map = pricing.get("alias_map", {})
    models = pricing.get("models", {})
    cny_to_usd = pricing.get("cny_to_usd", 0.14)

    # 标准化 + alias 查找
    norm = _normalize_model_name(model)
    canonical = alias_map.get(norm)

    # 如果 alias 没命中，尝试直接用标准化名
    if canonical is None:
        canonical = norm if norm in models else None
    if canonical is None:
        return None

    entry = models[canonical]

    # 免费模型
    if entry.get("free"):
        return 0.0

    in_rate = float(entry.get("input_per_million", 0))
    out_rate = float(entry.get("output_per_million", 0))

    cost = (safe_int(input_tokens) / 1_000_000) * in_rate + (safe_int(output_tokens) / 1_000_000) * out_rate

    # CNY → USD
    if entry.get("currency", "USD") == "CNY":
        cost = cost * cny_to_usd

    return round(cost, 8)
