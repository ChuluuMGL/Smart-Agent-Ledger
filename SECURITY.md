# Security Policy

Smart Agent Ledger is intended for trusted local machines and private networks. It reads local AI tool logs, usage ledgers, subscription metadata, and optional Fleet node data. Treat the dashboard and JSON endpoints as operationally sensitive.

## Supported Deployment Boundary

- Keep the main gateway (`8001`) on localhost, a trusted LAN, VPN, or another protected network.
- Keep collector-only nodes (`8002`) on a trusted LAN or VPN.
- Do not expose `8001` or `8002` directly to the public internet.
- Add an authentication proxy, firewall rule, VPN, or equivalent access control before using this outside a trusted network.

## Sensitive Files

Do not commit or share these files:

- `keys.env`, `.env`, `.env.local`, `secrets.env`
- `.secrets/*` except safe example files
- `data/company-agent-nodes.json`
- `data/feishu-reminder.json`
- `data/model-subscriptions.json`
- `data/fleet-exports/*`
- runtime logs, pid files, and local cache files

The repository `.gitignore` excludes these by default. Keep real API keys, Feishu credentials, SSH private keys, local hostnames, and private IPs out of examples and documentation.

## Fleet Collector Notes

The read-only `agent_ledger_server.py` service exposes:

- `GET /health`
- `GET /agent-ledger`

It does not proxy LLM requests, but `/agent-ledger` can reveal local usage metadata such as agents, projects, sessions, token counts, and estimated costs. Run it only on machines and networks you trust.

Fleet supports stale-cache fallback so a temporary collector outage does not break the dashboard. Cached data should still be treated as sensitive because it contains prior successful ledger responses.

## Reporting Vulnerabilities

If this repository is private, report issues through the private project channel or by opening a private GitHub security advisory if available. Do not post secrets, real logs, or personal ledger exports in public issues.

When reporting a vulnerability, include:

- A short description of the issue
- A minimal reproduction path
- Affected endpoint, script, or configuration file
- Whether credentials, logs, or local ledger data could be exposed

## Development Checks

Before pushing changes that touch deployment, Fleet, auth, or logging, run:

```bash
python -m pytest -q
node --check static/dashboard.js
git diff --check
```

Also scan changed files for secrets and private infrastructure details before committing.
