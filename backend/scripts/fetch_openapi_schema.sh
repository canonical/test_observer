#!/bin/bash

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Go to backend directory (parent of scripts)
cd "$SCRIPT_DIR/.."

uv sync

echo "Starting a transient copy of test-observer-api to fetch the OpenAPI schema..."
trap 'kill $(jobs -p)' EXIT
SKIP_SAML_INIT=1 uv run uvicorn test_observer.main:app --host 0.0.0.0 --port 30000 &

for i in {1..5}; do
    if curl --output /dev/null --silent --head --fail "http://localhost:30000/openapi.json"; then
        curl --silent http://localhost:30000/openapi.json | jq > schemata/openapi.json
        git add schemata/openapi.json
        echo "OpenAPI schema fetched."
        success=true
        break
    else
        sleep 1
    fi
done

if [ -z "$success" ]; then
    echo "Failed to fetch /openapi.json after multiple attempts."
fi
