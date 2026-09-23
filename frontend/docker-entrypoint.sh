#!/bin/sh
# Copyright 2026 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3, as
# published by the Free Software Foundation.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: GPL-3.0-only

set -eu

if [ -n "${TEST_OBSERVER_API_URL:-}" ]; then
    # proxy_pass needs a trailing slash so that /api/ is stripped from the path.
    TEST_OBSERVER_API_URL="${TEST_OBSERVER_API_URL%/}/"
    TEST_OBSERVER_API_HOST=$(
        printf '%s' "$TEST_OBSERVER_API_URL" |
            sed -e 's#^[a-zA-Z][a-zA-Z0-9+.-]*://##' -e 's#/.*$##'
    )

    case "$TEST_OBSERVER_API_URL" in
    https://*) ;;
    http://localhost/* | http://localhost:*) ;;
    http://127.0.0.1/* | http://127.0.0.1:*) ;;
    *)
        echo "TEST_OBSERVER_API_URL must use https:// for remote endpoints, got ${TEST_OBSERVER_API_URL}" >&2
        exit 1
        ;;
    esac

    if [ -n "${TEST_OBSERVER_API_KEY:-}" ]; then
        TEST_OBSERVER_API_AUTHORIZATION="Bearer ${TEST_OBSERVER_API_KEY}"
    else
        # nginx omits the header entirely when the value is empty.
        TEST_OBSERVER_API_AUTHORIZATION=""
    fi

    export TEST_OBSERVER_API_URL TEST_OBSERVER_API_HOST TEST_OBSERVER_API_AUTHORIZATION

    envsubst '${TEST_OBSERVER_API_URL} ${TEST_OBSERVER_API_HOST} ${TEST_OBSERVER_API_AUTHORIZATION}' \
        </etc/nginx/nginx-remote-api.conf.template \
        >/etc/nginx/sites-available/test-observer-frontend

    echo "Proxying /api/ to ${TEST_OBSERVER_API_URL} (api key: $([ -n "${TEST_OBSERVER_API_KEY:-}" ] && echo set || echo unset))"
fi

exec "$@"
