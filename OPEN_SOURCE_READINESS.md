# Open Source Readiness

This repository is currently optimized for private local use. Before publishing
any public repository, use this checklist to keep private data, machine names,
and internal deployment assumptions out of the release.

## Current Target

- Current private-product score: 75-80/100 after demo mode and Fleet stability work.
- Current public-release score: about 70/100.
- Public-release target: 80/100 after the checklist below is complete.

## Safe Public Positioning

Use this positioning for the public repository:

> Local-first AI agent usage ledger for individuals and small teams.

Do not position the public project as a full replacement for LiteLLM, Portkey,
Helicone, or Langfuse. The strongest differentiation is local AI coding tool
usage collection plus team-node rollups.

## Required Before Public Push

- Run demo mode and confirm the dashboard works without local logs:
  `SMART_AGENT_LEDGER_DEMO_MODE=1 uvicorn gateway:app --host 127.0.0.1 --port 8001 --no-access-log`
- Verify README screenshots and examples use anonymous demo nodes only.
- Remove real machine names, user names, private IPs, shared directory paths, SSH hosts,
  and local ledger export names from public-facing docs.
- Keep real configs untracked:
  `keys.env`, `.env`, `.secrets/*`, `data/company-agent-nodes.json`,
  `data/model-subscriptions.json`, `data/feishu-reminder.json`,
  `data/fleet-exports/*`, and runtime logs.
- Keep only `data/*.example.json` and demo-generated examples public.
- Run the release checks:
  `python -m pytest -q`
  `node --check static/dashboard.js`
  `python -m py_compile gateway.py fleet_ledger.py agent_ledger_server.py subscription_ledger.py`
  `git diff --check`
- Review `SECURITY.md` and confirm it still describes the public threat model.

## Public Repository Model

Keep the private and public repositories separate:

- Private repo: complete internal product, real deployment docs, private branches.
- Public repo: sanitized code, example configs, demo mode, public docs.

Do not use branch visibility as a privacy boundary. GitHub repository visibility
is repository-level, not branch-level.

## Not Yet Public-Ready

These items are valuable but not required for the first public release:

- One-command macOS collector installer with clearer status output.
- Daily rollups for very large local ledgers.
- Optional OpenTelemetry export.
- Public screenshots generated from demo mode.
- A short website or README animation showing the dashboard in demo mode.
