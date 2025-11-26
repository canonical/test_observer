#!/bin/bash
# Script to fetch the OpenAPI schema from the running server and save it to schemata/openapi.json

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Go to backend directory (parent of scripts)
cd "$SCRIPT_DIR/.."

for i in {1..5}; do
    if curl --output /dev/null --silent --fail "http://localhost:30000/openapi.json"; then
        curl --silent http://localhost:30000/openapi.json | jq > schemata/openapi.json
        echo "OpenAPI schema fetched and written to schemata/openapi.json"
        success=true
        break
    else
        sleep 1
    fi
done

if [ -z "$success" ]; then
    echo "Failed to fetch openapi.json after multiple attempts."
fi
