# Copyright (C) 2023-2025 Canonical Ltd.
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


from sqlalchemy.orm import Session

from scripts.delete_artefact import delete_artefact
from test_observer.data_access.models import Artefact
from test_observer.data_access.models_enums import StageName
from tests.data_generator import DataGenerator


def test_deletes_artefact(db_session: Session, generator: DataGenerator):
    artefact = generator.gen_artefact(StageName.beta)

    delete_artefact(artefact.id, db_session)

    assert db_session.get(Artefact, artefact.id) is None
