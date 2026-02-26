#!/usr/bin/env python

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
