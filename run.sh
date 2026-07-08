#!/bin/bash
# Start Smart Agent Ledger from this directory on port 8001.
# Before use: cp keys.env.example keys.env and fill in real keys.

cd "$(dirname "$0")"

if [ ! -f keys.env ]; then
  echo "Error: keys.env not found"
  echo "Copy keys.env.example to keys.env and fill in real keys first:"
  echo "  cp keys.env.example keys.env"
  echo "  open -e keys.env"
  exit 1
fi

# Check whether the port is already in use.
if lsof -i:8001 -sTCP:LISTEN -t >/dev/null 2>&1; then
  echo "Error: port 8001 is already in use. Stop the old process first:"
  echo "  kill \$(lsof -t -i:8001)"
  exit 1
fi

# Load keys.env into the current shell, ignoring comments and blank lines.
while IFS= read -r line || [ -n "$line" ]; do
  line="${line%%#*}"
  line="${line%"${line##*[![:space:]]}"}"
  [ -z "$line" ] && continue
  case "$line" in *=*) export "$line" ;; *) ;; esac
done < keys.env

PYTHON_BIN="$PWD/venv/bin/python"
if [ ! -x "$PYTHON_BIN" ]; then
  PYTHON_BIN="python3"
fi

# Check dependencies.
if ! "$PYTHON_BIN" -c "import fastapi, uvicorn, httpx" 2>/dev/null; then
  echo "Error: missing dependencies. Run:"
  echo "  pip install -r requirements.txt"
  exit 1
fi

echo "Environment loaded. Starting Smart Agent Ledger on port 8001 ..."
UVICORN_ARGS=(gateway:app --host 0.0.0.0 --port 8001)
if [ "${GATEWAY_ACCESS_LOG:-0}" != "1" ]; then
  UVICORN_ARGS+=(--no-access-log)
fi

exec "$PYTHON_BIN" -m uvicorn "${UVICORN_ARGS[@]}"
