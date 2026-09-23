#!/bin/bash

set -euo pipefail

# Check if TEST_OBSERVER_API_URL is set
if [ -z "${TEST_OBSERVER_API_URL:-}" ]; then
    echo "Warning: TEST_OBSERVER_API_URL is not set. Requests may not be routed correctly."
    exit 1
fi

# Check if TEST_OBSERVER_API_KEY is set
if [ -z "${TEST_OBSERVER_API_KEY:-}" ]; then
    echo "Warning: TEST_OBSERVER_API_KEY is not set. Requests may not be authorized correctly."
    exit
fi

docker compose up --build --no-deps --detach --quiet-build test-observer-frontend
echo "Access the frontend at: http://localhost:30001/wip"
echo "⚠️  NOTE: Requests are routed to: ${TEST_OBSERVER_API_URL:-}"
echo "Stop with 'just down'"