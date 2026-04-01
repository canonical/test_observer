import csv
from collections import defaultdict
from argparse import ArgumentParser


def parse_args():
    ap = ArgumentParser()
    ap.add_argument("csvs", nargs="+")
    ap.add_argument("--test-glob", required=True)
    return ap.parse_args()


def load_csvs(csv_paths):
    rows = []
    for f_path in csv_paths:
        with open(f_path) as f:
            reader = csv.DictReader(f, delimiter=",")
            rows += list(reader)
    return rows


def relevant_rows(test_glob, row):
    # only use deb/snap runs and not server:xxx artifacts
    if row["Artefact.family"] not in ("snap", "deb"):
        return False
    if row["Artefact.name"].startswith("server:"):
        return False
    if row["Artefact.name"].startswith("mir-"):
        return False
    if row["TestExecution.status"] == "SKIPPED":
        return False

    return (
        row["TestCase.name"] == test_glob
        or row["TestCase.template_id"] == test_glob
    )


def add_row_data(row):
    row["created_at_month"] = row["TestResult.created_at"].rsplit("-", 1)[0]
    row["CID"] = row["TestExecution.c3_link"].split("/")[4]
    return row


def main():
    args = parse_args()
    rows = load_csvs(args.csvs)
    rows = [
        add_row_data(row) for row in rows if relevant_rows(args.test_glob, row)
    ]
    table = defaultdict(lambda: defaultdict(list))
    months = set()
    for row in rows:
        table[row["CID"]][row["created_at_month"]].append(
            row["TestExecution.status"]
        )
        months.add(row["created_at_month"])

    relative_table = defaultdict(lambda: defaultdict(float))
    for cid in table:
        for date in table[cid]:
            relative_table[cid][date] = sum(
                1 for x in table[cid][date] if x == "FAILED"
            ) / len(table[cid][date])

    absolute_table = defaultdict(lambda: defaultdict(float))
    for cid in table:
        for date in table[cid]:
            absolute_table[cid][date] = sum(
                1 for x in table[cid][date] if x == "FAILED"
            )

    print(f"Loaded {len(rows)} rows from {len(args.csvs)} files")

    sorted_months = sorted(months)

    def print_table(name, tbl):
        header = ["CID"] + sorted_months
        print(f"\n{name}")
        print(",".join(header))
        for cid in sorted(tbl):
            values = [str(tbl[cid].get(m, "")) for m in sorted_months]
            print(",".join([cid] + values))

    print_table("Relative Table", relative_table)
    print_table("Absolute Table", absolute_table)


if __name__ == "__main__":
    main()
