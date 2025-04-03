import argparse
import csv
import logging
import os

from datetime import datetime, timedelta

import requests

DATE_FORMAT = "%Y-%m-%d"
TO_API_URL = os.environ.get("TO_API_URL", "https://test-observer-api.canonical.com")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def _validate_date(date_str):
    """Validates the date format and returns a datetime object."""
    try:
        return datetime.strptime(date_str, DATE_FORMAT)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Date '{date_str}' is not in the correct format: {DATE_FORMAT}"
        )


def _save_test_results_report_data(date_string, test_results):
    if not os.path.exists("test-results-reports"):
        os.makedirs("test-results-reports")

    file_name = f"test-results-reports/{date_string}.csv"
    logging.info(f"Saving test results report data to {file_name}")
    with open(file_name, "w") as file:
        file.write(test_results.text)
    logging.info(f"Test results report data for {date_string} saved to {file_name}")


def _fetch_test_results_report_data(date):
    date_string = date.strftime(DATE_FORMAT)
    if os.path.exists(f"test-results-reports/{date_string}.csv"):
        logging.info(f"Test results report data for {date_string} already exists.")
        return

    logging.info(f"Fetching test results report data for {date_string}.")

    next_date_string = (date + timedelta(days=1)).strftime(DATE_FORMAT)
    test_results = requests.get(
        f"{TO_API_URL}/v1/reports/test-results?start_date={date_string}T00:00:00&end_date={next_date_string}T00:00:00"
    )
    test_results.raise_for_status()
    _save_test_results_report_data(date_string, test_results)


def get_test_results_report_data(date):
    _fetch_test_results_report_data(date)

    date_string = date.strftime(DATE_FORMAT)
    file_name = f"test-results-reports/{date_string}.csv"
    logging.info(f"Reading test results report data from {file_name}")
    with open(file_name, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            yield row


def write_data_summary(test_results_summary, output_file):
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


def main(start_date, end_date, output_file):
    test_results_summary = {}

    current_date = start_date
    while current_date <= end_date:
        current_date_file = get_test_results_report_data(current_date)

        for row in current_date_file:
            test_identifier = (
                row["TestCase.template_id"]
                if row["TestCase.template_id"]
                else row["TestCase.name"]
            )

            if "mir" in test_identifier:
                continue

            if test_identifier not in test_results_summary:
                test_results_summary[test_identifier] = {
                    "PASSED": 0,
                    "SKIPPED": 0,
                    "FAILED": 0,
                }

            test_results_summary[test_identifier][row["TestResult.status"]] += 1

        current_date = current_date + timedelta(days=1)

    write_data_summary(test_results_summary, output_file)


example_usage = """Example:

  python %(prog)s 2024-10-01 2024-10-31 test_results_report.csv"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generates the test results report for a given time period"
        "\nUses TO_API_URL environment if defined defaulting to production otherwise",
        epilog=example_usage,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("start_date", help="Start date, format: YYYY-MM-DD", type=str)
    parser.add_argument("end_date", help="End date, format: YYYY-MM-DD", type=str)
    parser.add_argument(
        "output_file", help="Output file for the test results report", type=str
    )

    args = parser.parse_args()

    start_date = _validate_date(args.start_date)
    end_date = _validate_date(args.end_date)

    if start_date > end_date:
        raise argparse.ArgumentTypeError(
            f"Start date '{start_date}' must be before end date '{end_date}'"
        )

    today = datetime.now()
    today = today.replace(hour=0, minute=0, second=0, microsecond=0)
    if end_date >= today:
        raise argparse.ArgumentTypeError(
            f"End date '{end_date}' must be before today '{today}'"
        )

    if os.path.exists(args.output_file):
        raise argparse.ArgumentTypeError(
            f"Output file '{args.output_file}' already exists"
        )

    main(start_date, end_date, args.output_file)
    logging.info(
        f"Test results report data for {args.start_date} to {args.end_date} saved to {args.output_file}"
    )
