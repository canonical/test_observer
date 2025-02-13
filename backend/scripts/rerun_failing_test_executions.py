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


# ruff: noqa: T201

import argparse
import functools
import re
from os import environ

from requests import Session

TO_API_URL = environ.get("TO_API_URL", "https://test-observer-api.canonical.com")

requests = Session()
requests.request = functools.partial(requests.request, timeout=30)  # type: ignore


def main(artefact_id: int, test_case_regex: str, reversed: bool):
    artefact_builds = requests.get(
        f"{TO_API_URL}/v1/artefacts/{artefact_id}/builds"
    ).json()

    test_case_matcher = re.compile(test_case_regex)

    relevant_test_executions = []
    for ab in artefact_builds:
        for te in ab["test_executions"]:
            if (
                te["review_decision"] == []
                and not te["is_rerun_requested"]
                and te["status"] == "FAILED"
            ):
                relevant_test_executions.append(te)

    test_execution_ids_to_rerun = []
    for te in relevant_test_executions:
        test_results = requests.get(
            f"{TO_API_URL}/v1/test-executions/{te['id']}/test-results"
        ).json()

        matching_failed_tests = (
            tr
            for tr in test_results
            if tr["status"] == "FAILED" and test_case_matcher.match(tr["name"])
        )

        first_failing_test = next(matching_failed_tests, None)

        if first_failing_test and not reversed:
            test_execution_ids_to_rerun.append(te["id"])
            print(
                f"will rerun {te['environment']['name']}"
                f" for failing {first_failing_test['name']}"
            )
        elif not first_failing_test and reversed:
            test_execution_ids_to_rerun.append(te["id"])
            print(
                f"will rerun {te['environment']['name']}"
                f" as no failing matches found and reversed option is set"
            )

    should_rerun = (
        input(
            f"Will rerun {len(test_execution_ids_to_rerun)}"
            " test executions is that ok? (y/N) "
        ).lower()
        == "y"
    )

    if should_rerun:
        requests.post(
            f"{TO_API_URL}/v1/test-executions/reruns",
            json={"test_execution_ids": test_execution_ids_to_rerun},
        )
        print("Submitted rerun requests")
    else:
        print("Aborting the script")


example_usage = """Example:

  python %(prog)s 47906 '.*wireless.*'
  python %(prog)s 47906 '.*suspend.*'"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Reruns test executions of an artefact that"
        " failed particular test cases matched by the passed regex."
        "\nUses TO_API_URL environment if defined defaulting to production otherwise",
        epilog=example_usage,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("artefact_id", type=int)
    parser.add_argument("test_case_regex", type=str)
    parser.add_argument("--reversed", action="store_true")
    args = parser.parse_args()

    main(args.artefact_id, args.test_case_regex, args.reversed)
