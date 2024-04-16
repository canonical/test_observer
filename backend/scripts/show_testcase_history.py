# ruff: noqa: T201

import argparse
import asyncio
import re

from aiohttp import ClientSession


async def main(
    submission_json_jenkins_url: str, cases: list[str], number_of_jenkins_jobs: int
):
    urls = get_previous_jenkins_submission_json_urls(
        submission_json_jenkins_url, number_of_jenkins_jobs
    )

    async with ClientSession() as session:
        tasks = [fetch_json(url, session) for url in urls]
        submission_jsons = await asyncio.gather(*tasks)
        url_to_statuses = {
            urls[i]: {case: get_testcase_status(case, submission) for case in cases}
            for i, submission in enumerate(submission_jsons)
        }

    builds_headings = " | ".join(
        f"{extract_build_number_from_jenkins_submission_json_url(url): <4}"
        for url in url_to_statuses
    )

    print(f"{builds_headings} | case")

    for case in cases:
        statuses = " | ".join(
            str(statuses[case]) for statuses in url_to_statuses.values()
        )
        print(f"{statuses} | {case}")


def get_previous_jenkins_submission_json_urls(url: str, count: int) -> list[str]:
    build_url_prefix = extract_build_url_prefix_from_jenkins_submission_json_url(url)
    original_build_number = extract_build_number_from_jenkins_submission_json_url(url)
    urls = []

    for i in range(count):
        build_number = original_build_number - i
        if build_number < 1:
            break

        urls.append(
            f"{build_url_prefix}{build_number}/artifact/artifacts/submission.json"
        )

    return urls


def extract_build_number_from_jenkins_submission_json_url(url: str) -> int:
    pattern = ".+/(\d+)/artifact/artifacts/submission\.json"
    match = re.match(pattern, url)
    if match is None:
        raise ValueError(f"Provided url {url} is not a valid jenkins submission url")
    return int(match.group(1))


def extract_build_url_prefix_from_jenkins_submission_json_url(url: str) -> str:
    pattern = "(.+/)\d+/artifact/artifacts/submission\.json"
    match = re.match(pattern, url)
    if match is None:
        raise ValueError(f"Provided url {url} is not a valid jenkins submission url")
    return str(match.group(1))


def get_testcase_status(testcase_id: str, submission_json: dict) -> str | None:
    results = submission_json.get("results")
    if results:
        for result in results:
            case = result.get("id")
            status = result.get("status")
            if case and status and case == testcase_id:
                return status

    return None


async def fetch_json(url: str, session: ClientSession) -> dict:
    async with session.get(url) as response:
        if response.status == 404:
            return {}
        return await response.json()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Takes a jenkins url of a submission json, and a test case id."
        "Returns a string code showing the result of this test case in past runs",
    )
    parser.add_argument(
        "submission_json_jenkins_url", help="Jenkins URL of the latest submission json"
    )
    parser.add_argument(
        "cases",
        nargs="+",
        help="ids of the test cases you want to see the history for"
        " (e.g. camera/detect bluetooth/detect)",
    )
    parser.add_argument(
        "--number-of-jenkins-jobs",
        type=int,
        default=15,
        help="number of previous jenkins jobs to process",
    )
    args = parser.parse_args()

    asyncio.run(
        main(args.submission_json_jenkins_url, args.cases, args.number_of_jenkins_jobs)
    )
