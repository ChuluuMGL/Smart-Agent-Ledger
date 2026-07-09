#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${SMART_AGENT_LEDGER_REPO_URL:-https://github.com/ChuluuMGL/Smart-Agent-Ledger.git}"
BRANCH="${SMART_AGENT_LEDGER_BRANCH:-main}"
INSTALL_DIR="${SMART_AGENT_LEDGER_DIR:-$HOME/.smart-agent-ledger/app}"
MAIN_GATEWAY_URL="${MAIN_GATEWAY_URL:-}"
GATEWAY_API_KEY="${GATEWAY_API_KEY:-}"
NODE_NAME="${NODE_NAME:-$(hostname -s 2>/dev/null || echo "collector-node")}"
REQUIRE_TAILSCALE="${REQUIRE_TAILSCALE:-0}"

usage() {
  cat <<'EOF'
One-line bootstrap for a Smart Agent Ledger collector node.

Usage:
  bash bootstrap-collector-node.sh --main http://<mac-mini-tailscale-ip>:8001 --name <node-name>

Options:
  --main URL       Main gateway URL, for example http://100.x.y.z:8001.
  --api-key KEY    Main gateway API key, if /admin/nodes requires one.
  --name NAME      Collector node name. Defaults to hostname -s.
  --dir PATH       Install/update directory. Defaults to ~/.smart-agent-ledger/app.
  --repo URL       Git repository URL. Defaults to ChuluuMGL/Smart-Agent-Ledger.
  --branch NAME    Git branch. Defaults to main.
  --require-tailscale
                  Stop if no Tailscale 100.x IP is detected.
  --help           Show this help.

Environment variables with the same names are also supported:
  MAIN_GATEWAY_URL, GATEWAY_API_KEY, NODE_NAME,
  SMART_AGENT_LEDGER_DIR, SMART_AGENT_LEDGER_REPO_URL, SMART_AGENT_LEDGER_BRANCH.
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --main|--main-gateway-url)
      MAIN_GATEWAY_URL="${2:-}"
      shift 2
      ;;
    --api-key)
      GATEWAY_API_KEY="${2:-}"
      shift 2
      ;;
    --name)
      NODE_NAME="${2:-}"
      shift 2
      ;;
    --dir)
      INSTALL_DIR="${2:-}"
      shift 2
      ;;
    --repo)
      REPO_URL="${2:-}"
      shift 2
      ;;
    --branch)
      BRANCH="${2:-}"
      shift 2
      ;;
    --require-tailscale)
      REQUIRE_TAILSCALE="1"
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
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

install_with_git() {
  mkdir -p "$(dirname "$INSTALL_DIR")"
  if [ -d "$INSTALL_DIR/.git" ]; then
    git -C "$INSTALL_DIR" fetch --quiet origin "$BRANCH"
    git -C "$INSTALL_DIR" checkout --quiet "$BRANCH"
    git -C "$INSTALL_DIR" pull --quiet --ff-only origin "$BRANCH"
    return
  fi
  if [ -e "$INSTALL_DIR" ] && [ "$(find "$INSTALL_DIR" -mindepth 1 -maxdepth 1 2>/dev/null | head -n 1)" ]; then
    echo "Install directory exists but is not a git checkout: $INSTALL_DIR" >&2
    echo "Choose another --dir or remove that directory." >&2
    exit 1
  fi
  git clone --quiet --branch "$BRANCH" "$REPO_URL" "$INSTALL_DIR"
}

install_with_archive() {
  require_command curl
  require_command tar
  if [ "$REPO_URL" != "https://github.com/ChuluuMGL/Smart-Agent-Ledger.git" ]; then
    echo "git is not available, and archive fallback only supports the default repository." >&2
    exit 1
  fi
  local archive_url="https://codeload.github.com/ChuluuMGL/Smart-Agent-Ledger/tar.gz/refs/heads/${BRANCH}"
  local tmp_dir
  tmp_dir="$(mktemp -d)"
  trap 'rm -rf "$tmp_dir"' EXIT
  curl -fsSL "$archive_url" | tar -xz -C "$tmp_dir"
  local extracted
  extracted="$(find "$tmp_dir" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
  if [ -z "$extracted" ]; then
    echo "Failed to unpack repository archive." >&2
    exit 1
  fi
  rm -rf "$INSTALL_DIR"
  mkdir -p "$(dirname "$INSTALL_DIR")"
  mv "$extracted" "$INSTALL_DIR"
}

TAILSCALE_IP="$(detect_tailscale_ip)"
if [ -z "$TAILSCALE_IP" ]; then
  echo "Tailscale IP not detected. Same-LAN onboarding may still work, but cross-location monitoring needs Tailscale."
  if [ "$REQUIRE_TAILSCALE" = "1" ]; then
    echo "Stopping because --require-tailscale was set." >&2
    exit 1
  fi
else
  echo "Tailscale IP: $TAILSCALE_IP"
fi

require_command python3
if command -v git >/dev/null 2>&1; then
  install_with_git
else
  install_with_archive
fi

cd "$INSTALL_DIR"
chmod +x deploy/onboard-collector-node.sh deploy/install-agent-ledger-readonly-launchd.sh

echo "Running collector onboarding from: $INSTALL_DIR"
export MAIN_GATEWAY_URL
export GATEWAY_API_KEY
export NODE_NAME
bash deploy/onboard-collector-node.sh
