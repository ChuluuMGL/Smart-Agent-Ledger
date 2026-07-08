"""
Smart Agent Ledger - local-first AI agent usage ledger with an optional gateway.
Run from this directory with: uvicorn gateway:app --host 0.0.0.0 --port 8001
"""
import logging
from logging.handlers import RotatingFileHandler
import os
import pathlib
import errno
import time
import asyncio
import uuid
import copy
import datetime as dt
import json
import ipaddress
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager, suppress
from zoneinfo import ZoneInfo
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response, StreamingResponse, JSONResponse
import httpx
from agent_ledger import build_agent_ledger, collect_sessions, query_sessions, record_gateway_event
from utils import safe_read_json, load_env_file, mtime_cached
from fleet_ledger import build_fleet_ledger, register_node, remove_node
from feishu_notifier import CONFIG_PATH as FEISHU_CONFIG_PATH, build_alert_text, build_configured_alerts, build_reminder_windows, load_config as load_feishu_config, missing_send_fields, send_configured_alert
from subscription_ledger import build_subscription_ledger, choose_provider_for_route
from usage_report import write_monthly_usage_report
from utils import estimate_cost_usd as _estimate_cost_usd, load_model_pricing as _load_model_pricing

log = logging.getLogger("gateway")


# ---------- 结构化 JSON 日志 ----------
class _JsonFormatter(logging.Formatter):
    """将日志输出为 JSON Lines,方便 jq/grep/ELK 解析。"""
    def format(self, record: logging.LogRecord) -> str:
        entry: Dict[str, Any] = {
            "ts": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0] is not None:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry, ensure_ascii=False)


