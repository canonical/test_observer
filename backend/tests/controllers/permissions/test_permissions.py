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

from fastapi.testclient import TestClient

from test_observer.common.permissions import Permission
from tests.conftest import make_authenticated_request


def test_get_permissions(test_client: TestClient):
    response = make_authenticated_request(
        lambda: test_client.get("/v1/permissions"),
        Permission.view_permission,
    )
    assert response.status_code == 200
    assert response.json() == [p.value for p in Permission]
