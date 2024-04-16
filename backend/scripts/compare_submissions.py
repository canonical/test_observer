# ruff: noqa: T203

import argparse
import asyncio
from pprint import pprint
from typing import Any

import aiohttp


async def main(submission1_jenkinsurl: str, submission2_jenkinsurl: str):
    async with aiohttp.ClientSession() as session:
        submission1, submission2 = await asyncio.gather(
            fetch_json(submission1_jenkinsurl, session),
            fetch_json(submission2_jenkinsurl, session),
        )

    results1 = extract_results(submission1)
    results2 = extract_results(submission2)

    diff = diff_between_results(results1, results2)
    pprint(diff)


async def fetch_json(url: str, session: aiohttp.ClientSession) -> dict:
    async with session.get(url) as response:
        if response.status == 404:
            return {}
        return await response.json()


def extract_results(submission: dict[str, Any]) -> dict[str, str]:
    return {result["id"]: result["status"] for result in submission["results"]}


def diff_between_results(
    results1: dict[str, str], results2: dict[str, str]
) -> dict[str, Any]:
    result: dict[str, Any] = {}

    result["only_in_1"] = {
        key: results1[key] for key in results1.keys() - results2.keys()
    }

    result["different"] = {
        key: (results1[key], results2[key])
        for key in results1.keys() & results2.keys()
        if results1[key] != results2[key]
    }

    result["only_in_2"] = {
        key: results2[key] for key in results2.keys() - results1.keys()
    }

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("submission1_jenkinsurl", help="Jenkins URL of submission 1")
    parser.add_argument("submission2_jenkinsurl", help="Jenkins URL of submission 2")

    args = parser.parse_args()

    asyncio.run(main(args.submission1_jenkinsurl, args.submission2_jenkinsurl))
