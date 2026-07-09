#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLIST_TEMPLATE="$PROJECT_DIR/deploy/com.smart-agent-ledger.agent-ledger.plist.example"
PLIST_DEST="$HOME/Library/LaunchAgents/com.smart-agent-ledger.agent-ledger.plist"
LOG_DIR="$HOME/Library/Logs/smart-agent-ledger"
RUNTIME_DIR="${SMART_AGENT_LEDGER_RUNTIME_DIR:-$HOME/.smart-agent-ledger/agent-ledger}"
RUNTIME_VENV="$RUNTIME_DIR/venv"
PYTHON_BIN="$RUNTIME_VENV/bin/python"

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
  "$PLIST_TEMPLATE" > "$PLIST_DEST"

plutil -lint "$PLIST_DEST" >/dev/null

launchctl unload "$PLIST_DEST" 2>/dev/null || true
launchctl load "$PLIST_DEST"
launchctl kickstart -k "gui/$(id -u)/com.smart-agent-ledger.agent-ledger" 2>/dev/null || true

echo "Installed read-only Agent ledger service: $PLIST_DEST"
echo "URL: http://127.0.0.1:8002/agent-ledger?days=90&limit=1000"
echo "Log file: $LOG_DIR/agent-ledger.log"
echo "Runtime venv: $RUNTIME_VENV"
