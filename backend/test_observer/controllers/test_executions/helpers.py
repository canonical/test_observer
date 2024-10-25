# Copyright 2024 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from itertools import groupby

from test_observer.data_access.models import TestResult

from .models import PreviousTestResult


def parse_previous_test_results(
    previous_test_results: list[TestResult],
) -> dict[int, list[PreviousTestResult]]:
    grouped_test_cases = groupby(
        previous_test_results, lambda test_result: test_result.test_case_id
    )

    return {
        test_case_id: [
            PreviousTestResult(
                status=test_result.status,
                version=test_result.test_execution.artefact_build.artefact.version,
                artefact_id=test_result.test_execution.artefact_build.artefact_id,
                test_execution_id=test_result.test_execution.id,
            )
            for test_result in test_results
        ]
        for test_case_id, test_results in grouped_test_cases
    }
