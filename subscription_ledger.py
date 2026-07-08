#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import os
import pathlib
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from utils import safe_float, safe_int, safe_read_json


PROJECT_ROOT = pathlib.Path(__file__).resolve().parent
DATA_DIR = pathlib.Path(os.getenv("SMART_GATEWAY_DATA_DIR", PROJECT_ROOT / "data"))
CONFIG_PATH = DATA_DIR / "model-subscriptions.json"
DEFAULT_TZ = "Asia/Shanghai"


def _now(tz_name: str = DEFAULT_TZ) -> dt.datetime:
    try:
        tz = ZoneInfo(tz_name)
    except (KeyError, ValueError, OSError):
        tz = ZoneInfo(DEFAULT_TZ)
    return dt.datetime.now(tz)


def _parse_date(value: Any, tz_name: str = DEFAULT_TZ) -> Optional[dt.datetime]:
    if not value:
        return None
    text = str(value).strip()
    try:
        parsed = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=ZoneInfo(tz_name))
        return parsed.astimezone(ZoneInfo(tz_name))
    except (ValueError, TypeError):
        pass
    try:
        return dt.datetime.combine(dt.date.fromisoformat(text), dt.time.min, ZoneInfo(tz_name))
    except (ValueError, TypeError):
        return None




def _next_renewal(plan: Dict[str, Any], now: dt.datetime) -> Optional[dt.datetime]:
    billing = plan.get("billing") or {}
    renewal = _parse_date(billing.get("renewal_date") or plan.get("renewal_date"), plan.get("timezone") or DEFAULT_TZ)
    interval_months = safe_int(billing.get("renewal_interval_months") or plan.get("renewal_interval_months"))
    interval_days = safe_int(billing.get("renewal_interval_days") or plan.get("renewal_interval_days"))
    if not renewal:
        return None
    if interval_months and interval_months > 0:
        while renewal < now:
            month = renewal.month + interval_months
            year = renewal.year + (month - 1) // 12
            month = ((month - 1) % 12) + 1
            day = renewal.day
            while day > 28:
                try:
                    renewal = renewal.replace(year=year, month=month, day=day)
                    break
                except ValueError:
                    day -= 1
            else:
                renewal = renewal.replace(year=year, month=month, day=day)
        return renewal
    if interval_days and interval_days > 0:
        while renewal < now:
            renewal = renewal + dt.timedelta(days=interval_days)
    return renewal


def _time_on_day(day: dt.date, time_text: Optional[str], tz_name: str) -> dt.datetime:
    hour = 0
    minute = 0
    if time_text:
        parts = str(time_text).split(":")
        if parts:
            hour = int(parts[0] or 0)
        if len(parts) > 1:
            minute = int(parts[1] or 0)
    return dt.datetime.combine(day, dt.time(hour=hour, minute=minute), ZoneInfo(tz_name))


def _next_reset(plan: Dict[str, Any], now: dt.datetime) -> Optional[dt.datetime]:
    reset = plan.get("reset") or {}
    reset_type = reset.get("type")
    if not reset_type:
        return None
    tz_name = reset.get("timezone") or plan.get("timezone") or DEFAULT_TZ
    local_now = now.astimezone(ZoneInfo(tz_name))
    time_text = reset.get("time")
    if reset_type == "daily":
        candidate = _time_on_day(local_now.date(), time_text, tz_name)
        if candidate <= local_now:
            candidate += dt.timedelta(days=1)
        return candidate
    if reset_type == "weekly":
        # weekday=0 (Monday) is valid — check key existence before safe_int
        if reset.get("weekday") is None:
            return None
        weekday = safe_int(reset.get("weekday"))
        days_ahead = (weekday - local_now.weekday()) % 7
        candidate = _time_on_day(local_now.date() + dt.timedelta(days=days_ahead), time_text, tz_name)
        if candidate <= local_now:
            candidate += dt.timedelta(days=7)
        return candidate
    if reset_type == "monthly":
        day = safe_int(reset.get("day_of_month"))
        if day is None or day < 1:
            return None
        year = local_now.year
        month = local_now.month
        while True:
            try:
                candidate = _time_on_day(dt.date(year, month, day), time_text, tz_name)
            except ValueError:
                candidate = None
            if candidate and candidate > local_now:
                return candidate
            month += 1
            if month > 12:
                month = 1
                year += 1
    return None


