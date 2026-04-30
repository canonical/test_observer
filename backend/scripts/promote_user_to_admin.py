#!/usr/bin/env python

# Copyright 2025 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2025 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

from argparse import ArgumentParser

from test_observer.users.promote_user_to_admin import promote_user_to_admin

if __name__ == "__main__":
    parser = ArgumentParser(
        prog="promote_user_to_admin",
        description="Promotes a user to admin role via their email address",
    )
    parser.add_argument("email", type=str)
    args = parser.parse_args()
    promote_user_to_admin(args.email)