# Application JSON log rotation.
# data/gateway-app.log = structured JSON logs, rotated automatically (5 x 10MB).
_APP_LOG_FILE = os.path.join(os.path.dirname(__file__), "data", "gateway-app.log")
try:
    os.makedirs(os.path.dirname(_APP_LOG_FILE), exist_ok=True)
    _file_handler = RotatingFileHandler(
        _APP_LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    _file_handler.setFormatter(_JsonFormatter())
    log.addHandler(_file_handler)
    # 同时给 agent_ledger logger 也加上文件 handler
    logging.getLogger("agent_ledger").addHandler(_file_handler)
except OSError:
    pass  # 日志目录不可写时不阻塞启动

# 429/503 重试配置（PRD FR4.3）
RETRY_MAX = 3
RETRY_BASE_DELAY = 1.0
RETRY_BACKOFF = 2.0
FEISHU_REMINDER_STATE_PATH = os.path.join(os.path.dirname(__file__), "data", "feishu-reminder-state.json")


def _load_feishu_config_file() -> Dict[str, Any]:
    data = safe_read_json(FEISHU_CONFIG_PATH, default={})
    return data if isinstance(data, dict) else {}


def _save_feishu_config_file(data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(str(FEISHU_CONFIG_PATH)), exist_ok=True)
    with open(FEISHU_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _bounded_int(value: Any, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (ValueError, TypeError):
        return default
    return max(minimum, min(maximum, parsed))


def _load_feishu_reminder_state() -> Dict[str, Any]:
    data = safe_read_json(FEISHU_REMINDER_STATE_PATH, default={})
    return data if isinstance(data, dict) else {}


def _save_feishu_reminder_state(data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(FEISHU_REMINDER_STATE_PATH), exist_ok=True)
    with open(FEISHU_REMINDER_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _feishu_local_now(config: Dict[str, Any]) -> dt.datetime:
    tz_name = config.get("timezone") or "Asia/Shanghai"
    try:
        tz = ZoneInfo(str(tz_name))
    except (KeyError, ValueError, OSError):  # ZoneInfoNotFoundError 是 KeyError 子类
        tz = ZoneInfo("Asia/Shanghai")
    return dt.datetime.now(tz)


async def _maybe_send_feishu_reminder() -> None:
    config = await asyncio.to_thread(load_feishu_config)
    if not config.get("enabled"):
        return
    if any(missing_send_fields(config).values()):
        return
    now = _feishu_local_now(config)
    reminder_hour = int(config.get("reminder_hour") or 9)
    if now.hour < reminder_hour:
        return
    today = now.date().isoformat()
    state = await asyncio.to_thread(_load_feishu_reminder_state)
    if state.get("last_sent_date") == today:
        return
    alerts = await asyncio.to_thread(build_configured_alerts)
    if not alerts:
        return
    result = await asyncio.to_thread(send_configured_alert)
    state.update(
        {
            "last_checked_at": now.isoformat(),
            "last_sent_date": today if result.get("sent") else state.get("last_sent_date"),
            "last_result": result,
        }
    )
    await asyncio.to_thread(_save_feishu_reminder_state, state)


# P2.1: 后台清理超过 ACTIVE_REQUEST_STALE_SECONDS 的 stale 请求
async def _cleanup_stale_requests() -> None:
    """每 60 秒扫描 ACTIVE_REQUESTS，清理超时未结束的条目。"""
    while True:
        await asyncio.sleep(60)
        now = time.time()
        stale_ids = [
            rid for rid, info in ACTIVE_REQUESTS.items()
            if now - info.get("started_epoch", now) > ACTIVE_REQUEST_STALE_SECONDS
        ]
        for rid in stale_ids:
            info = ACTIVE_REQUESTS.pop(rid, None)
            if info:
                log.warning(
                    "清理 stale 请求: req_id=%s, provider=%s, age=%ds",
                    rid, info.get("provider"), int(now - info.get("started_epoch", now)),
                )


async def _feishu_reminder_loop() -> None:
    while True:
        try:
            await _maybe_send_feishu_reminder()
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            now = dt.datetime.now(dt.timezone.utc).isoformat()
            state = await asyncio.to_thread(_load_feishu_reminder_state)
            state.update({"last_checked_at": now, "last_error": str(exc)})
            await asyncio.to_thread(_save_feishu_reminder_state, state)
            log.warning("Feishu reminder skipped: %s", exc)
        await asyncio.sleep(600)


# P2.5: 后台定时保存统计
async def _stats_persistence_loop() -> None:
    """每 60 秒将 STATS 写入磁盘。"""
    while True:
        await asyncio.sleep(60)
        _save_stats_to_disk()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时校验密钥，缺失时警告（不阻塞启动，便于本地调试）。创建持久 httpx 连接池。"""
    # P2.5: 启动时恢复历史统计
    _load_stats_from_disk()
    # P0.1: 为每个 provider 预创建持久连接池
    for pk, p in PROVIDERS.items():
        CLIENTS[pk] = httpx.AsyncClient(timeout=p["timeout"])
    reminder_task = asyncio.create_task(_feishu_reminder_loop())
    cleanup_task = asyncio.create_task(_cleanup_stale_requests())  # P2.1
    stats_task = asyncio.create_task(_stats_persistence_loop())    # P2.5
    missing = []
    if not os.getenv("DEEPSEEK_API_KEY"):
        missing.append("DEEPSEEK_API_KEY")
    if not os.getenv("GLM_API_KEY"):
        missing.append("GLM_API_KEY")
    if not os.getenv("QWEN_API_KEY"):
        missing.append("QWEN_API_KEY")
    if missing:
        log.warning("以下 key 未设置，对应 provider 可能失败: %s", ", ".join(missing))
    try:
        yield
    finally:
        # P2.5: 关闭前最终写入
        _save_stats_to_disk()
        reminder_task.cancel()
        cleanup_task.cancel()
        stats_task.cancel()
        with suppress(asyncio.CancelledError):
            await reminder_task
        with suppress(asyncio.CancelledError):
            await cleanup_task
        with suppress(asyncio.CancelledError):
            await stats_task
        # 关闭所有持久连接池
        for pk, client in CLIENTS.items():
            with suppress(Exception):
                await client.aclose()
        CLIENTS.clear()


app = FastAPI(title="Smart Agent Ledger", lifespan=lifespan)

# P2.2: CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# P2.2: 简易 IP 限流器（令牌桶）
_RATE_LIMIT_MAX = 60          # 每个 IP 最多 60 个令牌
_RATE_LIMIT_REFILL = 1.0      # 每秒补充 1 个令牌
_RATE_BUCKET_TTL = 3600       # 空闲 IP 记录保留 1 小时
_rate_buckets: Dict[str, Dict[str, Any]] = {}


def _rate_limit_check(client_ip: str) -> bool:
    """返回 True 表示放行，False 表示超限。"""
    now = time.time()
    # TTL 清理：淘汰超过 TTL 未活跃的 IP 记录，防止内存泄漏
    if len(_rate_buckets) > 100:
        expired = [ip for ip, b in _rate_buckets.items() if now - b["last"] > _RATE_BUCKET_TTL]
        for ip in expired:
            del _rate_buckets[ip]
    bucket = _rate_buckets.get(client_ip)
    if bucket is None:
        _rate_buckets[client_ip] = {"tokens": _RATE_LIMIT_MAX - 1, "last": now}
        return True
    elapsed = now - bucket["last"]
    bucket["tokens"] = min(_RATE_LIMIT_MAX, bucket["tokens"] + elapsed * _RATE_LIMIT_REFILL)
    bucket["last"] = now
    if bucket["tokens"] >= 1:
        bucket["tokens"] -= 1
        return True
    return False


# P2.2: 请求校验中间件 —— 请求体大小限制 + 限流
@app.middleware("http")
async def request_validation_middleware(request: Request, call_next):
    # 限流（仅对 API 端点生效）
    if request.url.path.startswith("/v1/"):
        client_ip = request.client.host if request.client else "unknown"
        if not _rate_limit_check(client_ip):
            return JSONResponse(
                status_code=429,
                content={"detail": f"Rate limit exceeded for {client_ip}. Max {_RATE_LIMIT_MAX} req/s."},
            )
    # 请求体大小限制（10MB）
    content_length = request.headers.get("content-length")
    try:
        if content_length and int(content_length) > 10 * 1024 * 1024:
            return JSONResponse(status_code=413, content={"detail": "Request body too large (max 10MB)."})
    except (ValueError, TypeError):
        pass  # 非数字 content-length 头忽略，交给后续处理
    return await call_next(request)
SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "Screenshot")
SCREENSHOT_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
STATIC_DIR = pathlib.Path(__file__).resolve().parent / "static"
_ASSET_DISK_CACHE_DIR = pathlib.Path(
    os.getenv("SMART_GATEWAY_ASSET_CACHE_DIR")
    or pathlib.Path.home() / "Library/Caches/Smart Agent Ledger/static"
)
_ASSET_MEMORY_CACHE: Dict[str, Dict[str, Any]] = {}


def _asset_identity(path: pathlib.Path) -> Dict[str, Any]:
    try:
        stat_result = path.stat()
    except OSError:
        return {}
    return {"mtime_ns": stat_result.st_mtime_ns, "size": stat_result.st_size}


def _asset_disk_cache_path(path: pathlib.Path) -> pathlib.Path:
    return _ASSET_DISK_CACHE_DIR / path.name


def _remember_asset(path: pathlib.Path, content: bytes, identity: Dict[str, Any]) -> None:
    _ASSET_MEMORY_CACHE[str(path)] = {
        "content": content,
        "identity": identity or {"size": len(content)},
    }
    with suppress(OSError):
        _ASSET_DISK_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        _asset_disk_cache_path(path).write_bytes(content)


def _read_asset_bytes(path: pathlib.Path) -> bytes:
    key = str(path)
    identity = _asset_identity(path)
    cached = _ASSET_MEMORY_CACHE.get(key)
    if cached and (not identity or cached.get("identity") == identity):
        return cached["content"]
    try:
        content = path.read_bytes()
    except FileNotFoundError as exc:
        cache_path = _asset_disk_cache_path(path)
        if cache_path.is_file():
            return cache_path.read_bytes()
        raise HTTPException(status_code=404, detail="asset not found") from exc
    except OSError as exc:
        if cached:
            log.warning("Serving in-memory asset cache for %s after source read failed: %s", path.name, exc)
            return cached["content"]
        cache_path = _asset_disk_cache_path(path)
        try:
            content = cache_path.read_bytes()
        except OSError:
            if exc.errno == errno.EDEADLK:
                detail = f"asset temporarily unavailable: {path.name}"
            else:
                detail = f"asset read failed: {path.name}"
            raise HTTPException(status_code=503, detail=detail) from exc
        _ASSET_MEMORY_CACHE[key] = {
            "content": content,
            "identity": identity or {"cache_only": True, "size": len(content)},
        }
        log.warning("Serving disk asset cache for %s after source read failed: %s", path.name, exc)
        return content
    _remember_asset(path, content, identity)
    return content


def _asset_response(path: pathlib.Path, media_type: str) -> Response:
    return Response(
        content=_read_asset_bytes(path),
        media_type=media_type,
        headers={"Cache-Control": "no-store"},
    )


def _prime_static_asset_cache() -> None:
    for asset_name in ("dashboard.css", "dashboard.js"):
        with suppress(Exception):
            _read_asset_bytes(STATIC_DIR / asset_name)


_prime_static_asset_cache()

# P9.3: 自动加载 keys.env（如果存在且环境变量未设置）
_KEYS_ENV = pathlib.Path(__file__).resolve().parent / "keys.env"
if _KEYS_ENV.exists():
    for _k, _v in load_env_file(_KEYS_ENV).items():
        os.environ.setdefault(_k, _v)

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
GLM_API_KEY = os.getenv("GLM_API_KEY", "")
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")

# ========== Gateway 认证 (API Key + IP 白名单) ==========
_GW_API_KEY = os.getenv("GATEWAY_API_KEY", "")

_COMPANY_NODES_PATH = pathlib.Path(__file__).resolve().parent / "data" / "company-agent-nodes.json"
_GW_NETWORKS_CACHE: Dict[str, Any] = {"_mtime": 0, "data": []}


def _parse_authorized_networks() -> list:
    """解析 authorized_networks CIDR 列表（不含缓存逻辑）。"""
    data = safe_read_json(_COMPANY_NODES_PATH, default={})
    networks = []
    for cidr in (data.get("authorized_networks") or []):
        try:
            networks.append(ipaddress.ip_network(str(cidr), strict=False))
        except (ValueError, TypeError):
            log.warning("无效 CIDR in authorized_networks: %s", cidr)
    return networks


def _get_authorized_networks() -> list:
    """获取授权网络列表 (mtime 热重载, 文件修改后立即生效)。"""
    return mtime_cached(_COMPANY_NODES_PATH, _GW_NETWORKS_CACHE, _parse_authorized_networks)


def _ip_in_whitelist(client_ip: str) -> bool:
    """检查客户端 IP 是否在 authorized_networks 白名单内。"""
    try:
        addr = ipaddress.ip_address(client_ip)
        return any(addr in net for net in _get_authorized_networks())
    except (ValueError, TypeError):
        return False


def _has_auth_configured() -> bool:
    """检查是否配置了任何认证方式 (mtime 热重载感知)。"""
    return bool(_GW_API_KEY) or bool(_get_authorized_networks())


_AUTH_PUBLIC_PATHS = frozenset({"/health"})


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """API Key + IP 白名单双重认证。仅 /health 公开。

    - 未配置 GATEWAY_API_KEY 且无 authorized_networks → 允许所有（向后兼容）
    - 客户端 IP 在白名单内 → 直接放行
    - 否则需 X-API-Key 请求头 == GATEWAY_API_KEY
    """
    if request.url.path in _AUTH_PUBLIC_PATHS:
        return await call_next(request)

    # 未配置任何认证方式 → 允许所有（向后兼容，不破坏现有本地使用）
    if not _has_auth_configured():
        return await call_next(request)

    client_ip = request.client.host if request.client else ""

    # IP 白名单校验
    if _ip_in_whitelist(client_ip):
        return await call_next(request)

    # API Key 校验
    if _GW_API_KEY and request.headers.get("X-API-Key") == _GW_API_KEY:
        return await call_next(request)

    log.warning("认证失败: path=%s ip=%s", request.url.path, client_ip)
    return JSONResponse(
        status_code=401,
        content={"detail": "Unauthorized. Provide X-API-Key header or connect from authorized network."},
    )

# ========== Providers (OpenAI Compatible) ==========
PROVIDERS = {
    "local": {
        "url": "http://localhost:11434/v1/chat/completions",
        "model": "codeqwen:7b",
        "headers": {},
        "timeout": 60,
        "concurrency": 1,
    },
    "deepseek_chat": {
        "url": "https://api.deepseek.com/v1/chat/completions",
        "model": "deepseek-chat",
        "headers": lambda: {"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
        "timeout": 60,
        "concurrency": 6,
    },
    "deepseek_reasoner": {
        "url": "https://api.deepseek.com/v1/chat/completions",
        "model": "deepseek-reasoner",
        "headers": lambda: {"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
        "timeout": 120,
        "concurrency": 3,
    },
    "glm_quality": {
        "url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "url_coding": "https://open.bigmodel.cn/api/coding/paas/v4/chat/completions",
        "model": "glm-5",
        "headers": lambda: {"Authorization": f"Bearer {GLM_API_KEY}"},
        "timeout": 120,
        "concurrency": 1,
    },
    "qwen_backup": {
        "url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        "model": "qwen-plus",
        "headers": lambda: {"Authorization": f"Bearer {QWEN_API_KEY}"},
        "timeout": 60,
        "concurrency": 10,
    },
}

SEMAPHORES = {k: asyncio.Semaphore(v["concurrency"]) for k, v in PROVIDERS.items()}
CLIENTS: Dict[str, httpx.AsyncClient] = {}

# P2.5: 统计持久化路径
_STATS_FILE = os.path.join(os.path.dirname(__file__), "data", "gateway-stats.json")
STATS: Dict[str, Any] = {"requests": {p: 0 for p in PROVIDERS}, "total": 0, "fallbacks": 0}


def _load_stats_from_disk() -> None:
    """P2.5: 启动时从磁盘恢复历史统计。"""
    global STATS
    saved = safe_read_json(_STATS_FILE, default=None)
    if saved and isinstance(saved, dict):
        for p in PROVIDERS:
            saved.setdefault("requests", {}).setdefault(p, 0)
        STATS = saved
        log.info("已加载历史统计: total=%s", STATS.get("total", 0))


def _save_stats_to_disk() -> None:
    """P2.5: 将 STATS 写入磁盘。"""
    try:
        with open(_STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(STATS, f, ensure_ascii=False, indent=2)
    except OSError as exc:
        log.warning("保存统计失败: %s", exc)


def _safe_event_text(value: Any, fallback: str = "", limit: int = 160) -> str:
    text = str(value if value is not None else fallback)
    text = " ".join(text.replace("\n", " ").replace("\r", " ").split())
    if not text:
        text = fallback
    return text[:limit]


def _safe_event_float(value: Any) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if parsed < 0:
        return None
    return parsed


def _usage_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    usage = payload.get("usage")
    return usage if isinstance(usage, dict) else payload


def _build_n8n_usage_event(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a n8n side-channel usage event into the gateway event ledger shape.

    This intentionally stores only accounting fields. Prompts, response bodies, URLs,
    commands, headers, and credentials are ignored even if n8n sends them.
    """
    usage = _usage_payload(payload)
    input_tokens = _bounded_int(
        usage.get("prompt_tokens") or usage.get("input_tokens"),
        0,
        0,
        10_000_000_000,
    )
    output_tokens = _bounded_int(
        usage.get("completion_tokens") or usage.get("output_tokens"),
        0,
        0,
        10_000_000_000,
    )
    total_tokens = _bounded_int(
        usage.get("total_tokens"),
        input_tokens + output_tokens,
        0,
        10_000_000_000,
    )
    if total_tokens == 0 and (input_tokens or output_tokens):
        total_tokens = input_tokens + output_tokens

    workflow = _safe_event_text(payload.get("workflow") or payload.get("project"), "n8n workflow", 180)
    task = _safe_event_text(payload.get("task") or payload.get("node_name") or payload.get("node") or workflow, workflow, 180)
    provider = _safe_event_text(payload.get("provider"), "", 80)
    model = _safe_event_text(payload.get("model"), "", 120)
    status = _safe_event_text(payload.get("status"), "recorded", 60)
    source_node = _safe_event_text(payload.get("source_node") or payload.get("node_host") or payload.get("host"), "", 120)
    n8n_execution_id = _safe_event_text(payload.get("execution_id") or payload.get("executionId"), "", 120)
    provider_task_id = _safe_event_text(payload.get("provider_task_id") or payload.get("task_id"), "", 160)

    event_id = str(uuid.uuid4())[:12]
    event = {
        "agent": "n8n",
        "source": "n8n-usage-event",
        "source_node": source_node or None,
        "session_id": _safe_event_text(
            payload.get("session_id") or f"n8n:{n8n_execution_id or provider_task_id or event_id}",
            f"n8n:{event_id}",
            220,
        ),
        "request_id": event_id,
        "project": workflow,
        "task": task,
        "status": status,
        "provider": provider or None,
        "model": model or None,
        "route": "n8n-side-channel",
        "timestamp": _safe_event_text(payload.get("timestamp"), "", 80) or dt.datetime.now(dt.timezone.utc).isoformat(),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "token_status": "n8n_reported" if total_tokens > 0 else "not_available",
        "estimated_cost_usd": _safe_event_float(payload.get("estimated_cost_usd")),
        "actual_cost_usd": _safe_event_float(payload.get("actual_cost_usd")),
        "cost_status": _safe_event_text(
            payload.get("cost_status"),
            "n8n_reported"
            if (
                _safe_event_float(payload.get("actual_cost_usd")) is not None
                or _safe_event_float(payload.get("estimated_cost_usd")) is not None
            )
            else "unknown",
            80,
        ),
        "duration_ms": _bounded_int(payload.get("duration_ms"), 0, 0, 24 * 60 * 60 * 1000),
        "media_units": _bounded_int(payload.get("media_units"), 0, 0, 1_000_000),
        "video_seconds": _safe_event_float(payload.get("video_seconds")),
        "image_count": _bounded_int(payload.get("image_count"), 0, 0, 1_000_000),
        "n8n_workflow_id": _safe_event_text(payload.get("workflow_id") or payload.get("workflowId"), "", 120) or None,
        "n8n_execution_id": n8n_execution_id or None,
        "provider_task_id": provider_task_id or None,
        "confidence": "reported_by_n8n_side_channel",
    }
    return {key: value for key, value in event.items() if value is not None}


def _clear_usage_caches() -> None:
    LEDGER_CACHE.clear()
    FLEET_CACHE.clear()
    _SESSIONS_ROWS_CACHE.clear()
ACTIVE_REQUESTS: Dict[str, Dict[str, Any]] = {}
LEDGER_CACHE = {}
LEDGER_TASKS = {}

# P3.2: Provider 健康状态 —— 记录连续失败次数，达到阈值后暂时跳过
PROVIDER_HEALTH: Dict[str, Dict[str, Any]] = {
    pk: {"consecutive_failures": 0, "last_success": None, "last_failure": None, "skip_until": 0.0}
    for pk in PROVIDERS
}
PROVIDER_HEALTH_THRESHOLD = 3        # 连续失败 ≥3 次标记为不可用
PROVIDER_HEALTH_COOLDOWN = 300.0     # 标记后 5 分钟内跳过


def _provider_is_healthy(pk: str) -> bool:
    """检查 provider 是否处于健康状态（未被标记为不可用）。"""
    h = PROVIDER_HEALTH.get(pk)
    if h is None:
        return True
    if h["consecutive_failures"] < PROVIDER_HEALTH_THRESHOLD:
        return True
    # 冷却期已过，重新允许尝试
    if time.time() >= h["skip_until"]:
        h["consecutive_failures"] = 0
        return True
    return False


def _record_provider_success(pk: str) -> None:
    h = PROVIDER_HEALTH.get(pk)
    if h:
        h["consecutive_failures"] = 0
        h["last_success"] = time.time()


def _record_provider_failure(pk: str) -> None:
    h = PROVIDER_HEALTH.get(pk)
    if h:
        h["consecutive_failures"] += 1
        h["last_failure"] = time.time()
        if h["consecutive_failures"] >= PROVIDER_HEALTH_THRESHOLD:
            h["skip_until"] = time.time() + PROVIDER_HEALTH_COOLDOWN
            log.warning("Provider %s 连续失败 %d 次，将在 %.0f 秒内跳过", pk, h["consecutive_failures"], PROVIDER_HEALTH_COOLDOWN)

# P2.1: ACTIVE_REQUESTS 泄漏防护 —— 超过此秒数的请求视为 stale 并自动清理
ACTIVE_REQUEST_STALE_SECONDS = 600  # 10 分钟
LEDGER_CACHE_TTL_SECONDS = 60  # P9.1: 从 300s 降到 60s，匹配 Dashboard 30s 轮询节奏
LEDGER_FIRST_RESPONSE_TIMEOUT_SECONDS = 20.0  # 冷启动优先等真实账本，超时再用旧快照并后台刷新
SUBSCRIPTION_CACHE = {}
SUBSCRIPTION_CACHE_TTL_SECONDS = 60
FLEET_CACHE = {}
FLEET_CACHE_TTL_SECONDS = 60
FLEET_TASKS: Dict[tuple, asyncio.Task] = {}
FLEET_STALE_IF_ERROR_SECONDS = 15 * 60
FLEET_LOCAL_LEDGER_WAIT_SECONDS = 8.0
FLEET_LOCAL_LEDGER_LIMIT = 1000


def _parse_fleet_prefetch_windows(raw: str) -> tuple:
    windows = []
    for item in str(raw or "").split(","):
        item = item.strip()
        if not item:
            continue
        with suppress(ValueError):
            days = int(item)
            if 1 <= days <= 3660 and days not in windows:
                windows.append(days)
    return tuple(windows)


FLEET_PREFETCH_WINDOWS = _parse_fleet_prefetch_windows(
    os.getenv("SMART_GATEWAY_FLEET_PREFETCH_WINDOWS", "7,30,90")
)
FLEET_DISK_CACHE_DIR = pathlib.Path(
    os.getenv("SMART_GATEWAY_FLEET_CACHE_DIR")
    or pathlib.Path.home() / "Library/Caches/Smart Agent Ledger/fleet"
)


def _fleet_has_node_issue(data: Dict[str, Any]) -> bool:
    if data.get("access_issues"):
        return True
    for node in data.get("nodes") or []:
        if not isinstance(node, dict):
            continue
        if node.get("status") in {"unreachable", "error", "missing_url"}:
            return True
    return False


def _fleet_has_stale_export_issue(data: Dict[str, Any]) -> bool:
    for node in data.get("nodes") or []:
        if isinstance(node, dict) and node.get("export_stale"):
            return True
    for item in data.get("access_issues") or []:
        if isinstance(item, dict) and "ledger export is stale" in str(item.get("issue") or ""):
            return True
    return False


def _fleet_cache_is_usable(data: Dict[str, Any]) -> bool:
    return not data.get("_last_refresh_failed") and not _fleet_has_node_issue(data)


def _fleet_disk_cache_path(days: int) -> pathlib.Path:
    safe_days = _bounded_int(days, 30, 1, 3660)
    return FLEET_DISK_CACHE_DIR / f"fleet-ledger-{safe_days}d.json"


def _cache_fleet_ledger_data(cache_key: tuple, data: Dict[str, Any]) -> None:
    FLEET_CACHE[cache_key] = {"ts": time.time(), "data": data}
    if not _fleet_cache_is_usable(data):
        return
    days = _bounded_int(data.get("window_days") or cache_key[0], cache_key[0], 1, 3660)
    with suppress(OSError):
        FLEET_DISK_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with _fleet_disk_cache_path(days).open("w", encoding="utf-8") as f:
            json.dump({"ts": time.time(), "data": data}, f, ensure_ascii=False)


def _latest_complete_fleet_cache(days: int, now: Optional[float] = None) -> Optional[Dict[str, Any]]:
    now = time.time() if now is None else now
    candidates = [
        value
        for key, value in FLEET_CACHE.items()
        if key[0] == days
        and now - value["ts"] < FLEET_STALE_IF_ERROR_SECONDS
        and _fleet_cache_is_usable(value.get("data", {}))
    ]
    if candidates:
        latest = max(candidates, key=lambda value: value["ts"])
        return {"ts": latest["ts"], "data": copy.deepcopy(latest["data"])}

    payload = safe_read_json(_fleet_disk_cache_path(days), default=None)
    if not isinstance(payload, dict):
        return None
    data = payload.get("data")
    ts = float(payload.get("ts") or 0)
    if not isinstance(data, dict):
        return None
    if now - ts >= FLEET_STALE_IF_ERROR_SECONDS:
        return None
    if not _fleet_cache_is_usable(data):
        return None
    return {"ts": ts, "data": copy.deepcopy(data)}


def _latest_fleet_cache(days: int, limit: int, now: Optional[float] = None) -> Optional[Dict[str, Any]]:
    now = time.time() if now is None else now
    exact = FLEET_CACHE.get((days, limit))
    if exact and now - exact["ts"] < FLEET_STALE_IF_ERROR_SECONDS and _fleet_cache_is_usable(exact.get("data", {})):
        return {"ts": exact["ts"], "data": copy.deepcopy(exact["data"])}

    candidates = [
        value
        for key, value in FLEET_CACHE.items()
        if key[0] == days
        and now - value["ts"] < FLEET_STALE_IF_ERROR_SECONDS
        and _fleet_cache_is_usable(value.get("data", {}))
    ]
    if candidates:
        latest = max(candidates, key=lambda value: value["ts"])
        return {"ts": latest["ts"], "data": copy.deepcopy(latest["data"])}

    payload = safe_read_json(_fleet_disk_cache_path(days), default=None)
    if not isinstance(payload, dict):
        return None
    data = payload.get("data")
    ts = float(payload.get("ts") or 0)
    if not isinstance(data, dict):
        return None
    if now - ts >= FLEET_STALE_IF_ERROR_SECONDS:
        return None
    if not _fleet_cache_is_usable(data):
        return None
    return {"ts": ts, "data": copy.deepcopy(data)}


def _fleet_has_fresh_cache(days: int, limit: int, now: Optional[float] = None) -> bool:
    now = time.time() if now is None else now
    cached = FLEET_CACHE.get((days, limit))
    if cached and now - cached["ts"] < FLEET_CACHE_TTL_SECONDS and _fleet_cache_is_usable(cached.get("data", {})):
        return True
    for key, value in FLEET_CACHE.items():
        if key[0] != days:
            continue
        if now - value["ts"] < FLEET_CACHE_TTL_SECONDS and _fleet_cache_is_usable(value.get("data", {})):
            return True
    payload = safe_read_json(_fleet_disk_cache_path(days), default=None)
    if not isinstance(payload, dict):
        return False
    data = payload.get("data")
    ts = float(payload.get("ts") or 0)
    return bool(
        isinstance(data, dict)
        and now - ts < FLEET_CACHE_TTL_SECONDS
        and _fleet_cache_is_usable(data)
    )


def _schedule_fleet_prefetch_windows(days: int, limit: int) -> None:
    if not FLEET_PREFETCH_WINDOWS:
        return
    now = time.time()
    for prefetch_days in FLEET_PREFETCH_WINDOWS:
        if prefetch_days == days:
            continue
        cache_key = (prefetch_days, limit)
        task = FLEET_TASKS.get(cache_key)
        if task is not None:
            if not task.done():
                continue
            FLEET_TASKS.pop(cache_key, None)
        if _fleet_has_fresh_cache(prefetch_days, limit, now=now):
            continue
        FLEET_TASKS[cache_key] = asyncio.create_task(
            _refresh_fleet_cache(cache_key, prefetch_days, limit)
        )


def _decorate_stale_fleet_response(entry: Dict[str, Any], now: float) -> Dict[str, Any]:
    data = copy.deepcopy(entry["data"])
    data["_stale_cache_age_seconds"] = max(0, int(now - entry["ts"]))
    data["_stale"] = True
    data["_refreshing"] = True
    return data


def _decorate_partial_fleet_cache_response(entry: Dict[str, Any], now: float) -> Dict[str, Any]:
    data = copy.deepcopy(entry["data"])
    data["_partial_cache"] = True
    data["_cache_age_seconds"] = max(0, int(now - entry["ts"]))
    return data


async def _await_agent_ledger_refresh(cache_key: tuple, timeout_seconds: float) -> Optional[Dict[str, Any]]:
    task = LEDGER_TASKS.get(cache_key)
    if task is None:
        return None
    try:
        data = await asyncio.wait_for(asyncio.shield(task), timeout=timeout_seconds)
    except asyncio.TimeoutError:
        return None
    except Exception as exc:
        if task.done():
            LEDGER_TASKS.pop(cache_key, None)
        log.warning("Agent ledger refresh failed while preparing fleet ledger: %s", exc)
        return None

    if task.done():
        LEDGER_TASKS.pop(cache_key, None)
    _cache_agent_ledger_data(cache_key, data)
    data = copy.deepcopy(data)
    data["_refreshing"] = False
    data["_stale"] = False
    return _decorate_agent_ledger_response(data, cache_key)


async def _build_fleet_ledger_response(days: int, limit: int) -> Dict[str, Any]:
    local_cache_key = (days, FLEET_LOCAL_LEDGER_LIMIT)
    local_ledger = await _get_agent_ledger_data(days=days, limit=FLEET_LOCAL_LEDGER_LIMIT)
    local_ready = _agent_ledger_ready(local_ledger)
    if not local_ready:
        refreshed_ledger = await _await_agent_ledger_refresh(local_cache_key, FLEET_LOCAL_LEDGER_WAIT_SECONDS)
        if refreshed_ledger is not None:
            local_ledger = refreshed_ledger
            local_ready = _agent_ledger_ready(local_ledger)
    local_fallback = None if local_ready else _latest_cached_agent_ledger_data(days=days)
    local_for_fleet = local_ledger if local_ready else local_fallback
    return await build_fleet_ledger(
        days=days,
        limit=limit,
        local_agent_ledger=local_for_fleet,
        skip_local_agent_scan=local_for_fleet is None,
    )


async def _refresh_fleet_cache(cache_key: tuple, days: int, limit: int) -> Dict[str, Any]:
    try:
        data = await _build_fleet_ledger_response(days, limit)
        _cache_fleet_ledger_data(cache_key, data)
        return data
    finally:
        FLEET_TASKS.pop(cache_key, None)


def _empty_agent_ledger(days: int, limit: int) -> Dict[str, Any]:
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "window_days": days,
        "totals": {
            "sessions": 0,
            "agents": 0,
            "projects": 0,
            "total_tokens": 0,
            "known_token_sessions": 0,
            "known_cost_usd": 0.0,
            "known_cost_sessions": 0,
            "unknown_cost_sessions": 0,
            "lines_added": 0,
            "lines_removed": 0,
            "files_changed": 0,
            "active_sessions": 0,
            "infrastructure_components": 0,
            "infrastructure_records": 0,
        },
        "by_agent": [],
        "by_project": [],
        "by_task": [],
        "by_model": [],
        "agent_inventory": [],
        "recent_sessions": [],
        "access_issues": [],
        "notes": [
            "Agent ledger is refreshing in the background; retry shortly for source-backed rows.",
        ],
        "_refreshing": True,
        "_stale": False,
        "_requested_limit": limit,
    }


def _demo_mode_enabled() -> bool:
    enabled_values = {"1", "true", "yes", "on"}
    return (
        os.getenv("SMART_AGENT_LEDGER_DEMO_MODE", "").strip().lower() in enabled_values
        or os.getenv("SMART_GATEWAY_DEMO_MODE", "").strip().lower() in enabled_values
    )


def _demo_ts(offset_days: int = 0) -> str:
    base = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    return (base + dt.timedelta(days=offset_days)).isoformat()


def _demo_agent_ledger(days: int, limit: int) -> Dict[str, Any]:
    recent_sessions = [
        {
            "session_id": "demo-codex-001",
            "agent": "Codex",
            "project": "Website Redesign",
            "task": "Landing page polish",
            "model": "gpt-5-codex",
            "total_tokens": 482_000,
            "cost_usd": 1.92,
            "started_at": _demo_ts(-1),
            "updated_at": _demo_ts(0),
            "data_quality": "real",
        },
        {
            "session_id": "demo-claude-002",
            "agent": "Claude Code",
            "project": "Internal Analytics",
            "task": "Usage report refactor",
            "model": "claude-sonnet",
            "total_tokens": 316_000,
            "cost_usd": 2.68,
            "started_at": _demo_ts(-2),
            "updated_at": _demo_ts(-1),
            "data_quality": "real",
        },
        {
            "session_id": "demo-cursor-003",
            "agent": "Cursor",
            "project": "Support Automation",
            "task": "Inbox triage workflow",
            "model": "metadata-only",
            "total_tokens": 0,
            "cost_usd": None,
            "started_at": _demo_ts(-3),
            "updated_at": _demo_ts(-2),
            "data_quality": "activity_only",
        },
    ][: max(1, min(limit, 3))]
    total_tokens = sum(int(row.get("total_tokens") or 0) for row in recent_sessions)
    return {
        "demo_mode": True,
        "generated_at": _demo_ts(0),
        "window_days": days,
        "totals": {
            "sessions": 128,
            "agents": 5,
            "projects": 4,
            "total_tokens": total_tokens + 7_250_000,
            "known_token_sessions": 96,
            "known_cost_usd": 42.35,
            "known_cost_sessions": 91,
            "unknown_cost_sessions": 37,
            "active_sessions": 12,
            "lines_added": 18_420,
            "lines_removed": 6_340,
            "files_changed": 214,
        },
        "by_agent": [
            {"agent": "Codex", "sessions": 52, "total_tokens": 3_820_000, "known_cost_usd": 18.4},
            {"agent": "Claude Code", "sessions": 36, "total_tokens": 2_640_000, "known_cost_usd": 14.7},
            {"agent": "OpenClaw", "sessions": 21, "total_tokens": 1_180_000, "known_cost_usd": 5.1},
            {"agent": "Cursor", "sessions": 19, "total_tokens": 0, "token_status": "metadata_only"},
        ],
        "by_project": [
            {"project": "Website Redesign", "sessions": 44, "total_tokens": 2_940_000},
            {"project": "Internal Analytics", "sessions": 33, "total_tokens": 2_210_000},
            {"project": "Support Automation", "sessions": 27, "total_tokens": 1_520_000},
        ],
        "by_task": [
            {"task": "Landing page polish", "sessions": 18, "total_tokens": 1_120_000},
            {"task": "Monthly usage report", "sessions": 11, "total_tokens": 840_000},
        ],
        "by_model": [
            {"model": "gpt-5-codex", "sessions": 41, "total_tokens": 3_110_000},
            {"model": "claude-sonnet", "sessions": 29, "total_tokens": 2_480_000},
        ],
        "agent_inventory": [
            {"agent": "Codex", "status": "connected", "sessions": 52},
            {"agent": "Claude Code", "status": "connected", "sessions": 36},
            {"agent": "Cursor", "status": "metadata_only", "sessions": 19},
            {"agent": "Trae", "status": "installed_no_recent", "sessions": 0},
        ],
        "recent_sessions": recent_sessions,
        "access_issues": [],
        "notes": ["Demo mode uses anonymous sample rows and does not read local AI tool logs."],
        "_requested_limit": limit,
        "_refreshing": False,
        "_stale": False,
    }


def _demo_fleet_ledger(days: int, limit: int) -> Dict[str, Any]:
    agent = _demo_agent_ledger(days, limit)
    return {
        "demo_mode": True,
        "generated_at": _demo_ts(0),
        "window_days": days,
        "totals": {
            "records": 184,
            "activity_sessions": 312,
            "total_tokens": 9_860_000,
            "known_token_records": 144,
            "known_cost_usd": 58.2,
            "known_cost_sessions": 137,
            "configured_nodes": 3,
            "current_data_nodes": 3,
            "active_sessions": 18,
        },
        "node_health": {
            "status": "complete",
            "complete": True,
            "configured_nodes": 3,
            "connected_nodes": 3,
            "current_data_node_count": 3,
            "real_token_nodes": 2,
            "activity_only_nodes": 1,
            "unavailable_nodes": 0,
        },
        "nodes": [
            {
                "node": "demo-founder-mac",
                "name": "demo-founder-mac",
                "status": "connected",
                "data_quality": "real",
                "token_included": True,
                "token_total": 5_940_000,
                "records": 84,
                "activity_count": 132,
                "latest_at": _demo_ts(0),
            },
            {
                "node": "demo-designer-mac",
                "name": "demo-designer-mac",
                "status": "connected",
                "data_quality": "real",
                "token_included": True,
                "token_total": 3_920_000,
                "records": 60,
                "activity_count": 108,
                "latest_at": _demo_ts(-1),
            },
            {
                "node": "demo-automation-node",
                "name": "demo-automation-node",
                "status": "connected",
                "data_quality": "activity_only",
                "token_included": False,
                "token_total": 0,
                "records": 40,
                "activity_count": 72,
                "latest_at": _demo_ts(0),
            },
        ],
        "agent_token_rank": agent["by_agent"],
        "agent_activity_rank": [
            {"agent": "Codex", "activity_count": 96, "sessions": 52},
            {"agent": "Claude Code", "activity_count": 74, "sessions": 36},
            {"agent": "n8n", "activity_count": 72, "token_status": "activity_only"},
        ],
        "project_token_rank": agent["by_project"],
        "project_activity_rank": [
            {"project": "Website Redesign", "activity_count": 88},
            {"project": "Support Automation", "activity_count": 76},
        ],
        "activity_timeline": [
            {"date": _demo_ts(-2)[:10], "activity_count": 64, "total_tokens": 1_820_000},
            {"date": _demo_ts(-1)[:10], "activity_count": 91, "total_tokens": 3_040_000},
            {"date": _demo_ts(0)[:10], "activity_count": 122, "total_tokens": 5_000_000},
        ],
        "access_issues": [],
        "config_paths": {},
        "notes": ["Demo mode uses anonymous team-node data."],
        "_refreshing": False,
        "_stale": False,
    }


def _demo_subscription_ledger() -> Dict[str, Any]:
    return {
        "demo_mode": True,
        "generated_at": _demo_ts(0),
        "totals": {"plans": 3, "alerts": 1, "renewal_alerts": 1, "quota_alerts": 0},
        "plans": [
            {
                "id": "demo-chatgpt-team",
                "name": "ChatGPT Team",
                "provider_key": "openai",
                "status": "renewal_soon",
                "billing_amount": 30,
                "billing_currency": "USD",
                "billing_period": "month",
                "renewal_at": _demo_ts(5),
                "days_to_renewal": 5,
                "quota_remaining_pct": 72,
                "auto_renew": True,
            },
            {
                "id": "demo-claude-pro",
                "name": "Claude Pro",
                "provider_key": "anthropic",
                "status": "ok",
                "billing_amount": 20,
                "billing_currency": "USD",
                "billing_period": "month",
                "renewal_at": _demo_ts(18),
                "days_to_renewal": 18,
                "quota_remaining_pct": 61,
                "auto_renew": True,
            },
            {
                "id": "demo-deepseek-api",
                "name": "DeepSeek API Credits",
                "provider_key": "deepseek",
                "status": "ok",
                "billing_amount": 50,
                "billing_currency": "USD",
                "billing_period": "prepaid",
                "renewal_at": None,
                "days_to_renewal": None,
                "quota_remaining_pct": 84,
                "auto_renew": False,
            },
        ],
        "routing_advice": {
            "preferred": [{"provider_key": "deepseek", "remaining_pct": 84}],
            "avoid": [],
        },
        "config_path": "demo://model-subscriptions",
    }


def _demo_feishu_reminder() -> Dict[str, Any]:
    subscriptions = _demo_subscription_ledger()
    return {
        "demo_mode": True,
        "enabled": False,
        "ready_to_send": False,
        "missing": [],
        "app_id_present": False,
        "app_secret_present": False,
        "receive_id_type": "chat_id",
        "receive_id_present": False,
        "receive_id_masked": None,
        "recipient_name": "Demo workspace",
        "reminder_hour": 9,
        "timezone": "Asia/Shanghai",
        "default_renewal_warning_days": 7,
        "plan_warning_days": {},
        "reminder_windows": subscriptions["plans"],
        "feishu_alerts": subscriptions["totals"]["alerts"],
        "preview": "Demo reminder preview. Configure Feishu credentials to send real alerts.",
        "config_path": "demo://feishu-reminder",
        "last_checked_at": None,
        "last_sent_date": None,
        "last_error": None,
    }


def _decorate_agent_ledger_response(data: Dict[str, Any], cache_key: tuple) -> Dict[str, Any]:
    active_rows = list(ACTIVE_REQUESTS.values())
    if active_rows:
        data["recent_sessions"] = active_rows + data.get("recent_sessions", [])
        totals = data.setdefault("totals", {})
        totals["active_sessions"] = totals.get("active_sessions", 0) + len(active_rows)
    cached = LEDGER_CACHE.get(cache_key)
    if cached:
        data["_cache_age_seconds"] = max(0, int(time.time() - cached["ts"]))
    else:
        data.setdefault("_cache_age_seconds", None)
    return data


def _cache_agent_ledger_data(cache_key: tuple, data: Dict[str, Any]) -> None:
    LEDGER_CACHE[cache_key] = {"ts": time.time(), "data": data}
    if len(LEDGER_CACHE) <= 20:
        return
    now = time.time()
    expired_keys = [
        key for key, value in LEDGER_CACHE.items()
        if now - value["ts"] > LEDGER_CACHE_TTL_SECONDS
    ]
    for key in expired_keys:
        LEDGER_CACHE.pop(key, None)
        LEDGER_TASKS.pop(key, None)


def _agent_ledger_ready(data: Dict[str, Any]) -> bool:
    return bool(data.get("recent_sessions")) and not data.get("_refreshing")


def _latest_cached_agent_ledger_data(days: Optional[int] = None) -> Optional[Dict[str, Any]]:
    now = time.time()
    candidates = [
        value
        for key, value in LEDGER_CACHE.items()
        if now - value["ts"] < LEDGER_CACHE_TTL_SECONDS
        and (days is None or key[0] == days)
        and value.get("data", {}).get("recent_sessions")
    ]
    if not candidates:
        return None
    latest = max(candidates, key=lambda value: value["ts"])
    data = copy.deepcopy(latest["data"])
    data["_cache_age_seconds"] = max(0, int(now - latest["ts"]))
    data["_ledger_cache_fallback"] = True
    data["_fleet_cache_fallback"] = True
    return data


async def _get_agent_ledger_data(days: int, limit: int) -> Dict[str, Any]:
    cache_key = (days, limit)
    cached = LEDGER_CACHE.get(cache_key)
    now = time.time()
    if cached and now - cached["ts"] < LEDGER_CACHE_TTL_SECONDS:
        data = copy.deepcopy(cached["data"])
        data["_refreshing"] = False
        data["_stale"] = False
        return _decorate_agent_ledger_response(data, cache_key)

    task = LEDGER_TASKS.get(cache_key)
    if task is not None and task.done():
        LEDGER_TASKS.pop(cache_key, None)
        try:
            data = task.result()
        except Exception as exc:
            log.warning("Agent ledger background refresh failed: %s", exc)
        else:
            _cache_agent_ledger_data(cache_key, data)
            data = copy.deepcopy(data)
            data["_refreshing"] = False
            data["_stale"] = False
            return _decorate_agent_ledger_response(data, cache_key)
        task = None

    if task is None:
        task = asyncio.create_task(asyncio.to_thread(build_agent_ledger, days=days, limit=limit))
        LEDGER_TASKS[cache_key] = task

    try:
        data = await asyncio.wait_for(
            asyncio.shield(task),
            timeout=LEDGER_FIRST_RESPONSE_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        if cached:
            data = copy.deepcopy(cached["data"])
            data["_stale"] = True
        else:
            data = _latest_cached_agent_ledger_data(days=days) or _empty_agent_ledger(days, limit)
            data["_stale"] = bool(data.get("recent_sessions"))
        data["_refreshing"] = True
        return _decorate_agent_ledger_response(data, cache_key)
    except Exception:
        if task.done():
            LEDGER_TASKS.pop(cache_key, None)
        raise

    if task.done():
        LEDGER_TASKS.pop(cache_key, None)
    _cache_agent_ledger_data(cache_key, data)
    data = copy.deepcopy(data)
    data["_refreshing"] = False
    data["_stale"] = False
    return _decorate_agent_ledger_response(data, cache_key)

# P2.4: 从配置文件加载关键词，支持热更新；文件缺失时回退到内嵌默认值
_KW_DEFAULTS = {
    "local_hint": ["改变量名", "重命名", "格式化", "加注释", "简单", "快速", "小改"],
    "coding": ["代码", "编程", "debug", "bug", "报错", "异常", "traceback", "stack",
               "class ", "def ", "import ", "pytest", "SQL", "接口", "API", "重构", "单测", "mock"],
    "reasoning": ["推理", "证明", "复杂度", "权衡", "架构", "系统设计", "多步", "严谨分析",
                  "算法设计", "root cause", "why", "tradeoff"],
    "quality": ["终稿", "对外", "发客户", "PRD", "投标", "不可出错", "正式版", "润色", "审校", "总结成文档"],
}
_KW_FILE = os.path.join(os.path.dirname(__file__), "data", "routing-keywords.json")
_KW_MTIME_CACHE: Dict[str, Any] = {"_mtime": 0, "data": None}


def _parse_keywords() -> Dict[str, List[str]]:
    """解析 routing-keywords.json（不含缓存逻辑）。"""
    try:
        with open(_KW_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {k: data.get(k, v) for k, v in _KW_DEFAULTS.items()}
    except (FileNotFoundError, json.JSONDecodeError):
        return dict(_KW_DEFAULTS)


def _get_pricing() -> Dict[str, Any]:
    """获取模型单价表 (mtime 热重载, 代理到 utils)。"""
    return _load_model_pricing(DATA_DIR)


def _load_keywords() -> Dict[str, List[str]]:
    """加载路由关键词 (mtime 热重载, 文件修改后立即生效)。"""
    return mtime_cached(_KW_FILE, _KW_MTIME_CACHE, _parse_keywords)


KW_LOCAL_HINT = _KW_DEFAULTS["local_hint"]
KW_CODING = _KW_DEFAULTS["coding"]
KW_REASON = _KW_DEFAULTS["reasoning"]
KW_QUALITY = _KW_DEFAULTS["quality"]


def _messages_text(messages: List[Dict[str, Any]]) -> str:
    parts = []
    for m in messages:
        c = m.get("content")
        if isinstance(c, str):
            parts.append(c)
        else:
            parts.append(str(c))
    return " ".join(parts).lower()


def _metadata_from_request(request: Request, payload: Dict[str, Any], req_id: str) -> Dict[str, Any]:
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    headers = request.headers
    user_agent = headers.get("user-agent")
    return {
        "request_id": req_id,
        "agent": headers.get("x-agent-name") or headers.get("x-agent") or metadata.get("agent") or user_agent or "Gateway Client",
        "project": headers.get("x-project") or headers.get("x-project-name") or metadata.get("project"),
        "project_path": headers.get("x-project-path") or metadata.get("project_path"),
        "task": headers.get("x-task") or headers.get("x-task-name") or metadata.get("task") or "Gateway request",
        "session_id": headers.get("x-session-id") or metadata.get("session_id") or req_id,
        "status": metadata.get("status") or "active",
        "source": "gateway",
    }


def _usage_from_response(out: Any) -> Dict[str, int]:
    if not isinstance(out, dict):
        return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    usage = out.get("usage") or {}
    input_tokens = usage.get("prompt_tokens") or usage.get("input_tokens") or 0
    output_tokens = usage.get("completion_tokens") or usage.get("output_tokens") or 0
    total_tokens = usage.get("total_tokens") or (int(input_tokens or 0) + int(output_tokens or 0))
    return {
        "input_tokens": int(input_tokens or 0),
        "output_tokens": int(output_tokens or 0),
        "total_tokens": int(total_tokens or 0),
    }


def detect_route(messages: List[Dict[str, Any]], forced: Optional[str] = None) -> str:
    if forced in ["local", "coding", "reasoning", "quality"]:
        return forced
    # P2.4: 动态加载关键词（支持热更新）
    kw = _load_keywords()
    text = _messages_text(messages)
    # P2.4: 移除 len(text) < 400 限制，短消息也走完整路由判断
    if any(k.lower() in text for k in kw["local_hint"]):
        return "local"
    if any(k.lower() in text for k in kw["quality"]):
        return "quality"
    if any(k.lower() in text for k in kw["reasoning"]):
        return "reasoning"
    if any(k.lower() in text for k in kw["coding"]) or "```" in text:
        return "coding"
    return "coding"


def route_to_provider(route: str) -> str:
    if route == "local":
        return "local"
    if route == "coding":
        return "deepseek_chat"
    if route == "reasoning":
        return "deepseek_reasoner"
    if route == "quality":
        return "glm_quality"
    return "deepseek_chat"


def fallback_chain(route: str) -> List[str]:
    if route == "local":
        return ["local", "coding", "backup"]
    if route == "coding":
        return ["coding", "backup", "quality"]
    if route == "reasoning":
        return ["reasoning", "coding", "backup"]
    if route == "quality":
        return ["quality", "coding", "backup"]
    return ["coding", "backup"]


def _build_upstream_request(provider_key: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """透传客户端请求，仅覆盖 model。兼容 GLM/Z.AI 的 tools、tool_stream、stream 等参数。"""
    p = PROVIDERS[provider_key]
    req = dict(payload)
    req["model"] = p["model"]
    if "messages" not in req:
        req["messages"] = []
    return req


def _glm_url(provider_key: str, payload: Dict[str, Any]) -> str:
    """GLM 有 tools/tool_choice 时用 Coding Plan 端点，兼容 Z.AI tool_stream。"""
    p = PROVIDERS.get(provider_key, {})
    base = p.get("url", "")
    coding = p.get("url_coding")
    if not coding:
        return base
    if payload.get("tools") or payload.get("tool_choice"):
        return coding
    return base


async def _call_with_fallback(provider_key: str, payload: Dict[str, Any], url: str):
    """调用上游，失败时 GLM 可回退到标准端点。"""
    p = PROVIDERS[provider_key]
    headers = p["headers"]() if callable(p["headers"]) else p["headers"]
    auth_header = headers.get("Authorization") if isinstance(headers, dict) else None
    if auth_header is not None and auth_header.strip().lower() == "bearer":
        raise HTTPException(status_code=401, detail=f"{provider_key} API key missing")
    req = _build_upstream_request(provider_key, payload)
    stream = req.get("stream", False)

    async def _do_request():
        client = CLIENTS[provider_key]
        async with SEMAPHORES[provider_key]:
            if stream:
                # P0.1: 使用持久连接池 + 手动管理流式响应生命周期
                req_obj = client.build_request("POST", url, json=req, headers=headers)
                resp = await client.send(req_obj, stream=True)
                if resp.status_code in (429, 503):
                    body = await resp.aread()
                    await resp.aclose()
                    raise HTTPException(status_code=resp.status_code, detail=f"{provider_key} throttled: {body.decode()}")
                resp.raise_for_status()

                async def _pass_and_close():
                    try:
                        async for chunk in resp.aiter_bytes():
                            yield chunk
                    finally:
                        await resp.aclose()

                stream_headers = {"Cache-Control": "no-cache", "Connection": "keep-alive"}
                ct = resp.headers.get("content-type") or "text/event-stream"
                return StreamingResponse(
                    _pass_and_close(),
                    media_type=ct,
                    headers=stream_headers,
                )
            r = await client.post(url, json=req, headers=headers)
            if r.status_code in (429, 503):
                raise HTTPException(status_code=r.status_code, detail=f"{provider_key} throttled: {r.text}")
            r.raise_for_status()
            return r.json()

    last_err = None
    for attempt in range(RETRY_MAX):
        try:
            return await _do_request()
        except HTTPException as e:
            if e.status_code in (429, 503) and attempt < RETRY_MAX - 1:
                delay = RETRY_BASE_DELAY * (RETRY_BACKOFF ** attempt)
                last_err = e
                log.warning("%s 429/503，%.1fs 后重试 (%d/%d)", provider_key, delay, attempt + 1, RETRY_MAX)
                await asyncio.sleep(delay)
            else:
                raise
        except httpx.HTTPError as e:
            last_err = e
            if attempt < RETRY_MAX - 1:
                delay = RETRY_BASE_DELAY * (RETRY_BACKOFF ** attempt)
                log.warning("%s 请求失败，%.1fs 后重试 (%d/%d): %s", provider_key, delay, attempt + 1, RETRY_MAX, e)
                await asyncio.sleep(delay)
            else:
                raise
    raise last_err


async def call_provider(provider_key: str, payload: Dict[str, Any]):
    """调用上游；支持 stream 与 non-stream，透传 tools/tool_choice 等。GLM Coding 端点失败时回退到标准端点。"""
    p = PROVIDERS[provider_key]
    url = _glm_url(provider_key, payload) if provider_key == "glm_quality" else p["url"]
    base_url = p.get("url", "")
    try:
        return await _call_with_fallback(provider_key, payload, url)
    except httpx.HTTPError as e:
        if provider_key == "glm_quality" and url != base_url:
            log.warning("glm coding 端点失败，回退到标准端点: %s", e)
            return await _call_with_fallback(provider_key, payload, base_url)
        raise


@app.get("/health")
async def health():
    # P3.2: 展示各 provider 健康状态
    providers = {}
    for pk, h in PROVIDER_HEALTH.items():
        healthy = _provider_is_healthy(pk)
        providers[pk] = {
            "healthy": healthy,
            "consecutive_failures": h["consecutive_failures"],
            "last_success": h["last_success"],
            "last_failure": h["last_failure"],
            "skip_until": h["skip_until"] if h["skip_until"] > time.time() else None,
        }
    return {"status": "ok", "ts": time.time(), "providers": providers}


@app.get("/stats")
async def stats():
    """按 provider 的请求次数（内存统计，重启清零）。PRD FR5.2 的 token/成本 在 M3 实现。"""
    return {
        "by_provider": STATS["requests"],
        "total_requests": STATS["total"],
        "fallbacks": STATS["fallbacks"],
        "note": "tokens/成本 未实现，见 PRD M3",
    }


def _detect_forced_route(model_hint: str) -> Optional[str]:
    """从 model 字段检测强制路由。"""
    hint = (model_hint or "").lower()
    if "smart-local" in hint:
        return "local"
    elif "smart-coding" in hint:
        return "coding"
    elif "smart-reasoning" in hint:
        return "reasoning"
    elif "smart-quality" in hint:
        return "quality"
    elif "glm" in hint or "zai" in hint:
        return "quality"
    return None


def _build_provider_chain(chain_routes: list, sub_ledger_data: Optional[dict] = None) -> list:
    """根据 fallback chain 构建具体 provider 列表。"""
    provider_chain = []
    for rname in chain_routes:
        if rname == "backup":
            provider_chain.append("qwen_backup")
        else:
            default_provider = route_to_provider(rname)
            provider_chain.append(choose_provider_for_route(rname, default_provider, list(PROVIDERS.keys()), ledger_data=sub_ledger_data))
    return provider_chain


# P9.4: OpenAI 兼容的 /v1/models 端点
@app.get("/v1/models")
async def list_models():
    """列出网关可用的模型及其路由标签。"""
    models = []
    # 路由标签别名
    route_labels = {"local": "Ollama Local", "coding": "Coding", "reasoning": "Reasoning", "quality": "Quality", "backup": "Backup (Qwen)"}
    for rname in ["local", "coding", "reasoning", "quality", "backup"]:
        default_provider = route_to_provider(rname)
        provider_cfg = PROVIDERS.get(default_provider, {})
        model = provider_cfg.get("model", default_provider)
        models.append({
            "id": f"smart-{rname}",
            "object": "model",
            "owned_by": "smart-gateway",
            "routed_to": default_provider,
            "underlying_model": model,
        })
    return {"object": "list", "data": models}


# P2.4: 路由诊断端点 —— 只返回路由决策，不转发请求
@app.post("/v1/chat/completions/dry-run")
async def chat_completions_dry_run(request: Request):
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"detail": "Invalid JSON body."})
    messages = payload.get("messages") or []
    if not isinstance(messages, list) or len(messages) == 0:
        raise HTTPException(status_code=400, detail="messages 必须为非空数组")
    forced = _detect_forced_route(payload.get("model") or "")
    route = detect_route(messages, forced=forced)
    chain_routes = fallback_chain(route)
    sub_cached = SUBSCRIPTION_CACHE.get("default")
    sub_ledger_data = sub_cached["data"] if sub_cached and time.time() - sub_cached["ts"] < SUBSCRIPTION_CACHE_TTL_SECONDS else None
    provider_chain = _build_provider_chain(chain_routes, sub_ledger_data)
    return {
        "route": route,
        "forced": forced,
        "chain_routes": chain_routes,
        "provider_chain": provider_chain,
        "keywords_loaded_from": _KW_FILE if os.path.exists(_KW_FILE) else "defaults",
        "message_count": len(messages),
        "text_length": len(_messages_text(messages)),
    }


@app.get("/config")
async def config():
    """当前路由词表与 provider 列表，支持动态加载最新配置。"""
    kw = _load_keywords()
    return {
        "routing": {
            "local_hint": kw.get("local_hint", []),
            "coding": kw.get("coding", []),
            "reasoning": kw.get("reasoning", []),
            "quality": kw.get("quality", []),
        },
        "providers": list(PROVIDERS.keys()),
        "edit_hint": "修改词表或权重也可以直接编辑 data/routing-keywords.json 或编辑 gateway.py",
    }


@app.post("/config/routing")
async def update_routing_config(payload: Dict[str, List[str]]):
    """更新路由关键词词表，并清除缓存实现热加载。"""
    required_keys = {"local_hint", "coding", "reasoning", "quality"}
    for key in required_keys:
        if key not in payload:
            raise HTTPException(status_code=400, detail=f"缺少必要的路由字段: {key}")
        if not isinstance(payload[key], list):
            raise HTTPException(status_code=400, detail=f"字段 {key} 必须为列表(数组)")
        for item in payload[key]:
            if not isinstance(item, str):
                raise HTTPException(status_code=400, detail=f"字段 {key} 中的元素必须为字符串")

    # 写入文件
    try:
        os.makedirs(os.path.dirname(_KW_FILE), exist_ok=True)
        with open(_KW_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"保存配置文件失败: {exc}")

    # 清空关键词 mtime 缓存，下次调用时自动重载
    _KW_MTIME_CACHE["_mtime"] = 0

    return {"status": "ok", "message": "路由词表更新成功并已热加载"}



@app.get("/ui", response_class=HTMLResponse)
def dashboard():
    """只读 Web 仪表盘：健康、统计、词表与 provider。"""
    return (STATIC_DIR / "dashboard.html").read_text(encoding="utf-8")


# P3.3: 服务拆分后的 CSS/JS 静态资源
@app.get("/dashboard.css")
def dashboard_css():
    return _asset_response(STATIC_DIR / "dashboard.css", "text/css")


@app.get("/dashboard.js")
def dashboard_js():
    return _asset_response(STATIC_DIR / "dashboard.js", "application/javascript")


@app.get("/screenshots/{filename}")
def screenshot_asset(filename: str):
    safe_name = os.path.basename(filename)
    _, ext = os.path.splitext(safe_name)
    if safe_name != filename or ext.lower() not in SCREENSHOT_EXTENSIONS:
        raise HTTPException(status_code=404, detail="screenshot not found")
    path = os.path.join(SCREENSHOT_DIR, safe_name)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="screenshot not found")
    media_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }
    return _asset_response(pathlib.Path(path), media_types[ext.lower()])


@app.get("/agent-ledger")
async def agent_ledger(days: int = 30, limit: int = 100):
    if _demo_mode_enabled():
        return _demo_agent_ledger(days=days, limit=limit)
    return await _get_agent_ledger_data(days=days, limit=limit)


@app.post("/usage-events/n8n")
async def ingest_n8n_usage_event(request: Request):
    """Best-effort n8n usage side channel.

    This endpoint does not proxy or alter n8n business calls. It only appends a
    normalized usage event to the local agent ledger so existing dashboards can
    pick it up on the next refresh.
    """
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"detail": "Invalid JSON body."})
    if not isinstance(payload, dict):
        return JSONResponse(status_code=400, content={"detail": "payload must be object"})
    event = _build_n8n_usage_event(payload)
    await asyncio.to_thread(record_gateway_event, event)
    _clear_usage_caches()
    return {
        "status": "ok",
        "recorded": True,
        "event_id": event.get("request_id"),
        "agent": "n8n",
        "project": event.get("project"),
        "provider": event.get("provider"),
        "model": event.get("model"),
        "total_tokens": event.get("total_tokens", 0),
        "token_status": event.get("token_status"),
        "cost_status": event.get("cost_status"),
        "note": "Side-channel accounting only; n8n workflow execution is not proxied or changed.",
    }


