# Smart Agent Ledger

> **面向开发者和小团队的本地优先 AI Agent 用量账本**
>
> 一个开源仪表盘，用来统一追踪 Codex、Claude Code、Cursor、Trae、Hermes、OpenClaw、LiteLLM 等 AI 编程工具的 token、成本、订阅、项目和团队节点使用情况。
>
> 由 **Chuluu** 创建和维护。

中文 | [English](README.md)

[![Local First](https://img.shields.io/badge/local--first-agent--ledger-0E5E43)](#为什么需要它)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](./pyproject.toml)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/tests-412%20passing-green)](./TESTING.md)
[![License: AGPL](https://img.shields.io/badge/license-AGPL--3.0-blue)](./LICENSE)
[![Security](https://img.shields.io/badge/security-local--network-orange)](./SECURITY.md)

[Demo 快速体验](#3-分钟上手) | [测试矩阵](./TESTING.md) | [安全说明](./SECURITY.md) | [开源清单](./OPEN_SOURCE_READINESS.md)

![Smart Agent Ledger demo dashboard](./assets/dashboard-demo.png)

---

## 为什么需要它

AI 编程工作越来越分散：Codex 有一套记录，Claude Code 有一套记录，Cursor 可能只有元数据，有些工具甚至没有清晰的成本视图。实际使用时，很难回答这些问题：

- 最近一周团队到底用了多少 token？
- 哪些 Agent、项目或模型在消耗成本？
- 哪些数字是真实 token，哪些是估算、过期或仅有元数据？
- 哪些订阅快到续费日或额度压力区间？
- 哪些机器已接入，哪些节点过期或缺失？

**Smart Agent Ledger** 的目标是把 AI Agent 用量变成可信、可解释、可本地运行的账本，而不是把本机日志上传到第三方服务。

它也包含一个可选的轻量 OpenAI-compatible gateway，但公开版主定位是本地优先的用量账本。

---

## 3 分钟上手

先用匿名 demo 数据运行仪表盘。Demo mode 不会读取本机真实 Agent 日志、订阅文件、API key 或团队节点配置。

```bash
git clone https://github.com/ChuluuMGL/Smart-Agent-Ledger.git
cd Smart-Agent-Ledger
python3 -m venv venv
source venv/bin/activate
pip install -U pip
pip install -r requirements.txt
SMART_AGENT_LEDGER_DEMO_MODE=1 uvicorn gateway:app --host 127.0.0.1 --port 8001 --no-access-log
open http://127.0.0.1:8001/ui
```

本地正式运行：

```bash
cp keys.env.example keys.env
chmod 600 keys.env
./run.sh
```

Docker：

```bash
docker build -t smart-agent-ledger .
docker run -p 8001:8001 -v "$PWD/data:/app/data" smart-agent-ledger
```

---

## 它能做什么

| 能力 | 内容 |
|---|---|
| 本地 Agent 账本 | 读取 AI 编程工具产生的 JSONL、SQLite、日志和事件文件。 |
| Token 可信度 | 区分真实 token、估算 token、仅元数据、过期数据和缺失数据。 |
| 成本估算 | 根据 `data/model-pricing.json` 在模型和 token 可用时估算成本。 |
| 项目归因 | 按项目、路径、别名、workflow 名称或请求 metadata 聚合。 |
| 团队节点汇总 | 通过 HTTP collector 或共享账本文件聚合多台机器。 |
| 订阅提醒 | 跟踪续费窗口、额度压力和提醒状态。 |
| Demo mode | 使用匿名样例数据展示完整仪表盘。 |
| 可选 gateway | 提供 OpenAI-compatible 代理、关键词路由、fallback chain 和请求计量。 |

---

## 数据来源

| Agent / 来源 | 数据源 | Token 质量 |
|---|---|---|
| OpenAI Codex | Session JSONL 和 token-count events | 真实 |
| Claude Code | Session JSONL `message.usage` 记录 | 真实 |
| Hermes | SQLite `state.db` | 真实 |
| OpenClaw | Session index JSON | 真实 |
| LiteLLM | PostgreSQL SpendLogs，需自行配置 | 真实 |
| Trae | Git snapshot tags 和 turn 估算 | 估算 |
| Antigravity | `cloudcode.log` heartbeat 分析 | 估算 |
| Cursor | `workspaceStorage` 元数据 | 仅元数据 |
| n8n | 可选 SSH 读取 SQLite workflow 执行数据 | 仅活动 |

仪表盘默认保守处理：没有可信 token 的记录不会被静默改成 `0`，过期团队节点也会明确标记。

---

## 产品工作流

| 阶段 | 目的 | 产物 |
|---|---|---|
| 1. 采集 | 读取本机工具账本和可选 gateway 事件。 | 原始 session 与活动记录。 |
| 2. 标准化 | 把不同来源字段转换成统一 session 模型。 | Agent、项目、任务、模型、token、成本、时间。 |
| 3. 可信度判断 | 标记真实、估算、过期、仅元数据或不可用。 | 可用于 KPI 的可信输入。 |
| 4. 聚合 | 生成 Agent、项目、模型、任务、趋势和团队节点汇总。 | Dashboard 与 JSON API。 |
| 5. 解释 | 暴露缺失来源、过期 collector、token 质量备注。 | 可排错的数据说明。 |
| 6. 报告 | 导出月度用量摘要和订阅提醒。 | 本地 Markdown 报告和提醒 payload。 |

这个工作流优先追求“数据真实可解释”，而不是展示好看的虚高数字。

---

## 工作模式

| 模式 | 适用情况 | 行为 |
|---|---|---|
| `demo` | 首次体验、README 截图、公开演示。 | 只使用匿名样例数据。 |
| `local` | 单台开发机器。 | 读取本机 Agent 账本和本地配置。 |
| `team` | 多台可信机器。 | 拉取 collector 节点，并标记过期或不可达来源。 |
| `gateway` | 可选 API 代理与请求计量。 | 记录 OpenAI-compatible 请求和 provider fallback 事件。 |
| `reporting` | 月度或运营复盘。 | 生成本地用量报告和订阅提醒。 |

---

## API

| Endpoint | Method | 说明 |
|---|---|---|
| `/ui` | GET | 单页仪表盘。 |
| `/health` | GET | 服务健康检查。 |
| `/agent-ledger` | GET | 本机多 Agent 用量账本。 |
| `/fleet-ledger` | GET | 团队节点聚合账本。 |
| `/subscription-ledger` | GET | 订阅续费与额度状态。 |
| `/reports/monthly-usage` | POST | 本地 Markdown 月报。 |
| `/config` | GET | 路由与关键词配置。 |
| `/stats` | GET | Gateway 请求计数。 |
| `/v1/models` | GET | OpenAI-compatible 模型列表。 |
| `/v1/chat/completions` | POST | 可选 OpenAI-compatible chat proxy。 |
| `/v1/chat/completions/dry-run` | POST | 只诊断路由，不转发请求。 |

除 `/ui` 外，接口均返回 JSON。

---

## 配置文件

运行时配置位于 `data/`，真实配置会被 git 忽略；仓库只保留安全样例。

| 文件 | 用途 | 样例 |
|---|---|---|
| `keys.env` | Provider key 和 API auth key。 | `keys.env.example` |
| `model-pricing.json` | 成本估算价格表。 | 已包含 |
| `routing-keywords.json` | 可选关键词路由规则。 | 已包含 |
| `model-subscriptions.json` | 订阅额度和续费追踪。 | `model-subscriptions.example.json` |
| `company-agent-nodes.json` | 团队节点 endpoint 和可选 n8n SSH 来源。 | `company-agent-nodes.example.json` |
| `feishu-reminder.json` | 飞书 / Lark 提醒配置。 | `feishu-reminder.example.json` |
| `project-aliases.json` | 项目归因别名。 | `project-aliases.example.json` |

`company-agent-nodes.json` 是兼容历史版本的文件名；产品 UI 和文档里统一称为 **团队节点**。

---

## 包含文件

| 文件 / 目录 | 用途 |
|---|---|
| [`gateway.py`](./gateway.py) | FastAPI app、dashboard 路由、可选 gateway endpoint 和缓存编排。 |
| [`agent_ledger.py`](./agent_ledger.py) | 本机 Agent 采集编排和账本汇总。 |
| [`agent_collectors.py`](./agent_collectors.py) | 各 AI 编程工具与 gateway 事件的采集器。 |
| [`agent_ledger_server.py`](./agent_ledger_server.py) | 团队节点只读 collector 服务。 |
| [`fleet_ledger.py`](./fleet_ledger.py) | 团队节点聚合、过期缓存处理、n8n 活动采集。 |
| [`subscription_ledger.py`](./subscription_ledger.py) | 订阅与额度账本。 |
| [`usage_report.py`](./usage_report.py) | 本地月度用量报告。 |
| [`feishu_notifier.py`](./feishu_notifier.py) | 飞书 / Lark 提醒 payload 与发送。 |
| [`static/`](./static/) | Dashboard HTML、CSS、JavaScript。 |
| [`data/`](./data/) | 安全样例配置、价格表、路由表。 |
| [`tests/`](./tests/) | 单元测试和 API 行为测试。 |
| [`TESTING.md`](./TESTING.md) | 测试矩阵和 smoke tests。 |
| [`SECURITY.md`](./SECURITY.md) | 安全边界和敏感文件说明。 |
| [`OPEN_SOURCE_READINESS.md`](./OPEN_SOURCE_READINESS.md) | 公私仓库分离与公开发布清单。 |

---

## 测试

```bash
pip install -r requirements.txt
pip install pytest
python -m pytest -q
node --check static/dashboard.js
git diff --check
```

当前公开版本验证：

```text
412 passed
```

详见 [`TESTING.md`](./TESTING.md)。

---

## 新机器一键接入

在新的可信 Mac 上，直接安装只读 collector 并注册到主节点：

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/ChuluuMGL/Smart-Agent-Ledger/main/deploy/bootstrap-collector-node.sh)" -- --main http://<mac-mini-tailscale-ip>:8001 --name "$(hostname -s)"
```

如果主节点 `/admin/nodes` 需要 API key，追加 `--api-key <main-gateway-api-key>`。

这个 bootstrap 会把仓库克隆到 `~/.smart-agent-ledger/app`，安装只读 `8002` 采集服务，检测局域网和 Tailscale 地址，并在传入 `--main` 时注册节点。

---

## 安全边界

Smart Agent Ledger 会读取本机 AI 工具日志，并可能通过 HTTP 暴露用量摘要。建议只运行在 localhost、可信局域网或 VPN 内，除非你已经增加自己的认证和网络控制。

不要提交：

- `keys.env`、`.env`、`.secrets/*`
- `data/company-agent-nodes.json`
- `data/model-subscriptions.json`
- `data/feishu-reminder.json`
- `data/fleet-exports/*`
- runtime logs、本地缓存文件、私有机器路径

不要把 `8001` 或 `8002` 直接暴露到公网。

更多见 [`SECURITY.md`](./SECURITY.md)。

---

## Roadmap

| 优先级 | 事项 | 价值 |
|---|---|---|
| P0 | 每个 KPI 都显示更清晰的数据可信标签。 | 避免用户把过期或部分总量误认为当前真实总量。 |
| P0 | 新机器一条命令安装 collector。 | 已提供 `deploy/bootstrap-collector-node.sh`，后续需要更多真实机器反馈。 |
| P1 | 为超大本地账本做 daily rollup。 | 让 30/90 天切换在长期使用机器上仍然快速。 |
| P1 | 公开 demo 截图和简短 walkthrough GIF。 | 提升开源可信度和 adoption。 |
| P2 | 可选 OpenTelemetry 或 Prometheus export。 | 接入已有 observability 系统。 |
| P2 | 独立 docs site。 | 比单 README 更适合安装和排错。 |

---

## License

本项目采用 **GNU Affero General Public License v3.0**。

完整内容见 [`LICENSE`](./LICENSE)。

---

## 作者

由 **Chuluu** 创建和维护。

- GitHub: [ChuluuMGL](https://github.com/ChuluuMGL)
- Notice: [`NOTICE`](./NOTICE)
