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

# ruff: noqa: T201

import argparse
import functools
import sys
from collections import Counter
from os import environ
from pprint import pprint

from requests import Session

TO_API_URL = environ.get("TO_API_URL", "https://test-observer-api.canonical.com")

requests = Session()
requests.request = functools.partial(requests.request, timeout=30)  # type: ignore


def main(artefact_id: int):
    artefact_builds = requests.get(
        f"{TO_API_URL}/v1/artefacts/{artefact_id}/builds"
    ).json()

    relevant_test_executions = [
        te
        for ab in artefact_builds
        for te in ab["test_executions"]
        if te["review_decision"] == [] and te["status"] == "FAILED"
    ]

    failing_test_cases: list[str] = []
    for i, te in enumerate(relevant_test_executions):
        test_results = requests.get(
            f"{TO_API_URL}/v1/test-executions/{te['id']}/test-results"
        ).json()

        failing_test_cases.extend(
            tr["template_id"] or tr["name"]
            for tr in test_results
            if tr["status"] == "FAILED"
        )

        sys.stdout.write("\r")
        sys.stdout.write(f"{i + 1}/{len(relevant_test_executions)}")
        sys.stdout.flush()

    counter = Counter(failing_test_cases)

    print()
    pprint(counter.most_common())  # noqa: T203


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Given an artefact id, prints the most common failing"
        " test cases under undecided test executions. Groups tests by template_id"
        " if present and case name otherwise"
        "\nUses TO_API_URL environment if defined defaulting to production otherwise",
    )
    parser.add_argument("artefact_id", type=int)
    args = parser.parse_args()

    main(args.artefact_id)
