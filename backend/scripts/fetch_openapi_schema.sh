#!/bin/bash
# Script to fetch the OpenAPI schema from the running server and save it to schemata/openapi.json

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Go to backend directory (parent of scripts)
cd "$SCRIPT_DIR/.."

tmpfile=$(mktemp)
if curl --silent --fail "http://localhost:30000/openapi.json" -o "$tmpfile"; then
    jq < "$tmpfile" > schemata/openapi.json
    echo "OpenAPI schema fetched and written to schemata/openapi.json"
else
    echo "Failed to fetch openapi.json"
fi
rm "$tmpfile"