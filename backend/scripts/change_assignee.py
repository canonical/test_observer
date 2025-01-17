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

from test_observer.users.change_assignee import change_assignee

if __name__ == "__main__":
    parser = ArgumentParser(
        prog="change_assignee",
        description="Changes the user assigned to review a particular artefact",
    )

    parser.add_argument("artefact_id", type=int)
    parser.add_argument("user_id", type=int)

    args = parser.parse_args()

    change_assignee(args.artefact_id, args.user_id)
