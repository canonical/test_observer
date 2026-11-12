# Copyright 2024 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

from importlib import import_module
from unittest.mock import Mock

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from scripts.add_user import add_user
from test_observer.data_access.models import User
from tests.fake_launchpad_api import FakeLaunchpadAPI


def test_create_user(db_session: Session):
    email = "john.doe@canonical.com"

    user = add_user(email, db_session, FakeLaunchpadAPI())

    assert user
    assert (
        db_session.execute(
            select(User).where(
                User.email == email,
                User.launchpad_handle == "john-doe",
                User.name == "John Doe",
            )
        ).scalar_one_or_none()
        is not None
    )


def test_email_not_in_launchpad():
    email = "missing-email@canonical.com"
    with pytest.raises(ValueError, match="Email not registered in launchpad"):
        add_user(email, launchpad_api=FakeLaunchpadAPI())


@pytest.mark.parametrize(
    ("module_name", "helper_name", "args"),
    [
        ("add_user", "_create_user", ("john.doe@canonical.com",)),
        ("change_assignee", "_change_assignee", (1, 2)),
        ("promote_user_to_admin", "_promote_user", ("john.doe@canonical.com",)),
    ],
)
@pytest.mark.parametrize("supplied_session", [False, True])
def test_user_helpers_set_context_only_for_owned_sessions(
    monkeypatch: pytest.MonkeyPatch,
    module_name: str,
    helper_name: str,
    args: tuple[str] | tuple[int, int],
    supplied_session: bool,
) -> None:
    module = import_module(f"test_observer.users.{module_name}")
    session = Mock()
    session_factory = Mock(return_value=session)
    set_context = Mock()
    monkeypatch.setattr(module, "SessionLocal", session_factory)
    monkeypatch.setattr(module, "set_audit_context", set_context)

    def write(*_args: object) -> object:
        if supplied_session:
            set_context.assert_not_called()
        else:
            set_context.assert_called_once_with(session, automation_name=f"scripts.{module_name}")
        return session

    monkeypatch.setattr(module, helper_name, write)
    kwargs = {"launchpad_api": FakeLaunchpadAPI()} if module_name == "add_user" else {}
    getattr(module, module_name)(*args, session=session if supplied_session else None, **kwargs)

    if supplied_session:
        session_factory.assert_not_called()
        session.close.assert_not_called()
    else:
        session.close.assert_called_once()
