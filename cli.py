#!/usr/bin/env python3
"""
Smart Agent Ledger - 命令行查看状态/统计/配置（无需打开代码即可「可视」）
用法: python3 cli.py [status|stats|config|ledger|subscriptions|logs]
"""
import sys
import json
import urllib.error
import urllib.request
import subprocess
import os

BASE = os.environ.get("GATEWAY_URL", "http://127.0.0.1:8001")

def get(path, timeout=15):
    try:
        with urllib.request.urlopen(f"{BASE}{path}", timeout=timeout) as r:
            return json.loads(r.read().decode())
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, OSError, TimeoutError):
        return None

def main():
    cmd = (sys.argv[1:] or ["status"])[0].lower()
    proj = os.path.dirname(os.path.abspath(__file__))

    if cmd == "status":
        h = get("/health")
        if h is None:
            print("Smart Agent Ledger 未运行（请先 ./run.sh 或 uvicorn 启动）")
            print("  ./run.sh")
            print("  uvicorn gateway:app --host 127.0.0.1 --port 8001")
            return 1
        print("Smart Agent Ledger 运行中")
        print(f"  health: {h}")
        s = get("/stats")
        if s:
            print(f"  总请求: {s.get('total_requests', 0)}, fallback 次数: {s.get('fallbacks', 0)}")
        return 0

    if cmd == "stats":
        s = get("/stats")
        if s is None:
            print("请先启动服务: ./run.sh")
            return 1
        print("=== 请求统计（内存，重启清零）===")
        print(json.dumps(s, indent=2, ensure_ascii=False))
        return 0

    if cmd == "config":
        c = get("/config")
        if c is None:
            print("请先启动服务: ./run.sh")
            return 1
        print("=== 当前路由词表与 provider（只读）===")
        print(json.dumps(c, indent=2, ensure_ascii=False))
        print("\n修改词表/权重: 编辑 gateway.py（词表约 58-64 行，provider 约 19-55 行）")
        return 0

    if cmd == "ledger":
        q = sys.argv[2] if len(sys.argv) > 2 else ""
        path = "/agent-ledger" + (q if q.startswith("?") else "")
        data = get(path)
        if data is None:
            print("请先启动服务: ./run.sh")
            return 1
        totals = data.get("totals", {})
        print("=== Agent 工作台（近 %s 天）===" % data.get("window_days", 30))
        print(
            "Agent: {agents} | 项目: {projects} | 会话/任务: {sessions} | Token: {tokens:,} | 已知金额: ${cost:.4f} | 金额未知会话: {unknown}".format(
                agents=totals.get("agents", 0),
                projects=totals.get("projects", 0),
                sessions=totals.get("sessions", 0),
                tokens=int(totals.get("total_tokens") or 0),
                cost=float(totals.get("known_cost_usd") or 0),
                unknown=totals.get("unknown_cost_sessions", 0),
            )
        )
        print("\n-- 按 Agent --")
        for row in data.get("by_agent", [])[:10]:
            print(
                "{agent}: sessions={sessions}, projects={projects}, tokens={tokens:,}, known_cost=${cost:.4f}, latest={latest}".format(
                    agent=row.get("agent"),
                    sessions=row.get("sessions", 0),
                    projects=len(row.get("projects") or []),
                    tokens=int(row.get("total_tokens") or 0),
                    cost=float(row.get("known_cost_usd") or 0),
                    latest=(row.get("latest_task") or "")[:80],
                )
            )
        print("\n-- 最近会话 --")
        for row in data.get("recent_sessions", [])[:12]:
            print(
                "{time} | {agent} | {project} | {status} | {task} | tokens={tokens:,}".format(
                    time=row.get("ended_at") or row.get("started_at") or "",
                    agent=row.get("agent"),
                    project=row.get("project"),
                    status=row.get("status"),
                    task=(row.get("task") or "")[:90],
                    tokens=int(row.get("total_tokens") or 0),
                )
            )
        return 0

    if cmd in {"subscriptions", "subscription"}:
        data = get("/subscription-ledger")
        if data is None:
            print("请先启动服务: ./run.sh")
            return 1
        totals = data.get("totals", {})
        print("=== 模型订阅与额度 ===")
        print(
            "计划: {plans} | 提醒: {alerts} | 续费提醒: {renewals} | 额度提醒: {quota}".format(
                plans=totals.get("plans", 0),
                alerts=totals.get("alerts", 0),
                renewals=totals.get("renewal_alerts", 0),
                quota=totals.get("quota_alerts", 0),
            )
        )
        print(f"配置: {data.get('config_path')}")
        for plan in data.get("plans", []):
            remaining = plan.get("quota_remaining_pct")
            remaining_text = "不可用" if remaining is None else f"{remaining:.1f}%"
            print(
                "{name}: status={status}, renewal={renewal}, reset={reset}, remaining={remaining}".format(
                    name=plan.get("name"),
                    status=plan.get("status"),
                    renewal=plan.get("renewal_at") or "不可用",
                    reset=plan.get("reset_at") or "不可用",
                    remaining=remaining_text,
                )
            )
        if not data.get("plans"):
            print("尚未录入真实订阅/额度，因此不会显示任何虚拟数字。")
        return 0

    if cmd == "logs":
        log_path = os.path.join(proj, "gateway.log")
        if not os.path.isfile(log_path):
            print("未找到 gateway.log（若用 ./run.sh 前台跑，日志在终端）")
            print("  后台跑: nohup ./run.sh >> gateway.log 2>&1 &")
            return 1
        print("最近 30 行 gateway.log（实时看: tail -f gateway.log）")
        subprocess.run(["tail", "-30", log_path])
        return 0

    print("用法: python3 cli.py [status|stats|config|ledger|subscriptions|logs]")
    return 0

if __name__ == "__main__":
    sys.exit(main())
