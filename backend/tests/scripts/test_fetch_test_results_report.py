# Copyright (C) 2023 Canonical Ltd.
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

from datetime import datetime, timedelta
import os
import subprocess

from scripts.fetch_test_results_report import fetch_test_results_report
from test_observer.data_access.models_enums import StageName
from tests.data_generator import DataGenerator

from fastapi.testclient import TestClient


def _run_script(input_params: list[str]) -> tuple[bytes, bytes]:
    process = subprocess.Popen(
        ["python3", "scripts/fetch_test_results_report.py"] + input_params,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = process.communicate()
    return stdout, stderr


def _clean_files_created(output_file_name: str) -> None:
    if os.path.exists(output_file_name):
        os.remove(output_file_name)

    if os.path.exists("test-results-reports"):
        for file in os.listdir("test-results-reports"):
            os.remove(os.path.join("test-results-reports", file))
        os.rmdir("test-results-reports")


def _verify_csv_file(file_name: str) -> None:
    assert os.path.exists(file_name)
    with open(file_name) as output_file:
        lines = output_file.readlines()
        assert lines == [
            "Test Identifier,ALL,FAIL,PASS,SKIP\n",
            "camera/detect,1,0,1,0\n",
        ]


def test_fetch_test_results_report_missing_start_date():
    _, stderr = _run_script([])
    assert "error: the following arguments are required: --start_date" in str(stderr)


def test_fetch_test_results_report_missing_output_file():
    _, stderr = _run_script(["--start_date", "2023-01-01"])
    assert "error: the following arguments are required: --output_file" in str(stderr)


def test_fetch_test_results_report_invalid_start_date():
    _, stderr = _run_script(
        ["--start_date", "2023.01.15", "--output_file", "output.csv"]
    )
    assert "Date 2023.01.15 is not in the correct format: %Y-%m-%d" in str(stderr)


def test_fetch_test_results_report(generator: DataGenerator, test_client: TestClient):
    artefact = generator.gen_artefact(StageName.beta)
    artefact_build = generator.gen_artefact_build(artefact)
    environment = generator.gen_environment()
    test_execution = generator.gen_test_execution(artefact_build, environment)
    test_case = generator.gen_test_case()
    generator.gen_test_result(test_case, test_execution)

    fetch_test_results_report(
        datetime.now() - timedelta(days=1),
        datetime.now() + timedelta(days=1),
        "output.csv",
        test_client,
    )

    _verify_csv_file("output.csv")
    _clean_files_created("output.csv")