# P11: 管理员会话明细缓存 — 复用采集结果, 60s, 供 /admin/sessions 筛选/分页
_SESSIONS_ROWS_CACHE: Dict[int, Dict[str, Any]] = {}
_SESSIONS_ROWS_TTL = 60.0


def _get_sessions_rows(days: int) -> List[Dict[str, Any]]:
    """获取采集后的完整会话 rows (带 60s 缓存, 供 /admin/sessions 复用)。"""
    now = time.time()
    cached = _SESSIONS_ROWS_CACHE.get(days)
    if cached and now - cached["ts"] < _SESSIONS_ROWS_TTL:
        return cached["rows"]
    rows, _ = collect_sessions(days)
    _SESSIONS_ROWS_CACHE[days] = {"ts": now, "rows": rows}
    return rows


@app.get("/admin/sessions")
async def admin_sessions(
    days: int = 30,
    agent: Optional[str] = None,
    project: Optional[str] = None,
    min_tokens: int = 0,
    sort: str = "time",
    page: int = 1,
    page_size: int = 50,
):
    """管理员会话明细查询 — 支持筛选 + 排序 + 分页。

    受 auth_middleware 保护 (需 GATEWAY_API_KEY 或 IP 白名单)。
    前端主视图聚焦聚合排行, 具体会话明细由此端点按需查询。
    """
    rows = _get_sessions_rows(days)
    return await asyncio.to_thread(
        query_sessions,
        days=days, agent=agent, project=project,
        min_tokens=min_tokens, sort=sort, page=page, page_size=page_size,
        rows=rows,
    )


