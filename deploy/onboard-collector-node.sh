#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NODE_NAME="${NODE_NAME:-$(hostname -s 2>/dev/null || echo "collector-node")}"
LEDGER_PORT="8002"
MAIN_GATEWAY_URL="${MAIN_GATEWAY_URL:-}"
GATEWAY_API_KEY="${GATEWAY_API_KEY:-}"

detect_ip() {
  ipconfig getifaddr en0 2>/dev/null \
    || ipconfig getifaddr en1 2>/dev/null \
    || hostname -I 2>/dev/null | awk '{print $1}' \
    || true
}

detect_tailscale_ip() {
  local candidates=(
    "$(command -v tailscale 2>/dev/null || true)"
    "/opt/homebrew/bin/tailscale"
    "/usr/local/bin/tailscale"
    "/Applications/Tailscale.app/Contents/MacOS/tailscale"
    "/Applications/Tailscale.app/Contents/MacOS/Tailscale"
  )
  for bin in "${candidates[@]}"; do
    [ -n "$bin" ] || continue
    [ -x "$bin" ] || continue
    "$bin" ip -4 2>/dev/null | head -n 1 && return 0
  done
  return 0
}

echo "Installing read-only Agent ledger service..."
"$PROJECT_DIR/deploy/install-agent-ledger-readonly-launchd.sh"

echo "Checking local service..."
if ! curl -fsS "http://127.0.0.1:${LEDGER_PORT}/health" >/dev/null; then
  echo "Read-only service did not respond on 127.0.0.1:${LEDGER_PORT}" >&2
  exit 1
fi
echo "Local health: ok"

LOCAL_IP="$(detect_ip)"
TAILSCALE_IP="$(detect_tailscale_ip)"
HOST_SHORT="$(hostname -s 2>/dev/null || true)"
BASE_URL=""
CANDIDATES=()

if [ -n "$LOCAL_IP" ]; then
  BASE_URL="http://${LOCAL_IP}:${LEDGER_PORT}"
fi
if [ -n "$HOST_SHORT" ]; then
  CANDIDATES+=("http://${HOST_SHORT}.local:${LEDGER_PORT}")
fi
if [ -n "$TAILSCALE_IP" ]; then
  CANDIDATES+=("http://${TAILSCALE_IP}:${LEDGER_PORT}")
fi
if [ -z "$BASE_URL" ] && [ "${#CANDIDATES[@]}" -gt 0 ]; then
  BASE_URL="${CANDIDATES[0]}"
fi
if [ -z "$BASE_URL" ]; then
  BASE_URL="http://<this-machine-ip>:${LEDGER_PORT}"
fi

python3 - "$NODE_NAME" "$BASE_URL" "${CANDIDATES[@]}" <<'PY'
import json
import sys

name = sys.argv[1]
base_url = sys.argv[2]
candidates = [url for url in sys.argv[3:] if url and url != base_url]
payload = {
    "name": name,
    "base_url": base_url,
    "base_url_candidates": candidates,
    "host": base_url.removeprefix("http://").split(":")[0],
    "role": "agent_ledger_readonly_collector",
    "timeout_seconds": 60,
    "enabled": True,
}
print("Collector node is ready.")
print("Registration payload:")
print(json.dumps(payload, ensure_ascii=False, indent=2))
PY

cat <<EOF

One-command install/register for a new collector machine:
  MAIN_GATEWAY_URL=${MAIN_GATEWAY_URL:-http://<main-node-ip>:8001} GATEWAY_API_KEY=<optional-api-key> NODE_NAME=${NODE_NAME} bash deploy/onboard-collector-node.sh

Candidate URLs this node advertised:
  ${BASE_URL}
$(for url in "${CANDIDATES[@]}"; do printf '  %s\n' "$url"; done)
EOF

if [ -n "$MAIN_GATEWAY_URL" ]; then
  echo "Registering node on main gateway..."
  PAYLOAD="$(python3 - "$NODE_NAME" "$BASE_URL" "${CANDIDATES[@]}" <<'PY'
import json
import sys

name = sys.argv[1]
base_url = sys.argv[2]
candidates = [url for url in sys.argv[3:] if url and url != base_url]
print(json.dumps({
    "name": name,
    "base_url": base_url,
    "base_url_candidates": candidates,
    "host": base_url.removeprefix("http://").split(":")[0],
    "role": "agent_ledger_readonly_collector",
    "timeout_seconds": 60,
    "enabled": True,
}, ensure_ascii=False))
PY
)"
  CURL_HEADERS=(-H "Content-Type: application/json")
  if [ -n "$GATEWAY_API_KEY" ]; then
    CURL_HEADERS+=(-H "X-API-Key: ${GATEWAY_API_KEY}")
  fi
  curl -fsS -X POST "${MAIN_GATEWAY_URL%/}/admin/nodes" \
    "${CURL_HEADERS[@]}" \
    --max-time 20 \
    -d "$PAYLOAD"
  echo
  echo "Registered on ${MAIN_GATEWAY_URL%/}."
  echo "Verifying main gateway fleet read..."
  VERIFY_HEADERS=()
  if [ -n "$GATEWAY_API_KEY" ]; then
    VERIFY_HEADERS=(-H "X-API-Key: ${GATEWAY_API_KEY}")
  fi
  if curl -fsS "${MAIN_GATEWAY_URL%/}/fleet-ledger?days=7&limit=20" \
    "${VERIFY_HEADERS[@]}" \
    --max-time 20 >/dev/null; then
    echo "Main gateway fleet read: ok"
  else
    echo "Main gateway registered the node, but /fleet-ledger verification failed or requires auth. Check main gateway logs/config." >&2
  fi
else
  cat <<EOF

To auto-register from this machine, rerun with:
  MAIN_GATEWAY_URL=http://<main-node-ip>:8001 GATEWAY_API_KEY=<optional-api-key> NODE_NAME=${NODE_NAME} bash deploy/onboard-collector-node.sh

Or paste the registration payload above into the main node /admin/nodes API.
EOF
fi
