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

from launchpadlib.launchpad import Launchpad  # type: ignore
from pydantic import EmailStr

from .models import LaunchpadUser


class LaunchpadAPI:
    def __init__(self):
        self.launchpad = Launchpad.login_anonymously(
            "test-observer", "production", version="devel"
        )

    def get_user_by_email(self, email: EmailStr) -> LaunchpadUser | None:
        user = self.launchpad.people.getByEmail(email=email)
        if user:
            return LaunchpadUser(
                handle=user.name,
                email=email,
                name=user.display_name,
                teams=[team.name for team in user.super_teams],
            )
        return None
