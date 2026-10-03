#!/bin/bash

# Copyright 2025 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-FileCopyrightText: Copyright 2025 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

set -e

echo "Starting Test Observer Backend..."

# Keep the shell and Python checks consistent when users provide TRUE/True.
SWIFT_PROXY_ENABLED="${SWIFT_PROXY_ENABLED:-false}"
if [ "${SWIFT_PROXY_ENABLED,,}" = "true" ]; then
    SWIFT_PROXY_ENABLED=true
else
    SWIFT_PROXY_ENABLED=false
fi

# Start nginx only for local Swift proxy testing. The default development setup
# continues to expose Uvicorn directly on port 30000.
if [ "$SWIFT_PROXY_ENABLED" = "true" ]; then
    echo "Swift proxy is enabled; validating configuration..."
    : "${OS_AUTH_URL:?OS_AUTH_URL must be set when SWIFT_PROXY_ENABLED=true}"
    : "${OS_USERNAME:?OS_USERNAME must be set when SWIFT_PROXY_ENABLED=true}"
    : "${OS_PASSWORD:?OS_PASSWORD must be set when SWIFT_PROXY_ENABLED=true}"
    : "${OS_PROJECT_NAME:?OS_PROJECT_NAME must be set when SWIFT_PROXY_ENABLED=true}"
    : "${SWIFT_PROXY_TEAM:?SWIFT_PROXY_TEAM must be set when SWIFT_PROXY_ENABLED=true}"
    python /opt/test-observer/swift_proxy_nginx.py
    nginx -t
    API_HOST=127.0.0.1
    API_PORT=30001
else
    API_HOST=0.0.0.0
    API_PORT=30000
fi

# Run database migrations
echo "Running database migrations..."
uv run alembic upgrade head

# Start the application
echo "Starting FastAPI application..."
uv run uvicorn test_observer.main:app --host "$API_HOST" --port "$API_PORT" --reload &

# Get the PID of the uvicorn process
APP_PID=$!
PIDS=("$APP_PID")

if [ "$SWIFT_PROXY_ENABLED" = "true" ]; then
    nginx -g 'daemon off;' &
    NGINX_PID=$!
    PIDS+=("$NGINX_PID")
fi

cleanup() {
    trap - EXIT INT TERM
    for pid in "${PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done
    for pid in "${PIDS[@]}"; do
        wait "$pid" 2>/dev/null || true
    done
}
trap cleanup EXIT INT TERM

# Check if seeding is enabled (default to false)
if [ "${SEED_DATA:-false}" = "true" ]; then
    echo "SEED_DATA is enabled. Waiting for API server to be ready..."
    
    # Wait for the API server to be ready
    timeout=60
    count=0
    while [ $count -lt $timeout ]; do
        if curl -f http://localhost:30000/health/ready > /dev/null 2>&1; then
            echo "API server is ready. Starting database seeding..."
            break
        fi
        echo "Waiting for API server... ($count/$timeout)"
        sleep 2
        count=$((count + 2))
    done
    
    if [ $count -ge $timeout ]; then
        echo "ERROR: API server failed to start within $timeout seconds"
        exit 1
    fi
    
    # Run seed data script
    uv run python scripts/seed_data.py
else
    echo "SEED_DATA is disabled. Skipping database seeding."
fi

# Exit if either long-running service exits.
if [ "${#PIDS[@]}" -eq 1 ]; then
    wait "$APP_PID"
else
    wait -n "${PIDS[@]}"
fi