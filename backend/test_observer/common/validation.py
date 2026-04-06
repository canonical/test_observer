# Copyright 2026 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

from typing import Any

from test_observer.common.enums import Permission


def validate_permissions(permissions: list[Any]) -> list[Permission]:
    """
    Make sure that the provided permissions are valid Permission enum members.
    """

    validated: list[Permission] = []
    for permission in permissions:
        if not isinstance(permission, Permission | str):
            raise ValueError(f"Invalid permission type: {permission} (type {type(permission)})")
        if permission not in Permission:
            raise ValueError(f"Invalid permission: {permission}")
        validated.append(Permission(permission))
    return validated