# P2: Fleet 节点管理 — 注册/列出/移除团队设备 (受 auth_middleware 保护)
@app.get("/admin/nodes")
async def list_nodes():
    """列出所有已注册的 Fleet 节点 (含连接状态)。"""
    return await build_fleet_ledger()


@app.post("/admin/nodes")
async def add_node(payload: Dict[str, Any] = {}):
    """注册一个 Fleet 节点 (团队设备接入)。

    body: {"name": "dev-1", "base_url": "http://192.0.2.100:8002",
           "enabled": true, "ledger_url": "(可选)",
           "base_url_candidates": ["http://dev-1.local:8002"]}
    注册后配合配置热重载, 下次 /fleet-ledger 自动包含。
    """
    name = str(payload.get("name") or "").strip()
    base_url = str(payload.get("base_url") or "").strip()
    if not name or not base_url:
        raise HTTPException(status_code=400, detail="name and base_url are required")
    if not base_url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="base_url must start with http:// or https://")
    enabled = bool(payload.get("enabled", True))
    ledger_url = payload.get("ledger_url") or None
    extra = {
        key: payload.get(key)
        for key in (
            "type",
            "host",
            "role",
            "base_url_candidates",
            "base_urls",
            "fallback_base_urls",
            "ledger_url_candidates",
            "fallback_ledger_urls",
            "timeout_seconds",
        )
        if payload.get(key) is not None
    }
    return await asyncio.to_thread(register_node, name, base_url, enabled, ledger_url, **extra)


