# ruff: noqa: T201

import argparse
import sys
from collections import Counter
from os import environ
from pprint import pprint

import requests

TO_API_URL = environ.get("TO_API_URL", "https://test-observer-api.canonical.com")


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
            tr["name"] for tr in test_results if tr["status"] == "FAILED"
        )

        sys.stdout.write("\r")
        sys.stdout.write(f"{i+1}/{len(relevant_test_executions)}")
        sys.stdout.flush()

    counter = Counter(failing_test_cases)

    print()
    pprint(counter.most_common())  # noqa: T203


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Given an artefact id, prints the most common failing"
        " test cases under undecided test executions."
        "\nUses TO_API_URL environment if defined defaulting to production otherwise",
    )
    parser.add_argument("artefact_id", type=int)
    args = parser.parse_args()

    main(args.artefact_id)
