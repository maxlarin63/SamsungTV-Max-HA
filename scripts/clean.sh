#!/usr/bin/env bash
# Remove caches and build artifacts (not .venv).
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "Cleaning $REPO_ROOT ..."
find "$REPO_ROOT" -type d -name __pycache__ -not -path '*/.venv/*' -exec rm -rf {} + 2>/dev/null || true
find "$REPO_ROOT" -name '*.pyc' -not -path '*/.venv/*' -delete 2>/dev/null || true
rm -rf "$REPO_ROOT/.pytest_cache" "$REPO_ROOT/.ruff_cache" "$REPO_ROOT/.mypy_cache"
echo "OK: Clean complete."