@app.delete("/admin/nodes/{name}")
async def delete_node(name: str):
    """按 name 移除一个 Fleet 节点。"""
    return await asyncio.to_thread(remove_node, name)


# P6: SSE 推送 — 替代前端轮询, 每客户端按自身 days/limit 窗口推送
_SSE_INTERVAL_SECONDS = 30.0


@app.get("/stream/ledger")
async def stream_ledger(days: int = 30, limit: int = 100):
    """SSE: 每 30s 推送 ledger 更新 (替代前端定时轮询)。受 auth_middleware 保护。

    每个连接按其请求的 days/limit 窗口重算并推送; 客户端断开时自动取消。
    """
    async def event_gen():
        try:
            while True:
                data = await _get_agent_ledger_data(days=days, limit=limit)
                payload = json.dumps(data, ensure_ascii=False, default=str)
                yield f"event: ledger\ndata: {payload}\n\n"
                await asyncio.sleep(_SSE_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            return

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
    )


@app.get("/subscription-ledger")
async def subscription_ledger():
    if _demo_mode_enabled():
        return _demo_subscription_ledger()
    cached = SUBSCRIPTION_CACHE.get("default")
    now = time.time()
    if cached and now - cached["ts"] < SUBSCRIPTION_CACHE_TTL_SECONDS:
        return copy.deepcopy(cached["data"])
    data = await asyncio.to_thread(build_subscription_ledger)
    SUBSCRIPTION_CACHE["default"] = {"ts": now, "data": data}
    return data


