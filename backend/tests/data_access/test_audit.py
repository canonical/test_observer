# Copyright 2026 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# You should have received a copy of the License along with this program.  If
# not, see <https://www.gnu.org/licenses/>.
#
# SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from test_observer.data_access.audit import set_audit_context


def test_set_audit_context_merges_actors_and_reapplies_after_commit(db_session: Session) -> None:
    set_audit_context(db_session, user_id=12)
    set_audit_context(db_session, application_id=3)

    expected = {"automation": "tests", "user": {"id": 12}, "application": {"id": 3}}
    assert db_session.info["triggered_by"] == expected
    assert db_session.scalar(text("SELECT current_setting('audit.triggered_by')::jsonb")) == expected

    db_session.commit()

    assert db_session.scalar(text("SELECT current_setting('audit.triggered_by')::jsonb")) == expected


def test_set_audit_context_requires_an_actor(db_session: Session) -> None:
    with pytest.raises(ValueError):
        set_audit_context(db_session)
    with pytest.raises(ValueError):
        set_audit_context(db_session, automation="")
    with pytest.raises(ValueError):
        set_audit_context(db_session, automation="  ")