def load_config(path: pathlib.Path = CONFIG_PATH) -> Dict[str, Any]:
    if not path.exists():
        return {"schema_version": 1, "plans": [], "_config_exists": False}
    data = safe_read_json(path, default=None)
    if data is None:
        return {"schema_version": 1, "plans": [], "_config_exists": True, "_load_error": "read failed"}
    if not isinstance(data, dict):
        return {"schema_version": 1, "plans": [], "_config_exists": True, "_load_error": "root must be object"}
    data["_config_exists"] = True
    if not isinstance(data.get("plans"), list):
        data["plans"] = []
    return data


def _plan_status(plan: Dict[str, Any], days_to_renewal: Optional[int], remaining_pct: Optional[float]) -> str:
    quota = plan.get("quota") or {}
    billing = plan.get("billing") or {}
    warn_days = safe_int(billing.get("renewal_warning_days")) or 7
    warn_pct = safe_float(quota.get("warning_threshold_pct"))
    if days_to_renewal is not None and days_to_renewal <= 0:
        return "renewal_due"
    if remaining_pct is not None and warn_pct is not None and remaining_pct <= warn_pct:
        return "quota_low"
    if days_to_renewal is not None and days_to_renewal <= warn_days:
        return "renewal_soon"
    if remaining_pct is None and quota.get("limit") is not None:
        return "quota_unknown"
    return "ok"


def _normalize_plan(plan: Dict[str, Any], now: dt.datetime) -> Dict[str, Any]:
    quota = plan.get("quota") or {}
    usage = plan.get("usage") or {}
    renewal = _next_renewal(plan, now)
    reset_at = _next_reset(plan, now)
    limit = safe_float(quota.get("limit"))
    used = safe_float(usage.get("used"))
    remaining = None
    remaining_pct = None
    if limit is not None and used is not None:
        remaining = max(limit - used, 0)
        remaining_pct = (remaining / limit * 100) if limit > 0 else None
    days_to_renewal = None
    if renewal:
        days_to_renewal = (renewal.date() - now.date()).days
    status = _plan_status(plan, days_to_renewal, remaining_pct)
    return {
        "id": plan.get("id"),
        "name": plan.get("name") or plan.get("id"),
        "agent": plan.get("agent"),
        "provider": plan.get("provider"),
        "provider_key": (plan.get("routing") or {}).get("provider_key") or plan.get("provider_key"),
        "model": plan.get("model"),
        "billing_type": (plan.get("billing") or {}).get("type") or plan.get("billing_type"),
        "billing_amount": safe_float((plan.get("billing") or {}).get("amount")),
        "billing_currency": (plan.get("billing") or {}).get("currency"),
        "billing_period": (plan.get("billing") or {}).get("period"),
        "auto_renew": (plan.get("billing") or {}).get("auto_renew"),
        "renewal_at": renewal.isoformat() if renewal else None,
        "days_to_renewal": days_to_renewal,
        "reset_at": reset_at.isoformat() if reset_at else None,
        "quota_unit": quota.get("unit"),
        "quota_limit": limit,
        "quota_used": used,
        "quota_remaining": remaining,
        "quota_remaining_pct": round(remaining_pct, 3) if remaining_pct is not None else None,
        "quota_advertised_text": quota.get("advertised_text"),
        "status": status,
        "usage_source": usage.get("source"),
        "usage_as_of": usage.get("as_of"),
        "routing": plan.get("routing") or {},
        "source_note": plan.get("source_note"),
        "raw_source": "data/model-subscriptions.json",
    }