def _mask_identifier(value: Any) -> Optional[str]:
    if not value:
        return None
    text = str(value)
    if len(text) <= 8:
        return "*" * len(text)
    return f"{text[:4]}...{text[-6:]}"


@app.get("/feishu-reminder")
async def feishu_reminder():
    if _demo_mode_enabled():
        return _demo_feishu_reminder()
    config = await asyncio.to_thread(load_feishu_config)
    missing = [key for key, value in missing_send_fields(config).items() if value]
    preview = await asyncio.to_thread(build_alert_text)
    windows = await asyncio.to_thread(build_reminder_windows)
    alerts = await asyncio.to_thread(build_configured_alerts)
    state = await asyncio.to_thread(_load_feishu_reminder_state)
    return {
        "enabled": bool(config.get("enabled")),
        "ready_to_send": not bool(missing),
        "missing": missing,
        "app_id_present": bool(config.get("app_id")),
        "app_secret_present": bool(config.get("app_secret")),
        "receive_id_type": config.get("receive_id_type"),
        "receive_id_present": bool(config.get("receive_id")),
        "receive_id_masked": _mask_identifier(config.get("receive_id")),
        "recipient_name": config.get("recipient_name"),
        "reminder_hour": config.get("reminder_hour"),
        "timezone": config.get("timezone"),
        "default_renewal_warning_days": config.get("default_renewal_warning_days"),
        "plan_warning_days": config.get("plan_warning_days") or {},
        "reminder_windows": windows,
        "feishu_alerts": len(alerts),
        "preview": preview,
        "config_path": str(FEISHU_CONFIG_PATH),
        "last_checked_at": state.get("last_checked_at"),
        "last_sent_date": state.get("last_sent_date"),
        "last_error": state.get("last_error"),
    }


