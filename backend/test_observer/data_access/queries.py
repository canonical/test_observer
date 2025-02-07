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


from sqlalchemy import select

from test_observer.data_access.models import ArtefactBuild

latest_artefact_builds = (
    select(ArtefactBuild)
    .distinct(ArtefactBuild.artefact_id, ArtefactBuild.architecture)
    .order_by(
        ArtefactBuild.artefact_id,
        ArtefactBuild.architecture,
        ArtefactBuild.revision.desc(),
    )
)
