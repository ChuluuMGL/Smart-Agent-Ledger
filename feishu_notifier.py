#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import os
import pathlib
from typing import Any, Dict, List, Optional

import httpx

from subscription_ledger import build_subscription_ledger
from utils import load_env_file


PROJECT_ROOT = pathlib.Path(__file__).resolve().parent
CONFIG_PATH = PROJECT_ROOT / "data" / "feishu-reminder.json"
ENV_PATH = PROJECT_ROOT / ".secrets" / "feishu.env"

TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
MESSAGE_URL = "https://open.feishu.cn/open-apis/im/v1/messages"
DEFAULT_RENEWAL_WARNING_DAYS = 7


def _load_json(path: pathlib.Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError) as exc:
        return {"_load_error": str(exc)}
    return data if isinstance(data, dict) else {"_load_error": "root must be object"}


def load_config(path: pathlib.Path = CONFIG_PATH) -> Dict[str, Any]:
    config = _load_json(path)
    env_values = load_env_file(ENV_PATH)
    return {
        **config,
        "app_id": os.getenv("FEISHU_APP_ID") or env_values.get("FEISHU_APP_ID") or config.get("app_id"),
        "app_secret": os.getenv("FEISHU_APP_SECRET") or env_values.get("FEISHU_APP_SECRET"),
        "receive_id_type": os.getenv("FEISHU_RECEIVE_ID_TYPE") or env_values.get("FEISHU_RECEIVE_ID_TYPE") or config.get("receive_id_type"),
        "receive_id": os.getenv("FEISHU_RECEIVE_ID") or env_values.get("FEISHU_RECEIVE_ID") or config.get("receive_id"),
        "recipient_name": os.getenv("FEISHU_RECIPIENT_NAME") or env_values.get("FEISHU_RECIPIENT_NAME") or config.get("recipient_name"),
    }


def _status_label(status: Optional[str]) -> str:
    labels = {
        "ok": "正常",
        "renewal_due": "需续费",
        "renewal_soon": "临近续费",
        "quota_low": "额度偏低",
        "quota_unknown": "额度未知",
    }
    return labels.get(status or "", status or "未知")


def _money(plan: Dict[str, Any]) -> str:
    amount = plan.get("billing_amount")
    currency = plan.get("billing_currency")
    period = plan.get("billing_period")
    if amount is None or not currency:
        return "费用不可用"
    period_labels = {"month": "月", "month_reference": "月参考", "quarter": "季", "year": "年", "usage": "按量"}
    suffix = period_labels.get(period, period or "")
    amount_text = str(int(amount)) if float(amount).is_integer() else f"{float(amount):.2f}"
    return f"{currency} {amount_text}" + (f"/{suffix}" if suffix else "")


def _short_time(value: Optional[str]) -> str:
    if not value:
        return "不可用"
    return value.replace("T", " ")[:16]


def _clamped_int(value: Any, default: int, minimum: int = 0, maximum: int = 365) -> int:
    try:
        parsed = int(value)
    except (ValueError, TypeError):
        return default
    return max(minimum, min(maximum, parsed))


def effective_warning_days(config: Dict[str, Any], plan: Dict[str, Any]) -> int:
    plan_days = (config.get("plan_warning_days") or {}).get(plan.get("id"))
    if plan_days is not None:
        return _clamped_int(plan_days, DEFAULT_RENEWAL_WARNING_DAYS)
    return _clamped_int(config.get("default_renewal_warning_days"), DEFAULT_RENEWAL_WARNING_DAYS)


def _reminder_start_date(renewal_at: Optional[str], warning_days: int) -> Optional[str]:
    if not renewal_at:
        return None
    try:
        renewal = dt.datetime.fromisoformat(str(renewal_at).replace("Z", "+00:00"))
        return (renewal.date() - dt.timedelta(days=warning_days)).isoformat()
    except (ValueError, TypeError):
        return None


def build_reminder_windows() -> List[Dict[str, Any]]:
    config = load_config()
    ledger = build_subscription_ledger()
    windows = []
    for plan in ledger.get("plans", []):
        if plan.get("renewal_at") is None:
            continue
        warning_days = effective_warning_days(config, plan)
        days_to_renewal = plan.get("days_to_renewal")
        will_remind = days_to_renewal is not None and days_to_renewal <= warning_days
        windows.append(
            {
                "id": plan.get("id"),
                "name": plan.get("name"),
                "renewal_at": plan.get("renewal_at"),
                "days_to_renewal": days_to_renewal,
                "warning_days": warning_days,
                "remind_start_date": _reminder_start_date(plan.get("renewal_at"), warning_days),
                "will_remind": will_remind,
            }
        )
    return windows