def _routing_advice(plans: List[Dict[str, Any]]) -> Dict[str, Any]:
    avoid = []
    preferred = []
    for plan in plans:
        routing = plan.get("routing") or {}
        provider_key = plan.get("provider_key")
        if not provider_key:
            continue
        reserve_pct = safe_float(routing.get("reserve_pct"))
        remaining_pct = safe_float(plan.get("quota_remaining_pct"))
        if plan.get("status") in {"quota_low", "renewal_due"}:
            avoid.append({"provider_key": provider_key, "plan": plan.get("name"), "reason": plan.get("status")})
            continue
        if reserve_pct is not None and remaining_pct is not None and remaining_pct <= reserve_pct:
            avoid.append({"provider_key": provider_key, "plan": plan.get("name"), "reason": "below_reserve_pct"})
            continue
        preferred.append(
            {
                "provider_key": provider_key,
                "plan": plan.get("name"),
                "priority": safe_int(routing.get("priority")) or 0,
                "remaining_pct": remaining_pct,
            }
        )
    preferred.sort(key=lambda item: (item.get("priority") or 0, item.get("remaining_pct") or -1), reverse=True)
    return {"preferred": preferred, "avoid": avoid}


def build_subscription_ledger(path: pathlib.Path = CONFIG_PATH) -> Dict[str, Any]:
    config = load_config(path)
    tz_name = config.get("timezone") or DEFAULT_TZ
    now = _now(tz_name)
    plans = [_normalize_plan(plan, now) for plan in config.get("plans", []) if isinstance(plan, dict)]
    alerts = [plan for plan in plans if plan.get("status") in {"renewal_due", "renewal_soon", "quota_low", "quota_unknown"}]
    return {
        "generated_at": now.isoformat(),
        "config_path": str(path),
        "config_exists": bool(config.get("_config_exists")),
        "load_error": config.get("_load_error"),
        "totals": {
            "plans": len(plans),
            "alerts": len(alerts),
            "renewal_alerts": sum(1 for plan in alerts if plan.get("status") in {"renewal_due", "renewal_soon"}),
            "quota_alerts": sum(1 for plan in alerts if plan.get("status") in {"quota_low", "quota_unknown"}),
        },
        "plans": plans,
        "alerts": alerts,
        "routing_advice": _routing_advice(plans),
        "notes": [
            "No subscription or quota number is inferred. Missing values are returned as null and shown as unavailable.",
            "Routing advice only uses plans that have provider_key and real quota/renewal fields in data/model-subscriptions.json.",
        ],
    }


def choose_provider_for_route(route: str, default_provider: str, available_providers: List[str], ledger_data: Optional[Dict[str, Any]] = None) -> str:
    ledger = ledger_data if isinstance(ledger_data, dict) else build_subscription_ledger()
    available = set(available_providers)
    avoid = {item.get("provider_key") for item in ledger.get("routing_advice", {}).get("avoid", [])}
    if default_provider not in avoid:
        return default_provider
    for item in ledger.get("routing_advice", {}).get("preferred", []):
        provider_key = item.get("provider_key")
        if provider_key in available and provider_key != default_provider:
            return provider_key
    return default_provider


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect model subscription and quota ledger.")
    parser.add_argument("--json", action="store_true", help="print full JSON")
    args = parser.parse_args()
    data = build_subscription_ledger()
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0
    totals = data.get("totals", {})
    print(f"plans={totals.get('plans', 0)} alerts={totals.get('alerts', 0)} config={data.get('config_path')}")
    for plan in data.get("plans", []):
        remaining = plan.get("quota_remaining_pct")
        remaining_text = "unavailable" if remaining is None else f"{remaining:.1f}%"
        print(f"{plan.get('name')}: status={plan.get('status')} renewal={plan.get('renewal_at')} remaining={remaining_text}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
