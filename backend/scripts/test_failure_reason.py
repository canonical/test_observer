import os
import csv
import json
import string
import time
import urllib.request
from multiprocessing import Pool
from argparse import ArgumentParser

RETRY = 10

access_token = os.getenv("C3_TOKEN")
if not access_token:
    raise SystemExit("C3_TOKEN required")


def parse_args():
    ap = ArgumentParser()
    ap.add_argument("--filter", choices=("id", "artifact_name"), default="id")
    ap.add_argument("csvs", nargs="+")
    ap.add_argument("--test-ids", nargs="+", required=True)
    return ap.parse_args()


def get_summary(sub_id):
    """
    Get the validation results of a given list of submissions from the C3 API.
    """
    for i in range(RETRY):
        try:
            api_url = f"https://certification.canonical.com/api/v2/reports/summary/{sub_id}"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}",
            }
            # Convert the payload to a JSON string
            # Create the request object with the data and headers
            req = urllib.request.Request(
                api_url, headers=headers, method="GET"
            )
            # Send the request and get the response
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode("utf-8"))

            return (sub_id, result)
        except Exception as e:
            if i == RETRY - 1:
                raise
            print(f"C3 failed with exception: {e}", flush=True)
            time.sleep(min(i * 10, 60))


def slugify(_string: str):
    if not _string:
        return _string
    _string = _string.replace("com.canonical.certification::", "")

    valid_chars = frozenset(f"_{string.ascii_letters}{string.digits}")
    # Python identifiers cannot start with a digit
    if _string[0].isdigit():
        _string = "_" + _string
    return "".join(c if c in valid_chars else "_" for c in _string)


def get_filter(filter_name, filter_param):

    def id_filter(x: dict) -> bool:
        # if a test fails, the test run fail, so its 2 failed
        return (
            x["TestCase.name"] == filter_param
            or x["TestCase.template_id"] == filter_param
        ) and x["TestResult.status"] == "FAILED"

    def artifact_filter(x: dict) -> bool:
        return (
            x["Artefact.name"] == filter_param
            and x["TestResult.status"] == "FAILED"
        )

    def both(f):
        def _f(x: dict) -> bool:
            return x["Artefact.family"] in ["snap", "deb"] and f(x)

        return _f

    return {"id": both(id_filter), "artifact_name": both(artifact_filter)}[
        filter_name
    ]


def do_test_id(filter_arg, csvs, test_id):
    lines_of_interest = []
    filter_f = get_filter(filter_arg, test_id)

    for f_path in csvs:
        with open(f_path) as f:
            reader = csv.DictReader(f, delimiter=",")
            lines_of_interest += list(filter(filter_f, reader))

    artefact_id = (x["Artefact.name"] for x in lines_of_interest)
    to_links = [
        f"https://test-observer.canonical.com/#/{x["Artefact.family"]}s/{x["Artefact.id"]}?q={x["Environment.name"]}"
        for x in lines_of_interest
    ]
    machine_id = (x["TestExecution.c3_link"][45:57] for x in lines_of_interest)
    environment_name = (x["Environment.name"] for x in lines_of_interest)
    checkbox_version = (
        x["TestExecution.checkbox_version"] for x in lines_of_interest
    )
    test_date = (x["TestResult.created_at"] for x in lines_of_interest)

    sub_links = (x["TestExecution.c3_link"] for x in lines_of_interest)
    sub_links = [f"{x}test-results/fail" for x in sub_links]
    print(f"Found {len(sub_links)} failures")

    relevant_template_id = {
        x["TestCase.template_id"] for x in lines_of_interest
    }
    relevant_ids = {
        x["TestCase.name"] for x in lines_of_interest
    } | relevant_template_id
    relevant_ids = relevant_ids - {None, ""}

    file_name = slugify(test_id)

    with open(f"{file_name}.url", "w+") as f:
        f.writelines("\n".join(sub_links))

    sub_ids = [x.rsplit("/", 3)[-3] for x in sub_links]
    unique_ids = list(set(sub_ids))
    sub_summaries = {}
    print("Downloading all submissions")
    with Pool(min(len(unique_ids), 20)) as p:
        for i, (sub_id, sub_summary) in enumerate(
            p.imap_unordered(get_summary, unique_ids)
        ):
            print(f"Done {i+1}/{len(unique_ids)}")
            sub_summaries[sub_id] = sub_summary["results"][0]["testresult_set"]

    job_objects = [
        list(
            filter(
                lambda x: (
                    x["name"] in relevant_ids
                    or x["template_id"] in relevant_ids
                )
                and x["status"] == "fail",
                sub_summaries[sub_id],
            )
        )
        for sub_id in sub_ids
    ]
    fieldnames = [
        "TestObserver Link",
        "Submission Link",
        "Job ID",
        "Template ID",
        "Job log",
        "Machine",
        "Environment Name",
        "Checkbox Version",
        "Artefact id",
        "Test date",
    ]
    results = zip(
        to_links,
        sub_links,
        job_objects,
        machine_id,
        environment_name,
        checkbox_version,
        artefact_id,
        test_date,
    )
    results = (
        (
            to_link,
            sub_link,
            job_object["name"],
            job_object.get("template_id", ""),
            job_object["io_log"],
            machine_id,
            environment_name,
            checkbox_version,
            artefact_id,
            test_date,
        )
        for (
            to_link,
            sub_link,
            job_objects,
            machine_id,
            environment_name,
            checkbox_version,
            artefact_id,
            test_date,
        ) in results
        for job_object in job_objects
    )
    result_rows = [dict(zip(fieldnames, result_row)) for result_row in results]

    with open(f"{file_name}.csv", "w+") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(result_rows)


def main():
    args = parse_args()
    tot = len(args.test_ids)
    for i, test_id in enumerate(args.test_ids, 1):
        print(f"Doing [{i}/{tot}]: {test_id}")
        do_test_id(args.filter, args.csvs, test_id)


if __name__ == "__main__":
    main()
