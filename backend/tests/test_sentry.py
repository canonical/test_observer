# Copyright 2026 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

import sentry_sdk


def test_sentry_initializes_without_error():
    """
    This test simply checks that the Sentry SDK can be initialized with the provided DSN
    without raising any exceptions. It does not check for successful event sending,
    as that would require integration testing with a real Sentry instance.

    This test was added after `sentry_sdk.init` broke in a staging deployment following dependency updates.
    All tests ran without SENTRY_DSN set, which means sentry_sdk.init() was not exercised by tests.
    """
    try:
        sentry_sdk.init("https://abc123xyz@o0.ingest.sentry.io/123456")
    finally:
        sentry_sdk.get_client().close()