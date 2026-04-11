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