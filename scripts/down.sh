#!/bin/bash

set -euo pipefail

docker compose stop test-observer-frontend
echo "Frontend container stopped."