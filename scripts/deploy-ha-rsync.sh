#!/usr/bin/env bash
# Deploy Samsung TV Max to Home Assistant via rsync over SSH.
# Requires rsync on the SSH server (common on generic Linux; not on HAOS).
# Usage: ./scripts/deploy-ha-rsync.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$REPO_ROOT/.env.ha"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: $ENV_FILE not found. Copy .env.ha.example and fill in your values." >&2
  exit 1
fi

# shellcheck source=/dev/null
source "$ENV_FILE"

HA_HOST="${HA_HOST:?HA_HOST must be set in .env.ha}"
HA_USER="${HA_USER:-root}"

# SSH identity: use ha_deploy key if present, override via HA_SSH_IDENTITY
if [[ -z "${HA_SSH_IDENTITY:-}" && -f "$HOME/.ssh/ha_deploy" ]]; then
  HA_SSH_IDENTITY="$HOME/.ssh/ha_deploy"
fi

SSH_OPTS=(-o StrictHostKeyChecking=no -o BatchMode=yes)
[[ -n "${HA_SSH_IDENTITY:-}" ]] && SSH_OPTS+=(-i "$HA_SSH_IDENTITY")

SRC="$REPO_ROOT/custom_components/samsungtv_max/"
DST="$HA_USER@$HA_HOST:/config/custom_components/samsungtv_max/"

VERSION=$(python3 -c "import json; print(json.load(open('$REPO_ROOT/custom_components/samsungtv_max/manifest.json'))['version'])")
echo "→ Deploying samsungtv_max v$VERSION to $HA_USER@$HA_HOST"

RSYNC_RSH="ssh ${SSH_OPTS[*]}"
export RSYNC_RSH

rsync -avz --delete \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.ruff_cache' \
  --exclude='node_modules/' \
  --exclude='frontend/src/' \
  --exclude='frontend/package.json' \
  --exclude='frontend/package-lock.json' \
  --exclude='frontend/rollup.config.mjs' \
  --exclude='frontend/tsconfig.json' \
  "$SRC" "$DST"

echo "✓ Deploy complete."

# Optional restart
if [[ -n "${HA_HTTP_URL:-}" && -n "${HA_TOKEN:-}" ]]; then
  echo "→ Restarting Home Assistant..."
  curl -s -X POST "$HA_HTTP_URL/api/services/homeassistant/restart" \
    -H "Authorization: Bearer $HA_TOKEN" \
    -H "Content-Type: application/json" -d '{}' > /dev/null
  echo "✓ Restart triggered."
fi
