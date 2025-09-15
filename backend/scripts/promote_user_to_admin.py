#!/usr/bin/env python
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
