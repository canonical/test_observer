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

from sqlalchemy.orm import Session

from test_observer.data_access.models import Artefact
from test_observer.data_access.setup import SessionLocal


def delete_artefact(artefact_id: int, session: Session | None = None):
    if session is None:
        session = SessionLocal()
        try:
            _delete(artefact_id, session)
        finally:
            session.close()
    else:
        _delete(artefact_id, session)


def _delete(artefact_id: int, session: Session) -> None:
    artefact = session.get(Artefact, artefact_id)
    if artefact:
        session.delete(artefact)
        session.commit()


if __name__ == "__main__":
    parser = ArgumentParser(
        prog="delete_artefact",
        description="Given an artefact id, deletes this artefact",
        epilog="Note that this will also delete builds, test executions"
        " and test results belonging to the artefact",
    )

    parser.add_argument("artefact_id", type=int)

    args = parser.parse_args()

    delete_artefact(args.artefact_id)
