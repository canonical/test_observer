#!/bin/bash

if git diff --cached --name-only | grep --quiet "backend"; then
    cd backend
    poetry install >/dev/null 2>&1

    echo "Starting a transient copy of test-observer-api to fetch the OpenAPI schema..."
    docker build -t test-observer-api . >/dev/null 2>&1
    trap 'docker stop transient-test-observer-api >/dev/null 2>&1; docker rm transient-test-observer-api >/dev/null 2>&1' EXIT
    docker run -d -p 30001:30000 --name transient-test-observer-api test-observer-api >/dev/null 2>&1

    for i in {1..5}; do
        if curl --output /dev/null --silent --head --fail "http://localhost:30001/openapi.json"; then
            curl --silent http://localhost:30001/openapi.json -o schemas/openapi.json
            git add schemas/openapi.json
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
fi
