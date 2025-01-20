# Copyright (C) 2023 Canonical Ltd.
#
# This file is part of Test Observer Backend.
#
# Test Observer Backend is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
#
# Test Observer Backend is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


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
            return LaunchpadUser(handle=user.name, email=email, name=user.display_name)
        return None
