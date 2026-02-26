# Copyright 2025 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2025 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

import argparse
from collections import defaultdict
import csv
import io
import logging
import os
import httpx
from collections.abc import Iterable
from datetime import datetime, timedelta

from fastapi.testclient import TestClient


import requests

DATE_FORMAT = "%Y-%m-%d"
TO_API_URL = os.environ.get("TO_API_URL", "https://test-observer-api.canonical.com")
EMPTY_TEST_RESULT_STATUS_COUNT = {
    "FAILED": 0,
    "PASSED": 0,
    "SKIPPED": 0,
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def _is_test_result_relevant(test_result: dict) -> bool:
    if "mir" in test_result["TestCase.name"]:
        return False

    return test_result["Artefact.family"] in ["snap", "deb"]


def _validate_date(date_str: str) -> datetime:
    """Validates the date format and returns a datetime object."""
    try:
        return datetime.strptime(date_str, DATE_FORMAT)
    except ValueError as err:
        raise argparse.ArgumentTypeError(
            f"Date {date_str} is not in the correct format: {DATE_FORMAT}"
        ) from err


def _save_test_results_report_data(
    date_string: str, test_results_response: httpx._models.Response | requests.Response
) -> None:
    if not os.path.exists("test-results-reports"):
        os.makedirs("test-results-reports")

    file_name = f"test-results-reports/{date_string}.csv"
    logging.info(f"Saving test results report data to {file_name}")
    with open(file_name, "w") as file:
        file.write(test_results_response.text)
    logging.info(f"Test results report data for {date_string} saved to {file_name}")


def _read_test_results_report_data(date_string: str) -> Iterable[dict]:
    file_name = f"test-results-reports/{date_string}.csv"
    with open(file_name) as file:
        yield from csv.DictReader(file)


def get_test_results_report_data(
    date: datetime, client: TestClient | requests.Session
) -> Iterable[dict]:
    date_string = date.strftime(DATE_FORMAT)
    if os.path.exists(f"test-results-reports/{date_string}.csv"):
        logging.info(f"Test results report data for {date_string} already exists.")
        yield from _read_test_results_report_data(date_string)
    else:
        logging.info(f"Fetching test results report data for {date_string}.")
        next_date_string = (date + timedelta(days=1)).strftime(DATE_FORMAT)
        test_results_response = client.get(
            f"{TO_API_URL}/v1/reports/test-results",
            params={
                "start_date": f"{date_string}T00:00:00",
                "end_date": f"{next_date_string}T00:00:00",
            },
            timeout=120,
        )
        test_results_response.raise_for_status()
        _save_test_results_report_data(date_string, test_results_response)
        yield from csv.DictReader(io.StringIO(test_results_response.text))


def write_data_summary(test_results_summary: dict, output_file: str) -> None:
    with open(output_file, "w") as f:
        summary_writer = csv.writer(f)
        summary_writer.writerow(["Test Identifier", "ALL", "FAIL", "PASS", "SKIP"])

        for test_identifier, test_result in test_results_summary.items():
            summary_writer.writerow(
                [
                    test_identifier,
                    test_result["FAILED"] + test_result["PASSED"],
                    test_result["FAILED"],
                    test_result["PASSED"],
                    test_result["SKIPPED"],
                ]
            )

    logging.info(f"Report saved to {output_file}")


def fetch_test_results_report(
    start_date: datetime,
    end_date: datetime,
    output_file: str,
    client: TestClient | requests.Session,
) -> None:
    test_results_summary: dict = defaultdict(
        lambda: EMPTY_TEST_RESULT_STATUS_COUNT.copy()
    )

    current_date = start_date
    while current_date <= end_date:
        current_date_results = get_test_results_report_data(current_date, client)
        for test_result in current_date_results:
            if not _is_test_result_relevant(test_result):
                continue

            test_identifier = (
                test_result["TestCase.template_id"]
                if test_result["TestCase.template_id"]
                else test_result["TestCase.name"]
            )
            test_results_summary[test_identifier][test_result["TestResult.status"]] += 1

        current_date = current_date + timedelta(days=1)

    write_data_summary(test_results_summary, output_file)


example_usage = (
    """Example:

  python %(prog)s --start_date 2024-10-01 --end_date 2024-10-31 """
    "--output_file test_results_report.csv"
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generates the test results report for a given time period"
        "\nUses TO_API_URL environment if defined defaulting to production otherwise",
        epilog=example_usage,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--start_date", help="Start date, format: YYYY-MM-DD", required=True, type=str
    )
    parser.add_argument(
        "--end_date",
        help="End date, format: YYYY-MM-DD",
        required=False,
        default=datetime.now().strftime(DATE_FORMAT),
        type=str,
    )
    parser.add_argument(
        "--output_file",
        help="Output file for the test results report",
        required=True,
        type=str,
    )

    args = parser.parse_args()

    start_date = _validate_date(args.start_date)
    end_date = _validate_date(args.end_date)

    if start_date > end_date:
        raise argparse.ArgumentTypeError(
            f"Start date '{start_date}' must be before end date '{end_date}'"
        )

    if os.path.exists(args.output_file):
        raise argparse.ArgumentTypeError(
            f"Output file '{args.output_file}' already exists"
        )

    fetch_test_results_report(
        start_date, end_date, args.output_file, requests.Session()
    )