@app.post("/feishu-reminder/settings")
async def update_feishu_reminder_settings(request: Request):
    payload = await request.json()
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="payload must be object")
    config = await asyncio.to_thread(_load_feishu_config_file)
    if "reminder_hour" in payload:
        config["reminder_hour"] = _bounded_int(payload.get("reminder_hour"), 9, 0, 23)
    if "default_renewal_warning_days" in payload:
        config["default_renewal_warning_days"] = _bounded_int(payload.get("default_renewal_warning_days"), 7, 0, 365)
    if isinstance(payload.get("plan_warning_days"), dict):
        plan_warning_days = {}
        for plan_id, days in payload["plan_warning_days"].items():
            if not isinstance(plan_id, str) or not plan_id:
                continue
            plan_warning_days[plan_id] = _bounded_int(days, config.get("default_renewal_warning_days", 7), 0, 365)
        config["plan_warning_days"] = plan_warning_days
    await asyncio.to_thread(_save_feishu_config_file, config)
    return await feishu_reminder()


@app.get("/fleet-ledger")
async def fleet_ledger(days: int = 30, limit: int = 100):
    if _demo_mode_enabled():
        return _demo_fleet_ledger(days=days, limit=limit)
    cache_key = (days, limit)
    cached = FLEET_CACHE.get(cache_key)
    now = time.time()
    if cached and now - cached["ts"] < FLEET_CACHE_TTL_SECONDS:
        if _fleet_cache_is_usable(cached.get("data", {})):
            _schedule_fleet_prefetch_windows(days, limit)
            return copy.deepcopy(cached["data"])
        if not cached.get("data", {}).get("_last_refresh_failed"):
            return _decorate_partial_fleet_cache_response(cached, now)

    task = FLEET_TASKS.get(cache_key)
    if task is not None and task.done():
        FLEET_TASKS.pop(cache_key, None)
        with suppress(Exception):
            data = task.result()
            if _fleet_cache_is_usable(data):
                _schedule_fleet_prefetch_windows(days, limit)
                return copy.deepcopy(data)

    stale_cache = _latest_fleet_cache(days=days, limit=limit, now=now)
    if stale_cache is not None:
        if task is None:
            FLEET_TASKS[cache_key] = asyncio.create_task(_refresh_fleet_cache(cache_key, days, limit))
        _schedule_fleet_prefetch_windows(days, limit)
        return _decorate_stale_fleet_response(stale_cache, now)

    data = await _build_fleet_ledger_response(days=days, limit=limit)
    has_node_issue = _fleet_has_node_issue(data)
    if has_node_issue and not _fleet_has_stale_export_issue(data):
        fallback_cache = _latest_complete_fleet_cache(days=days, now=now)
        if fallback_cache is not None:
            stale = copy.deepcopy(fallback_cache["data"])
            stale["_stale_cache_age_seconds"] = max(0, int(now - fallback_cache["ts"]))
            stale["_stale"] = True
            stale["_refreshing"] = False
            stale["_last_refresh_failed"] = True
            stale["latest_access_issues"] = data.get("access_issues") or []
            stale["latest_partial_totals"] = data.get("totals") or {}
            return stale
    if not has_node_issue:
        _cache_fleet_ledger_data(cache_key, data)
        _schedule_fleet_prefetch_windows(days, limit)
    else:
        _cache_fleet_ledger_data(cache_key, data)
    return data


