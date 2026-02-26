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

OPENAPI_JSON="$1"

# List exceptions as path/method pairs (method in lowercase)
EXCEPTIONS='[
  {"method": "get", "path": "/v1/version"},
  {"method": "get", "path": "/"},
  {"method": "get", "path": "/sentry-debug"},
  {"method": "get", "path": "/openapi.json"},
  {"method": "get", "path": "/docs"},
  {"method": "get", "path": "/v1/auth/saml/login"},
  {"method": "get", "path": "/v1/auth/saml/logout"},
  {"method": "post", "path": "/v1/auth/saml/acs"},
  {"method": "get", "path": "/v1/auth/saml/sls"},
  {"method": "post", "path": "/v1/auth/saml/sls"},
  {"method": "get", "path": "/v1/users/me"},
  {"method": "get", "path": "/v1/applications/me"}
]'

missing_permissions=$(jq -e --argjson exceptions "$EXCEPTIONS" '[
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
  | select($op["x-permissions"] | length == 0)
  | {path: $path, method: $method}
]' "$OPENAPI_JSON")

if [ "$missing_permissions" != "[]" ]; then
  echo "Endpoints missing permissions:"
  echo "$missing_permissions" | jq -r '.[] | .method + " " + .path'
  exit 1
fi

echo "All endpoints have permissions defined."
