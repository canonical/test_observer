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

from test_observer.data_access.models import ArtefactBuild
from test_observer.data_access.models_enums import (
    ArtefactBuildEnvironmentReviewDecision,
)


def are_all_environments_approved(builds: list[ArtefactBuild]) -> bool:
    return all(
        review.review_decision
        and ArtefactBuildEnvironmentReviewDecision.REJECTED
        not in review.review_decision
        for build in builds
        for review in build.environment_reviews
    )


def is_there_a_rejected_environment(builds: list[ArtefactBuild]) -> bool:
    return any(
        ArtefactBuildEnvironmentReviewDecision.REJECTED in review.review_decision
        for build in builds
        for review in build.environment_reviews
    )
