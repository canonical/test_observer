#!/bin/bash
# Script to fetch the OpenAPI schema from the running server and save it to schemata/openapi.json

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Go to backend directory (parent of scripts)
cd "$SCRIPT_DIR/.."

for i in {1..5}; do
    tmpfile=$(mktemp)
    if curl --silent --fail "http://localhost:30000/openapi.json" -o "$tmpfile"; then
        jq < "$tmpfile" > schemata/openapi.json
        echo "OpenAPI schema fetched and written to schemata/openapi.json"
        success=true
        rm "$tmpfile"
        break
    else
        rm "$tmpfile"
        sleep 1
    fi
done

if [ -z "$success" ]; then
    echo "Failed to fetch openapi.json after multiple attempts."
    exit 1
fi
