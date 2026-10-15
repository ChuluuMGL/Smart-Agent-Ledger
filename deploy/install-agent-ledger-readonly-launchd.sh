#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLIST_TEMPLATE="$PROJECT_DIR/deploy/com.smart-agent-ledger.agent-ledger.plist.example"
PLIST_DEST="$HOME/Library/LaunchAgents/com.smart-agent-ledger.agent-ledger.plist"
LOG_DIR="$HOME/Library/Logs/smart-agent-ledger"
RUNTIME_DIR="${SMART_AGENT_LEDGER_RUNTIME_DIR:-$HOME/.smart-agent-ledger/agent-ledger}"
RUNTIME_VENV="$RUNTIME_DIR/venv"
PYTHON_BIN="$RUNTIME_VENV/bin/python"
# Access control: comma-separated CIDRs allowed to read /agent-ledger
# (e.g. the main node's Tailscale IP "100.101.102.103/32"). Loopback is always allowed.
ALLOWED_NETWORKS="${SMART_AGENT_LEDGER_COLLECTOR_ALLOWED_NETWORKS:-}"
# Bind address: loopback unless an allowlist is configured (override explicitly if needed).
if [ -n "${SMART_AGENT_LEDGER_COLLECTOR_HOST:-}" ]; then
  BIND_HOST="$SMART_AGENT_LEDGER_COLLECTOR_HOST"
elif [ -n "$ALLOWED_NETWORKS" ]; then
  BIND_HOST="0.0.0.0"
else
  BIND_HOST="127.0.0.1"
fi
case "$BIND_HOST$ALLOWED_NETWORKS" in
  *[!A-Za-z0-9.:/,_-]*)
    echo "Invalid characters in SMART_AGENT_LEDGER_COLLECTOR_HOST or SMART_AGENT_LEDGER_COLLECTOR_ALLOWED_NETWORKS" >&2
    exit 1
    ;;
esac

if [ ! -f "$PROJECT_DIR/agent_ledger_server.py" ]; then
  echo "agent_ledger_server.py not found in $PROJECT_DIR" >&2
  exit 1
fi

if [ ! -f "$PROJECT_DIR/requirements.txt" ]; then
  echo "requirements.txt not found in $PROJECT_DIR" >&2
  exit 1
fi

if ! grep -q "agent_ledger_server:app" "$PLIST_TEMPLATE"; then
  echo "Invalid plist template: missing agent_ledger_server:app" >&2
  exit 1
fi

mkdir -p "$HOME/Library/LaunchAgents" "$LOG_DIR"
mkdir -p "$RUNTIME_DIR"

if [ ! -x "$PYTHON_BIN" ]; then
  python3 -m venv "$RUNTIME_VENV"
fi

"$PYTHON_BIN" -m pip install --disable-pip-version-check -U pip >/dev/null
"$PYTHON_BIN" -m pip install --disable-pip-version-check -r "$PROJECT_DIR/requirements.txt" >/dev/null

PROJECT_ESCAPED=${PROJECT_DIR//&/&amp;}
PROJECT_ESCAPED=${PROJECT_ESCAPED//</&lt;}
PROJECT_ESCAPED=${PROJECT_ESCAPED//>/&gt;}
HOME_ESCAPED=${HOME//&/&amp;}
HOME_ESCAPED=${HOME_ESCAPED//</&lt;}
HOME_ESCAPED=${HOME_ESCAPED//>/&gt;}
PYTHON_BIN_ESCAPED=${PYTHON_BIN//&/&amp;}
PYTHON_BIN_ESCAPED=${PYTHON_BIN_ESCAPED//</&lt;}
PYTHON_BIN_ESCAPED=${PYTHON_BIN_ESCAPED//>/&gt;}

sed \
  -e "s#__PROJECT_DIR__#$PROJECT_ESCAPED#g" \
  -e "s#__HOME__#$HOME_ESCAPED#g" \
  -e "s#__PYTHON_BIN__#$PYTHON_BIN_ESCAPED#g" \
  -e "s#__BIND_HOST__#$BIND_HOST#g" \
  -e "s#__ALLOWED_NETWORKS__#$ALLOWED_NETWORKS#g" \
  "$PLIST_TEMPLATE" > "$PLIST_DEST"

plutil -lint "$PLIST_DEST" >/dev/null

launchctl unload "$PLIST_DEST" 2>/dev/null || true
launchctl load "$PLIST_DEST"
launchctl kickstart -k "gui/$(id -u)/com.smart-agent-ledger.agent-ledger" 2>/dev/null || true

echo "Installed read-only Agent ledger service: $PLIST_DEST"
echo "URL: http://127.0.0.1:8002/agent-ledger?days=90&limit=1000"
echo "Bind address: $BIND_HOST"
if [ -n "$ALLOWED_NETWORKS" ]; then
  echo "Allowed remote networks: $ALLOWED_NETWORKS"
else
  echo "Allowed remote networks: none (loopback only). Set SMART_AGENT_LEDGER_COLLECTOR_ALLOWED_NETWORKS"
  echo "  to the main node's IP/CIDR and rerun so the main gateway can pull this ledger."
fi
echo "Log file: $LOG_DIR/agent-ledger.log"
echo "Runtime venv: $RUNTIME_VENV"
