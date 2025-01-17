#!/usr/bin/env python
# Copyright (C) 2023 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


from argparse import ArgumentParser

from test_observer.users.add_user import add_user

if __name__ == "__main__":
    parser = ArgumentParser(
        prog="add_user",
        description="Adds a user via their launchpad email"
        " to the list of users that can review artefacts",
    )

    parser.add_argument("launchpad_email", type=str)

    args = parser.parse_args()

    add_user(args.launchpad_email)
