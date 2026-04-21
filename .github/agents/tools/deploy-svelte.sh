#!/usr/bin/env bash
# deploy-svelte.sh — Build the SvelteKit PoC and deploy to the running frontend container.
#
# Usage:
#   bash .github/agents/tools/deploy-svelte.sh
#
# Assumes:
#   - podman (or docker) is available
#   - A frontend container matching *frontend* is running
#   - The SvelteKit project is at frontend/svelte_poc/

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
SVELTE_DIR="$REPO_ROOT/frontend/svelte_poc"
DEPLOY_PATH="/usr/share/nginx/html/svelte_poc"

# Detect container runtime
if command -v podman &>/dev/null; then
  RUNTIME=podman
elif command -v docker &>/dev/null; then
  RUNTIME=docker
else
  echo "ERROR: Neither podman nor docker found." >&2
  exit 1
fi

# Find the frontend container
CONTAINER=$($RUNTIME ps --format '{{.Names}}' | grep -i frontend | head -1)
if [[ -z "$CONTAINER" ]]; then
  echo "ERROR: No running frontend container found." >&2
  exit 1
fi

echo "==> Building SvelteKit project..."
cd "$SVELTE_DIR"
npm run build

echo "==> Deploying to container '$CONTAINER' at $DEPLOY_PATH..."
$RUNTIME exec "$CONTAINER" bash -c "rm -rf $DEPLOY_PATH && mkdir -p $DEPLOY_PATH"
$RUNTIME cp build/. "$CONTAINER:$DEPLOY_PATH/"

echo "==> Done. Svelte PoC deployed to $DEPLOY_PATH"
