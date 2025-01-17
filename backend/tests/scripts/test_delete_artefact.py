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

from sqlalchemy.orm import Session

from scripts.delete_artefact import delete_artefact
from test_observer.data_access.models import Artefact
from test_observer.data_access.models_enums import StageName
from tests.data_generator import DataGenerator


def test_deletes_artefact(db_session: Session, generator: DataGenerator):
    artefact = generator.gen_artefact(StageName.beta)

    delete_artefact(artefact.id, db_session)

    assert db_session.get(Artefact, artefact.id) is None
