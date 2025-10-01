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


from test_observer.external_apis.launchpad.launchpad_api import LaunchpadAPI
from test_observer.external_apis.launchpad.models import LaunchpadUser


class FakeLaunchpadAPI(LaunchpadAPI):
    def __init__(self):
        # override superclass init
        pass

    def get_user_by_email(self, email: str) -> LaunchpadUser | None:
        if email == "john.doe@canonical.com":
            return LaunchpadUser(handle="john-doe", email=email, name="John Doe")
        if email == "certbot@canonical.com":
            return LaunchpadUser(handle="certbot", email=email, name="Certbot")
        return None