def build_configured_alerts(include_all: bool = False) -> List[Dict[str, Any]]:
    config = load_config()
    ledger = build_subscription_ledger()
    if include_all:
        rows = list(ledger.get("plans") or [])
    else:
        rows = []
        statuses = set(config.get("alert_statuses") or ["renewal_due", "renewal_soon", "quota_low", "quota_unknown"])
        for plan in ledger.get("plans", []):
            days_to_renewal = plan.get("days_to_renewal")
            if days_to_renewal is not None:
                warning_days = effective_warning_days(config, plan)
                if days_to_renewal <= 0 and "renewal_due" in statuses:
                    rows.append(plan)
                    continue
                if 0 < days_to_renewal <= warning_days and "renewal_soon" in statuses:
                    rows.append(plan)
                    continue
            if plan.get("status") in {"quota_low", "quota_unknown"} and plan.get("status") in statuses:
                rows.append(plan)
    normalized = []
    for plan in rows:
        enriched = dict(plan)
        enriched["feishu_warning_days"] = effective_warning_days(config, plan) if plan.get("renewal_at") else None
        normalized.append(enriched)
    return normalized


def build_alert_text(include_all: bool = False) -> str:
    ledger = build_subscription_ledger()
    totals = ledger.get("totals") or {}
    rows = build_configured_alerts(include_all=include_all)

    lines = [
        "Smart Agent Ledger 订阅与额度提醒",
        f"生成时间：{_short_time(ledger.get('generated_at'))}",
        f"计划：{totals.get('plans', 0)} 个，飞书提醒：{len(rows)} 个",
    ]
    if not rows:
        lines.append("当前没有触发提醒的真实订阅或额度项。")
        return "\n".join(lines)

    for plan in rows:
        remaining = plan.get("quota_remaining_pct")
        remaining_text = "剩余额度不可用" if remaining is None else f"剩余额度 {float(remaining):.1f}%"
        renewal = _short_time(plan.get("renewal_at"))
        reset = _short_time(plan.get("reset_at"))
        warning = plan.get("feishu_warning_days")
        warning_text = "" if warning is None else f"; 提前 {warning} 天提醒"
        lines.append(
            f"- {plan.get('name')}: {_status_label(plan.get('status'))}; "
            f"{_money(plan)}; 续费/到期 {renewal}{warning_text}; 重置 {reset}; {remaining_text}"
        )
    return "\n".join(lines)


def get_tenant_access_token(app_id: str, app_secret: str) -> str:
    response = httpx.post(
        TOKEN_URL,
        json={"app_id": app_id, "app_secret": app_secret},
        headers={"Content-Type": "application/json; charset=utf-8"},
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    if data.get("code") != 0:
        raise RuntimeError(f"Feishu token error code={data.get('code')} msg={data.get('msg')}")
    token = data.get("tenant_access_token")
    if not token:
        raise RuntimeError("Feishu token response missing tenant_access_token")
    return token


def send_text_message(token: str, receive_id_type: str, receive_id: str, text: str) -> Dict[str, Any]:
    response = httpx.post(
        MESSAGE_URL,
        params={"receive_id_type": receive_id_type},
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        },
        json={
            "receive_id": receive_id,
            "msg_type": "text",
            "content": json.dumps({"text": text}, ensure_ascii=False),
        },
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    if data.get("code") != 0:
        raise RuntimeError(f"Feishu message error code={data.get('code')} msg={data.get('msg')}")
    return data


def send_configured_alert(include_all: bool = False, text: Optional[str] = None) -> Dict[str, Any]:
    config = load_config()
    missing = {key: missing for key, missing in missing_send_fields(config).items() if missing}
    if missing:
        return {"sent": False, "missing": list(missing.keys())}
    body = text or build_alert_text(include_all=include_all)
    token = get_tenant_access_token(str(config["app_id"]), str(config["app_secret"]))
    response = send_text_message(token, str(config["receive_id_type"]), str(config["receive_id"]), body)
    return {"sent": True, "message": response.get("data")}


def missing_send_fields(config: Dict[str, Any]) -> Dict[str, bool]:
    return {
        "app_id": not bool(config.get("app_id")),
        "app_secret": not bool(config.get("app_secret")),
        "receive_id_type": not bool(config.get("receive_id_type")),
        "receive_id": not bool(config.get("receive_id")),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Send Smart Agent Ledger subscription reminders to Feishu.")
    parser.add_argument("--send", action="store_true", help="send the reminder to Feishu")
    parser.add_argument("--all", action="store_true", help="include all subscription plans, not only alerts")
    parser.add_argument("--text", help="send a custom text message instead of generated alerts")
    parser.add_argument("--json", action="store_true", help="print machine-readable status")
    args = parser.parse_args()

    config = load_config()
    text = args.text or build_alert_text(include_all=args.all)
    missing = {key: missing for key, missing in missing_send_fields(config).items() if missing}

    if not args.send:
        result = {"ready_to_send": not bool(missing), "missing": list(missing.keys()), "text": text}
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else text)
        if missing and not args.json:
            print("未发送：缺少 " + ", ".join(missing.keys()))
        return 0

    if missing:
        print(json.dumps({"sent": False, "missing": list(missing.keys())}, ensure_ascii=False, indent=2))
        return 2

    result = send_configured_alert(include_all=args.all, text=args.text)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