@app.post("/reports/monthly-usage")
async def create_monthly_usage_report(days: int = 30, limit: int = 120, month: Optional[str] = None):
    bounded_days = _bounded_int(days, 30, 1, 366)
    bounded_limit = _bounded_int(limit, 120, 10, 500)
    fleet = await fleet_ledger(days=bounded_days, limit=bounded_limit)
    subscriptions = await subscription_ledger()
    result = await asyncio.to_thread(
        write_monthly_usage_report,
        fleet,
        subscriptions,
        month=month,
        days=bounded_days,
    )
    return {"status": "ok", **result}


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    req_id = str(uuid.uuid4())[:8]
    started = time.time()
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"detail": "Invalid JSON body."})
    request_meta = _metadata_from_request(request, payload, req_id)
    ACTIVE_REQUESTS[req_id] = {
        **request_meta,
        "agent": request_meta.get("agent"),
        "source": "gateway-active",
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(started)),
        "started_epoch": started,  # P2.1: 用于 stale 清理
        "ended_at": None,
        "provider": None,
        "model": payload.get("model"),
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "estimated_cost_usd": None,
        "cost_status": "in_progress",
        "message_count": 1,
        "tool_call_count": 0,
    }
    messages = payload.get("messages") or []
    if not isinstance(messages, list) or len(messages) == 0:
        ACTIVE_REQUESTS.pop(req_id, None)
        raise HTTPException(status_code=400, detail="messages 必须为非空数组")
    forced = _detect_forced_route(payload.get("model") or "")
    route = detect_route(messages, forced=forced)
    chain_routes = fallback_chain(route)
    # P0.2: 使用缓存的订阅数据避免路由决策时重复读磁盘
    sub_cached = SUBSCRIPTION_CACHE.get("default")
    sub_ledger_data = sub_cached["data"] if sub_cached and time.time() - sub_cached["ts"] < SUBSCRIPTION_CACHE_TTL_SECONDS else None
    provider_chain = _build_provider_chain(chain_routes, sub_ledger_data)
    last_err = None
    for pk in provider_chain:
        if pk not in PROVIDERS:
            continue
        # P3.2: 跳过不健康的 provider
        if not _provider_is_healthy(pk):
            log.info("[%s] 跳过不健康 provider %s", req_id, pk)
            continue
        try:
            log.info("[%s] route=%s -> provider=%s", req_id, route, pk)
            ACTIVE_REQUESTS[req_id]["provider"] = pk
            ACTIVE_REQUESTS[req_id]["model"] = PROVIDERS[pk]["model"]
            out = await call_provider(pk, payload)
            _record_provider_success(pk)  # P3.2
            STATS["requests"][pk] = STATS["requests"].get(pk, 0) + 1
            STATS["total"] += 1
            if last_err is not None:
                STATS["fallbacks"] += 1

            if isinstance(out, dict):
                # 非流式：立即记录 token 用量
                usage = _usage_from_response(out)
                _model_name = PROVIDERS[pk]["model"]
                _pricing = _get_pricing()
                _cost = _estimate_cost_usd(_model_name, usage["input_tokens"], usage["output_tokens"], _pricing)
                record_gateway_event(
                    {
                        **request_meta,
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "status": "success",
                        "route": route,
                        "provider": pk,
                        "model": _model_name,
                        "duration_ms": int((time.time() - started) * 1000),
                        "fallback": last_err is not None,
                        "input_tokens": usage["input_tokens"],
                        "output_tokens": usage["output_tokens"],
                        "total_tokens": usage["total_tokens"],
                        "estimated_cost_usd": _cost,
                        "cost_status": "gateway_pricing_estimate" if _cost is not None else "usage_only_no_price_table",
                    }
                )
                ACTIVE_REQUESTS.pop(req_id, None)
                return out
            else:
                # P0.3: 流式响应 —— 包装 generator 解析 SSE 末尾 usage，流结束后补记 token
                original_gen = out.body_iterator

                async def _stream_with_usage(
                    _gen=original_gen, _pk=pk, _route=route, _started=started, _fb=last_err is not None,
                ):
                    usage_data = None
                    buffer = b""
                    try:
                        async for chunk in _gen:
                            yield chunk
                            # 解析 SSE 数据行寻找 usage 字段
                            buffer += chunk
                            while b"\n" in buffer:
                                line, buffer = buffer.split(b"\n", 1)
                                line_str = line.decode("utf-8", errors="ignore").strip()
                                if line_str.startswith("data: ") and line_str != "data: [DONE]":
                                    try:
                                        sse_data = json.loads(line_str[6:])
                                        if isinstance(sse_data, dict) and isinstance(sse_data.get("usage"), dict):
                                            usage_data = sse_data["usage"]
                                    except (json.JSONDecodeError, ValueError):
                                        pass
                    finally:
                        usage = _usage_from_response({"usage": usage_data}) if usage_data else {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
                        _stream_model = PROVIDERS[_pk]["model"]
                        _stream_pricing = _get_pricing()
                        _stream_cost = _estimate_cost_usd(_stream_model, usage["input_tokens"], usage["output_tokens"], _stream_pricing)
                        record_gateway_event(
                            {
                                **request_meta,
                                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                "status": "stream_completed",
                                "route": _route,
                                "provider": _pk,
                                "model": _stream_model,
                                "duration_ms": int((time.time() - _started) * 1000),
                                "fallback": _fb,
                                "input_tokens": usage["input_tokens"],
                                "output_tokens": usage["output_tokens"],
                                "total_tokens": usage["total_tokens"],
                                "token_status": "stream_usage_captured" if usage_data else "stream_no_usage",
                                "estimated_cost_usd": _stream_cost,
                                "cost_status": "gateway_pricing_estimate" if _stream_cost is not None else ("usage_only_no_price_table" if usage_data else "stream_no_usage_data"),
                            }
                        )

                # 记录流开始事件
                record_gateway_event(
                    {
                        **request_meta,
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "status": "stream_started",
                        "route": route,
                        "provider": pk,
                        "model": PROVIDERS[pk]["model"],
                        "duration_ms": int((time.time() - started) * 1000),
                        "fallback": last_err is not None,
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "total_tokens": 0,
                        "token_status": "stream_pending",
                        "estimated_cost_usd": None,
                        "cost_status": "stream_pending_usage",
                    }
                )
                ACTIVE_REQUESTS.pop(req_id, None)
                return StreamingResponse(
                    _stream_with_usage(),
                    media_type=out.media_type,
                    headers=dict(out.headers.items()) if hasattr(out.headers, "items") else {},
                )
        except (httpx.HTTPError, httpx.InvalidURL, json.JSONDecodeError, UnicodeDecodeError) as e:
            last_err = str(e)
            _record_provider_failure(pk)  # P3.2
            log.warning("[%s] %s failed: %s", req_id, pk, e)
            continue
    record_gateway_event(
        {
            **request_meta,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "status": "failed",
            "route": route,
            "duration_ms": int((time.time() - started) * 1000),
            "error": last_err,
            "estimated_cost_usd": None,
            "cost_status": "failed_no_usage",
        }
    )
    ACTIVE_REQUESTS.pop(req_id, None)
    raise HTTPException(status_code=503, detail=f"All providers failed. last_err={last_err}")
