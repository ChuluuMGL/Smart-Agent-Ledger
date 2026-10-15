# Security Policy

> This project is archived and unmaintained. Security reports will not be acted on. Fork the repository if you need fixes.

Smart Agent Ledger is intended for trusted local machines and private networks. It reads local AI tool logs, usage ledgers, subscription metadata, and optional Fleet node data. Treat the dashboard and JSON endpoints as operationally sensitive.

## Supported Deployment Boundary

- Keep the main gateway (`8001`) on localhost, a trusted LAN, VPN, or another protected network.
- Keep collector-only nodes (`8002`) on a trusted LAN or VPN.
- Do not expose `8001` or `8002` directly to the public internet.
- Add an authentication proxy, firewall rule, VPN, or equivalent access control before using this outside a trusted network.

## Default Network Policy

Since the final (archival) update, everything defaults to local-only:

- `run.sh` binds the gateway to `127.0.0.1` (override with `GATEWAY_HOST`).
- The Docker image listens on `0.0.0.0` inside the container. `docker-compose.yml` publishes it on `127.0.0.1:${SMART_AGENT_LEDGER_PORT:-8001}` only.
- If neither `GATEWAY_API_KEY` nor `authorized_networks` is configured, the gateway serves only loopback clients (`127.0.0.0/8`, `::1`) and requires a loopback `Host` header (`localhost`, `*.localhost`, or a loopback IP), which blocks DNS rebinding. Any other client gets `403` with instructions. `/health` stays public.
- Inside Docker, traffic through a loopback-published port arrives from the bridge gateway. `SMART_AGENT_LEDGER_TRUST_DOCKER_BRIDGE=1` (set by compose) treats the container's default gateway IP as local. You can also set it to an explicit comma-separated IP list. Turn it off (`0`) when you publish the port on the LAN: with Docker Desktop or the userland proxy, LAN clients can also appear as the bridge gateway.
- CORS is disabled by default. Allow specific origins with `SMART_AGENT_LEDGER_CORS_ORIGINS` (comma-separated). Avoid `*`.
- Browser `POST`/`PUT`/`PATCH`/`DELETE` requests whose `Origin` is neither same-origin nor listed in `SMART_AGENT_LEDGER_CORS_ORIGINS` are rejected (CSRF guard). Requests without an `Origin` header (curl, SDKs, agents) are not affected.
- `X-API-Key` is compared with `hmac.compare_digest`.
- The collector (`agent_ledger_server.py`, `8002`) serves `/agent-ledger` only to loopback clients and to IPs in `SMART_AGENT_LEDGER_COLLECTOR_ALLOWED_NETWORKS`. The launchd installer binds it to `127.0.0.1` unless that allowlist is set.

### Enabling LAN / Fleet mode

1. On the main node, set `GATEWAY_API_KEY` in `keys.env` to a long random value (`openssl rand -hex 32`), and optionally list trusted CIDRs in `authorized_networks` in `data/company-agent-nodes.json`.
2. Start with `GATEWAY_HOST=0.0.0.0 ./run.sh`. With compose, set `SMART_AGENT_LEDGER_BIND=0.0.0.0` and `SMART_AGENT_LEDGER_TRUST_DOCKER_BRIDGE=0`.
3. On each collector, run the onboarding script with `--main http://<main-ip>:8001 --api-key <key>`. The main node's IP is added to `SMART_AGENT_LEDGER_COLLECTOR_ALLOWED_NETWORKS` automatically. Add any other address the main node uses to reach the collector.

Once auth is configured, every non-`/health` request needs the API key or an allowlisted IP, including requests from localhost.

Do not put the gateway behind a reverse proxy on the same machine while running without auth. Every proxied request would come from `127.0.0.1` and count as local.

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

It does not proxy LLM requests, but `/agent-ledger` can reveal local usage metadata such as agents, projects, sessions, token counts, and estimated costs. It only serves loopback clients and `SMART_AGENT_LEDGER_COLLECTOR_ALLOWED_NETWORKS`. Keep that allowlist as narrow as possible, ideally just the main node's IP as `/32`.

Fleet supports stale-cache fallback so a temporary collector outage does not break the dashboard. Cached data should still be treated as sensitive because it contains prior successful ledger responses.

## Reporting Vulnerabilities

The repository is archived, so reports will not be triaged. If you maintain a fork, use your fork's private advisory channel. Do not post secrets, real logs, or personal ledger exports in public issues.

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
