# Smart Agent Ledger

> **Local-first AI agent usage ledger with a lightweight LLM gateway** — track tokens, costs, subscriptions, and team-node usage across AI coding tools from one dashboard.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688) ![Tests](https://img.shields.io/badge/tests-400%2B%20passing-green) ![License](https://img.shields.io/badge/license-AGPL--3.0-blue)

---

## Why This Exists

If you use multiple AI coding tools (Claude Code, Codex, Cursor, Trae, etc.), you have **zero visibility** into total token usage and costs across all of them. Each tool has its own dashboard — or none at all.

**Smart Agent Ledger solves this in two ways:**

1. **Agent Usage Ledger** — Reads local databases, JSONL logs, and SQLite stores from AI coding tools to give you a unified view of sessions, tokens, projects, and estimated costs.
2. **Lightweight Gateway** — Optionally routes API requests based on content analysis, subscription quotas, and fallback chains.

## Features

### 🤖 Multi-Agent Data Collection

| Agent | Data Source | Tokens |
|-------|-----------|--------|
| OpenAI Codex | Session JSONL + token_count events | ✅ Real |
| Claude Code | Session JSONL (message.usage) | ✅ Real |
| Hermes | SQLite state.db | ✅ Real |
| Trae | Git snapshot tags (turn estimation) | ⚡ Estimated |
| Antigravity | cloudcode.log heartbeat analysis | ⚡ Estimated |
| OpenClaw | Session index JSON | ✅ Real |
| Cursor | workspaceStorage state.vscdb | ❌ Metadata only |
| LiteLLM | PostgreSQL SpendLogs | ✅ Real (if configured) |

### 🔀 Optional Smart Routing

- **Content-aware keyword routing** — analyzes message text to classify as coding, reasoning, quality, or local
- **Subscription-aware** — avoids providers with low remaining quota or upcoming renewal
- **Automatic fallback chains** — if the primary provider fails, tries the next in chain
- **Hot-reloadable keywords** — update routing rules via JSON config or API without restart

### 💰 Cost Estimation

- Model pricing table with CNY/USD conversion
- Per-request cost estimation using input/output token counts
- Automatic cost fill for sessions with tokens but no price
- Cost trends in the dashboard (token / cost / combined views)

### 📊 Real-Time Dashboard

Single-page web dashboard showing:
- KPI cards (total sessions, tokens, active agents, costs)
- Agent inventory with collector status
- Token trend chart with agent breakdown and cost overlay
- Project rankings, task rankings, **model cost rankings**
- Provider health and request statistics
- Subscription status and renewal reminders
- Fleet view (aggregate across multiple machines)

### 🏢 Fleet Aggregation

Pull agent ledgers from multiple machines on your network for a team-wide view of AI usage.

Fleet supports:
- Full Smart Agent Ledger nodes exposing `/agent-ledger`
- Collector-only read-only nodes running `agent_ledger_server.py` on port `8002`
- shared directory/shared-file handoff via `agent_ledger_file`
- Optional n8n SSH activity-only collection
- HTTP fallback URLs and stale-cache readback for temporary collector outages

### 📬 Feishu (Lark) Alerts

Automated subscription renewal and quota warnings via Feishu bot.

---

## Quick Start

### Prerequisites

- Python 3.9+ (3.13 recommended)
- API keys for at least one LLM provider if you want to proxy real model calls

### Try the Demo Dashboard

Run the dashboard with anonymous sample data. This mode does not read local AI tool logs, subscription files, or Fleet node configuration.

```bash
git clone https://github.com/ChuluuMGL/Smart-Agent-Ledger.git
cd Smart-Agent-Ledger
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
SMART_AGENT_LEDGER_DEMO_MODE=1 uvicorn gateway:app --host 127.0.0.1 --port 8001 --no-access-log
open http://127.0.0.1:8001/ui
```

### Install

```bash
git clone https://github.com/ChuluuMGL/Smart-Agent-Ledger.git
cd Smart-Agent-Ledger
pip install -r requirements.txt
```

### Configure

```bash
# Copy the example keys file and add your API keys
cp keys.env.example keys.env
# Edit keys.env with your real API keys
```

The `keys.env` file supports these keys:

| Variable | Provider |
|----------|----------|
| `DEEPSEEK_API_KEY` | DeepSeek |
| `GLM_API_KEY` | Zhipu / GLM |
| `QWEN_API_KEY` | Qwen / Tongyi |

### Run

```bash
# Start the gateway
uvicorn gateway:app --host 0.0.0.0 --port 8001

# Or use the run script after creating keys.env
./run.sh
```

### Verify

```bash
# Check health
curl http://localhost:8001/health

# Open the dashboard
open http://localhost:8001/ui
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/chat/completions` | POST | OpenAI-compatible chat completions (main proxy) |
| `/v1/chat/completions/dry-run` | POST | Route diagnosis without forwarding |
| `/v1/models` | GET | List available models and routing labels |
| `/agent-ledger` | GET | Multi-agent usage data (sessions, tokens, costs) |
| `/fleet-ledger` | GET | Aggregated data from multiple machines |
| `/reports/monthly-usage` | POST | Generate a local Markdown monthly usage report |
| `/subscription-ledger` | GET | Subscription status and renewal info |
| `/health` | GET | Gateway + provider health check |
| `/stats` | GET | Request statistics |
| `/ui` | GET | Web dashboard |
| `/config` | GET | Current routing configuration |

All endpoints return JSON. The `/v1/chat/completions` endpoint is compatible with any OpenAI SDK.

---

## Configuration Files

All config files live in the `data/` directory (gitignored, examples provided):

| File | Purpose | Example |
|------|---------|---------|
| `keys.env` | API keys (auto-loaded) | `keys.env.example` |
| `model-pricing.json` | Per-model pricing for cost estimation | Included |
| `routing-keywords.json` | Content routing keywords | Included |
| `model-subscriptions.json` | Subscription quota tracking | `model-subscriptions.example.json` |
| `company-agent-nodes.json` | Fleet node endpoints and optional n8n SSH activity sources | `company-agent-nodes.example.json` |
| `feishu-reminder.json` | Feishu alert settings | `feishu-reminder.example.json` |
| `project-aliases.json` | Lightweight project attribution aliases for paths/workflow names | `project-aliases.example.json` |

---

## Architecture

```
┌─────────────┐     ┌──────────────────────────────────────┐
│  AI Clients  │────▶│         Smart Agent Ledger            │
│ (IDEs, CLI)  │     │                                      │
└─────────────┘     │  ┌─────────┐  ┌──────────────────┐  │
                    │  │ Router  │  │  Agent Ledger     │  │
                    │  │ (keywords│  │  (10 collectors) │  │
                    │  │  + subs) │  │                   │  │
                    │  └────┬────┘  └──────────────────┘  │
                    │       │                               │
                    │  ┌────▼────┐  ┌──────────────────┐  │
                    │  │Fallback │  │  Dashboard        │  │
                    │  │ Chain   │  │  (real-time web)  │  │
                    │  └────┬────┘  └──────────────────┘  │
                    │       │                               │
                    └───────┼───────────────────────────────┘
                            │
               ┌────────────┼────────────┐
               ▼            ▼            ▼
         ┌──────────┐ ┌──────────┐ ┌──────────┐
         │ DeepSeek │ │   GLM    │ │   Qwen   │
         └──────────┘ └──────────┘ └──────────┘
```

---

## Cost Tracking

The gateway automatically estimates costs using a built-in pricing table (`data/model-pricing.json`):

```
Total estimated costs across all agents:
┌─────────────┬──────────────┬──────────┐
│ Agent       │ Tokens       │ Est. Cost│
├─────────────┼──────────────┼──────────┤
│ Codex       │ 3.41B        │ $5,159   │
│ Claude Code │ 367M         │ $26      │
│ Antigravity │ 11.1M (est.) │ $53      │
│ Trae        │ 3.68M (est.) │ $2.88    │
│ Hermes      │ 30.2M        │ $0.87    │
│ OpenClaw    │ 204K         │ $0.01    │
├─────────────┼──────────────┼──────────┤
│ TOTAL       │ ~3.83B       │ ~$5,241  │
└─────────────┴──────────────┴──────────┘
```

---

## Deployment

### Docker

```bash
docker build -t smart-agent-ledger .
docker run -p 8001:8001 -v ./data:/app/data smart-agent-ledger
```

---

## Testing

```bash
pip install pytest
python -m pytest tests/ -v
# 400+ tests, runs in about a second on a local dev machine
```

Quick checks used before release:

```bash
python -m pytest -q
node --check static/dashboard.js
git diff --check
```

## Security

This project reads local AI tool logs and may expose usage summaries over HTTP. Keep it on trusted local networks unless you add your own authentication and network controls.

- Do not commit `keys.env`, `.env`, `.secrets/*`, `data/company-agent-nodes.json`, local ledger exports, or runtime logs.
- Do not expose ports `8001` or `8002` directly to the public internet.
- Treat `/agent-ledger` and `/fleet-ledger` as sensitive operational endpoints.

See [SECURITY.md](SECURITY.md) for the full security guidance.

For public-release cleanup, demo-mode verification, and private/public repo
separation, see [OPEN_SOURCE_READINESS.md](OPEN_SOURCE_READINESS.md).

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the **GNU Affero General Public License v3.0** (AGPL-3.0).

- ✅ You can use, study, and modify the code
- ✅ You must open-source any modifications (including network use)
- ❌ You cannot use this code in proprietary software without contributing back

See [LICENSE](LICENSE) for the full license text.

---

## Author

**ChuluuMGL** — [GitHub](https://github.com/ChuluuMGL)

---

## Acknowledgments

Built with [FastAPI](https://fastapi.tiangolo.com/), [uvicorn](https://www.uvicorn.org/), and [httpx](https://www.python-httpx.org/).
