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


from fastapi.testclient import TestClient

from tests.data_generator import DataGenerator


def test_get_teams(test_client: TestClient, generator: DataGenerator):
    user = generator.gen_user()
    team = generator.gen_team(permissions=["create_artefact"], members=[user])

    response = test_client.get("/v1/teams")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": team.id,
            "name": team.name,
            "permissions": ["create_artefact"],
            "members": [
                {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "launchpad_email": user.email,
                    "launchpad_handle": user.launchpad_handle,
                }
            ],
        }
    ]
