#!/bin/bash
set -e

OPENAPI_JSON="$1"

# List exceptions as path/method pairs (method in lowercase)
EXCEPTIONS='[
  {"path": "/v1/version", "method": "get"},
  {"path": "/", "method": "get"},
  {"path": "/sentry-debug", "method": "get"},
  {"path": "/openapi.json", "method": "get"},
  {"path": "/docs", "method": "get"},
  {"path": "/v1/auth/saml/login", "method": "get"},
  {"path": "/v1/auth/saml/logout", "method": "get"},
  {"path": "/v1/auth/saml/acs", "method": "post"},
  {"path": "/v1/auth/saml/sls", "method": "get"},
  {"path": "/v1/auth/saml/sls", "method": "post"}
]'

missing_permissions=$(jq -e --argjson exceptions "$EXCEPTIONS" '
  .paths
  | to_entries[]
  | .key as $path
  | .value
  | to_entries[]
  | .key as $method
  | .value as $op
  | select(
      ($exceptions | map(.path == $path and .method == $method) | any) | not
    )
  | select((.op["x-permissions"] | length) == 0)
  | {path: $path, method: $method}
' "$OPENAPI_JSON")

if [ -n "$missing_permissions" ]; then
  echo "Endpoints missing permissions:"
  echo "$missing_permissions" | jq -r '. | "\(.method) \(.path)"'
  exit 1
fi
