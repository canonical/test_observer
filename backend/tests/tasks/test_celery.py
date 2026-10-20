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

from itertools import product
from unittest.mock import Mock, call

import pytest

from tasks import celery as celery_tasks

FLAGS = (
    "ENABLE_PERIODIC_TASKS",
    "ENABLE_KERNEL_SWM",
    "ENABLE_ARTEFACT_PROMOTION",
    "ENABLE_USER_SESSION_CLEANUP",
    "ENABLE_ISSUE_SYNC",
)


@pytest.mark.parametrize("enabled", list(product((False, True), repeat=5)))
def test_periodic_task_switches(
    monkeypatch: pytest.MonkeyPatch,
    enabled: tuple[bool, ...],
) -> None:
    for flag, value in zip(FLAGS, enabled, strict=True):
        monkeypatch.setenv(flag, str(value).lower())

    config = celery_tasks.SyncConfig
    groups: tuple[tuple[tuple[int, str], ...], ...] = (
        ((300, "integrate_with_kernel_swm"),),
        ((600, "run_promote_artefacts"),),
        ((600, "clean_user_sessions"),),
        (
            (config.OPEN_ISSUE_INTERVAL, "sync_high_priority_issues"),
            (config.RECENT_CLOSED_INTERVAL, "sync_medium_priority_issues"),
            (config.OLD_CLOSED_INTERVAL, "sync_low_priority_issues"),
        ),
    )

    for group in groups:
        for _, task_name in group:
            monkeypatch.setattr(celery_tasks, task_name, Mock())

    sender = Mock()
    celery_tasks.setup_periodic_tasks(sender=sender)

    expected = []
    if enabled[0]:
        for group_enabled, group in zip(enabled[1:], groups, strict=True):
            if group_enabled:
                for interval, task_name in group:
                    task = getattr(celery_tasks, task_name)
                    expected.append(call(interval, task.s()))

    assert sender.add_periodic_task.call_args_list == expected
