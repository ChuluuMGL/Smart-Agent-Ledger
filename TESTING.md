# Testing Matrix

This matrix records what has been checked for `Smart Agent Ledger`. Keep it conservative: only mark a source or runtime as verified after a realistic run, not just because code paths exist.

## Status Legend

| Status | Meaning |
|---|---|
| `verified` | Tested with automated tests or a realistic local run. |
| `demo-verified` | Verified in anonymous demo mode only. |
| `unit-tested` | Covered by unit/API tests, but not verified against a live external service in this release. |
| `expected-compatible` | Code and docs describe the integration, but a fresh end-to-end public run is still needed. |
| `not-supported` | The product intentionally does not claim support. |

## Current Release Checks

| Check | Status | Evidence |
|---|---|---|
| Python test suite | verified | `python -m pytest -q` returned `411 passed`. |
| Dashboard JavaScript syntax | verified | `node --check static/dashboard.js` passed. |
| Python module compile | verified | `python -m py_compile gateway.py fleet_ledger.py agent_ledger_server.py subscription_ledger.py` passed. |
| Git whitespace check | verified | `git diff --check` passed before public push. |
| Public sanitization scan | verified | Scanned for private paths, internal repo names, real machine names, and private IP fragments before release. |
| Demo mode | demo-verified | `SMART_AGENT_LEDGER_DEMO_MODE=1` returns anonymized `/agent-ledger`, `/fleet-ledger`, `/subscription-ledger`, and `/feishu-reminder` data. |

## Agent Data Source Matrix

| Source | Status | Token Quality | Notes |
|---|---|---|---|
| OpenAI Codex session JSONL | unit-tested | real | Collector reads token-count events and session metadata. |
| Claude Code session JSONL | unit-tested | real | Collector reads `message.usage` style records where available. |
| Hermes SQLite | unit-tested | real | Collector expects a readable local SQLite state database. |
| OpenClaw session index | unit-tested | real | Collector reads local session index JSON. |
| LiteLLM SpendLogs | expected-compatible | real | Requires a configured PostgreSQL source. |
| Trae git snapshots | unit-tested | estimated | Uses turn/snapshot heuristics, not provider billing data. |
| Antigravity logs | unit-tested | estimated | Uses heartbeat/log analysis, not provider billing data. |
| Cursor workspaceStorage | unit-tested | metadata only | Useful for presence and project metadata, not token totals. |
| n8n SQLite over SSH | unit-tested | activity only | Counts workflow activity unless LLM calls also pass through the gateway. |

## Runtime Modes

| Mode | Status | Smoke Test |
|---|---|---|
| Demo dashboard | demo-verified | Start with `SMART_AGENT_LEDGER_DEMO_MODE=1` and open `/ui`. |
| Local ledger API | unit-tested | `GET /agent-ledger?days=30&limit=120`. |
| Team-node aggregation | unit-tested | `GET /fleet-ledger?days=30&limit=120` with fake node responses and cache cases. |
| Read-only collector | unit-tested | Start `agent_ledger_server.py` and call `/health` and `/agent-ledger`. |
| Subscription ledger | unit-tested | `GET /subscription-ledger` with example config. |
| Feishu/Lark reminders | unit-tested | Builds alert text and payloads; live delivery requires user credentials. |
| Optional gateway proxy | unit-tested | Routing and dry-run behavior are covered; live provider calls require API keys. |
| Docker runtime | expected-compatible | Dockerfile and compose are included; run a fresh container smoke test before tagging a release. |

## Recommended Smoke Tests

### Demo Dashboard

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
SMART_AGENT_LEDGER_DEMO_MODE=1 uvicorn gateway:app --host 127.0.0.1 --port 8001 --no-access-log
open http://127.0.0.1:8001/ui
```

Pass condition:

- The dashboard loads without local config files.
- KPI cards use anonymous sample data.
- Team nodes are shown as demo nodes only.
- No local paths, usernames, private machine names, or private IPs appear.

### Local API

```bash
curl http://127.0.0.1:8001/health
curl "http://127.0.0.1:8001/agent-ledger?days=30&limit=120"
curl "http://127.0.0.1:8001/fleet-ledger?days=30&limit=120"
curl http://127.0.0.1:8001/subscription-ledger
```

Pass condition:

- `/health` returns `ok`.
- Ledger endpoints return JSON.
- Missing or partial token sources are explained instead of silently converted to `0`.

### Read-only Collector

```bash
python agent_ledger_server.py --host 127.0.0.1 --port 8002
curl http://127.0.0.1:8002/health
curl "http://127.0.0.1:8002/agent-ledger?days=30&limit=120"
```

Pass condition:

- The collector starts without the main gateway.
- It exposes read-only ledger data only.
- It does not proxy model requests.

### Final Release Check

```bash
python -m pytest -q
node --check static/dashboard.js
python -m py_compile gateway.py fleet_ledger.py agent_ledger_server.py subscription_ledger.py
git diff --check
```

Pass condition:

- Tests pass.
- Dashboard JavaScript parses.
- Python modules compile.
- No whitespace errors are introduced.

## Known Gaps

- No hosted demo site yet.
- No one-command public collector installer yet.
- Docker should be smoke-tested in a clean environment before a tagged release.
- Very large long-running ledgers should move toward daily rollups for faster 30/90-day switching.
- Team-node config still uses the legacy-compatible file name `company-agent-nodes.json`; the product UI should continue using the reader-facing term "team nodes".
