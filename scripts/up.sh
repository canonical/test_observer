#!/bin/bash

# Copyright 2026 Canonical Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

# Check if TEST_OBSERVER_API_URL is set
if [ -z "${TEST_OBSERVER_API_URL:-}" ]; then
    echo "Warning: TEST_OBSERVER_API_URL is not set. Requests may not be routed correctly."
    exit 1
fi

# Check if TEST_OBSERVER_API_KEY is set
if [ -z "${TEST_OBSERVER_API_KEY:-}" ]; then
    echo "Warning: TEST_OBSERVER_API_KEY is not set. Requests may not be authorized correctly."
    exit
fi

docker compose up --build --no-deps --detach --quiet-build test-observer-frontend
echo "Access the frontend at: http://localhost:30001/wip"
echo "⚠️  NOTE: Requests are routed to: ${TEST_OBSERVER_API_URL:-}"
echo "Stop with 'just down'"