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

# NOTE: Remember to set TEST_OBSERVER_API_URL to a valid URL and set
# TEST_OBSERVER_API_KEY to a read-only key

# Show this help message
default:
    @just --list

# Start the frontend container
up:
    @./scripts/up.sh

# Stop the frontend container
down:
    @./scripts/down.sh

# Start native LXD services; optionally replace the DB from a zipped pg_dump directory archive
lxd-dev-up snapshot="":
    @if [ -n "{{snapshot}}" ]; then scripts/lxd-dev up --snapshot "{{snapshot}}"; else scripts/lxd-dev up; fi

# Stop the native Ubuntu services (PostgreSQL data is retained)
lxd-dev-down:
    @scripts/lxd-dev down

# Install SvelteKit frontend dependencies
sveltekit-install:
    cd frontend/sveltekit && npm ci

# Lint and type check the SvelteKit frontend
sveltekit-lint:
    cd frontend/sveltekit && npm run lint
    cd frontend/sveltekit && npm run check

# Auto-fix SvelteKit frontend formatting and lint issues
sveltekit-lint-fix:
    cd frontend/sveltekit && npm run lint:fix
