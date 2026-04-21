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

"""Common helper functions used across the application"""

from test_observer.common.config import FRONTEND_URL
from test_observer.data_access.models import Artefact


def get_artefact_url(artefact: Artefact) -> str:
    """Generate the frontend URL for an artefact

    Args:
        artefact: The artefact to generate URL for

    Returns:
        Full URL to the artefact page in the frontend

    Examples:
        >>> artefact = Artefact(id=123, family=FamilyName.snap, ...)
        >>> get_artefact_url(artefact)
        'http://localhost:30001/snaps/123'
    """
    family_path = f"{artefact.family.value}s"  # snap -> snaps, deb -> debs, etc.
    return f"{FRONTEND_URL}/{family_path}/{artefact.id}"
