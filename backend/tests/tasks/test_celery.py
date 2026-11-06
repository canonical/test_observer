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
from unittest.mock import MagicMock, Mock, call

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


@pytest.mark.parametrize(
    ("task_name", "automation_name"),
    [
        ("clean_user_sessions", "celery.clean_user_sessions"),
        ("sync_high_priority_issues", "celery.sync_high_priority_issues"),
        ("sync_medium_priority_issues", "celery.sync_medium_priority_issues"),
        ("sync_low_priority_issues", "celery.sync_low_priority_issues"),
        ("sync_all_issues", "celery.sync_all_issues"),
        ("sync_issue_by_id", "celery.sync_issue_by_id"),
    ],
)
def test_background_writers_set_context_before_writing(
    monkeypatch: pytest.MonkeyPatch, task_name: str, automation_name: str
) -> None:
    session = MagicMock()
    session.__enter__.return_value = session
    issue = Mock()
    session.query.return_value.all.return_value = [issue]
    session.get.return_value = issue
    monkeypatch.setattr(celery_tasks, "SessionLocal", Mock(return_value=session))
    set_context = Mock()
    monkeypatch.setattr(celery_tasks, "set_audit_context", set_context)
    monkeypatch.setattr(celery_tasks, "create_synchronization_service", MagicMock())
    monkeypatch.setattr(celery_tasks.SyncStrategy, "get_issues_due_for_sync", Mock(return_value=[issue]))
    monkeypatch.setattr(celery_tasks.SyncStrategy, "get_sync_stats", Mock(return_value={}))

    def write(*_args: object) -> None:
        set_context.assert_called_once_with(session, automation_name=automation_name)

    writer = Mock(side_effect=write)
    monkeypatch.setattr(celery_tasks, "delete_expired_user_sessions", writer)
    monkeypatch.setattr(celery_tasks, "_apply_sync_results", writer)
    monkeypatch.setattr(celery_tasks.SyncResults, "from_results", Mock())

    task = getattr(celery_tasks, task_name)
    task.run(1) if task_name == "sync_issue_by_id" else task.run()

    writer.assert_called_once()
    set_context.assert_called_once_with(session, automation_name=automation_name)
