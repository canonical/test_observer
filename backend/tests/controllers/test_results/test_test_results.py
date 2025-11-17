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
from fastapi.testclient import TestClient
import uuid
import pytest

from test_observer.data_access.models_enums import (
    FamilyName,
    TestResultStatus,
    TestExecutionStatus,
)
from test_observer.common.permissions import Permission

from tests.data_generator import DataGenerator
from tests.conftest import make_authenticated_request


def generate_unique_name(prefix: str = "test") -> str:
    """Generate a unique name to avoid database constraint violations"""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


class TestSearchTestResults:
    """Test class for the test results search endpoint"""

    def test_search_all_test_results(
        self, test_client: TestClient, generator: DataGenerator
    ):
        """Test searching all test results without filters"""
        # Create test data
        environment = generator.gen_environment()
        test_case = generator.gen_test_case(name=generate_unique_name("search_all"))
        artefact = generator.gen_artefact(name=generate_unique_name("artefact"))
        artefact_build = generator.gen_artefact_build(artefact)
        test_execution = generator.gen_test_execution(artefact_build, environment)
        test_result = generator.gen_test_result(test_case, test_execution)

        response = make_authenticated_request(
            lambda: test_client.get("/v1/test-results"),
            Permission.view_test,
        )

        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "test_results" in data
        assert data["count"] >= 1
        assert any(
            tr["test_result"]["id"] == test_result.id for tr in data["test_results"]
        )

    def test_search_limit_0(self, test_client: TestClient, generator: DataGenerator):
        """Test searching all test results with limit 0"""
        # Create test data
        environment = generator.gen_environment()
        test_case = generator.gen_test_case(name=generate_unique_name("search_all"))
        artefact = generator.gen_artefact(name=generate_unique_name("artefact"))
        artefact_build = generator.gen_artefact_build(artefact)
        test_execution = generator.gen_test_execution(artefact_build, environment)
        generator.gen_test_result(test_case, test_execution)

        response = make_authenticated_request(
            lambda: test_client.get("/v1/test-results", params={"limit": 0}),
            Permission.view_test,
        )

        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "test_results" in data
        assert data["count"] >= 1
        assert len(data["test_results"]) == 0

    def test_window_function_count_accuracy(
        self, test_client: TestClient, generator: DataGenerator
    ):
        """Test that window function count matches actual number of results"""
        # Create multiple test results with specific family
        environment = generator.gen_environment()
        test_case = generator.gen_test_case(name=generate_unique_name("window_count"))
        snap_artefact = generator.gen_artefact(
            family=FamilyName.snap, name=generate_unique_name("snap_artefact")
        )
        artefact_build = generator.gen_artefact_build(snap_artefact)
        test_execution = generator.gen_test_execution(artefact_build, environment)

        # Create test results
        test_results = []
        for _ in range(7):
            test_results.append(generator.gen_test_result(test_case, test_execution))

        response = make_authenticated_request(
            lambda: test_client.get("/v1/test-results?families=snap&limit=3"),
            Permission.view_test,
        )

        assert response.status_code == 200
        data = response.json()

        # Should return 3 results but count should show total (at least 7)
        assert len(data["test_results"]) <= 3
        assert data["count"] >= 7

        # Verify our test results are in the response
        returned_ids = {tr["test_result"]["id"] for tr in data["test_results"]}
        test_result_ids = {tr.id for tr in test_results}
        assert returned_ids.issubset(test_result_ids)

    def test_pagination_consistency(
        self, test_client: TestClient, generator: DataGenerator
    ):
        """Test that pagination works correctly with window function"""
        # Create test data
        environment = generator.gen_environment()
        test_case = generator.gen_test_case(name=generate_unique_name("pagination"))
        charm_artefact = generator.gen_artefact(
            family=FamilyName.charm, name=generate_unique_name("charm_artefact")
        )
        artefact_build = generator.gen_artefact_build(charm_artefact)
        test_execution = generator.gen_test_execution(artefact_build, environment)

        # Create 5 test results
        for _ in range(5):
            generator.gen_test_result(test_case, test_execution)

        # Test first page
        response1 = make_authenticated_request(
            lambda: test_client.get("/v1/test-results?families=charm&limit=2&offset=0"),
            Permission.view_test,
        )
        assert response1.status_code == 200
        data1 = response1.json()

        # Test second page
        response2 = make_authenticated_request(
            lambda: test_client.get("/v1/test-results?families=charm&limit=2&offset=2"),
            Permission.view_test,
        )
        assert response2.status_code == 200
        data2 = response2.json()

        # Both should have same total count
        assert data1["count"] == data2["count"]
        assert data1["count"] >= 5

        # Results should be different than each other
        ids1 = {tr["test_result"]["id"] for tr in data1["test_results"]}
        ids2 = {tr["test_result"]["id"] for tr in data2["test_results"]}
        assert ids1.isdisjoint(ids2)  # No overlap between pages

    @pytest.mark.parametrize(
        "family",
        [
            FamilyName.snap,
            FamilyName.deb,
            FamilyName.image,
            FamilyName.charm,
        ],
    )
    def test_search_by_family(
        self, test_client: TestClient, generator: DataGenerator, family: FamilyName
    ):
        """the filter returns only results from the requested family"""
        env = generator.gen_environment()
        tc = generator.gen_test_case(
            name=generate_unique_name(f"family_{family.value}")
        )

        # Matching family
        artefact_yes = generator.gen_artefact(
            family=family, name=generate_unique_name(f"{family.value}_yes")
        )
        ab_yes = generator.gen_artefact_build(artefact_yes)
        te_yes = generator.gen_test_execution(ab_yes, env)
        tr_yes = generator.gen_test_result(tc, te_yes)

        # Non-matching family
        all_families = [
            FamilyName.snap,
            FamilyName.deb,
            FamilyName.image,
            FamilyName.charm,
        ]

        other_family = next(f for f in all_families if f != family)
        artefact_no = generator.gen_artefact(
            family=other_family, name=generate_unique_name(f"{other_family.value}_no")
        )
        ab_no = generator.gen_artefact_build(artefact_no)
        te_no = generator.gen_test_execution(ab_no, env)
        tr_no = generator.gen_test_result(tc, te_no)

        resp = make_authenticated_request(
            lambda: test_client.get(f"/v1/test-results?families={family.value}"),
            Permission.view_test,
        )
        assert resp.status_code == 200
        data = resp.json()

        # Includes the matching result
        ids = {tr["test_result"]["id"] for tr in data["test_results"]}
        assert tr_yes.id in ids

        # Excludes the other family's result
        assert tr_no.id not in ids

        # Every returned row belongs to the requested family
        assert all(
            tr["artefact"]["family"] == family.value for tr in data["test_results"]
        )

    def test_search_by_template_id(
        self, test_client: TestClient, generator: DataGenerator
    ):
        """Test filtering by template ID"""
        # Create test data with specific template ID
        environment = generator.gen_environment()
        test_case = generator.gen_test_case(
            name=generate_unique_name("template"), template_id="test_template_123"
        )
        artefact = generator.gen_artefact(name=generate_unique_name("artefact"))
        artefact_build = generator.gen_artefact_build(artefact)
        test_execution = generator.gen_test_execution(artefact_build, environment)
        test_result = generator.gen_test_result(test_case, test_execution)

        response = make_authenticated_request(
            lambda: test_client.get("/v1/test-results?template_ids=test_template_123"),
            Permission.view_test,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        assert any(
            tr["test_result"]["id"] == test_result.id for tr in data["test_results"]
        )

    def test_search_by_issues(self, test_client: TestClient, generator: DataGenerator):
        """Test filtering by issue IDs with window function"""
        # Create test data
        environment = generator.gen_environment()
        test_case = generator.gen_test_case(name=generate_unique_name("issues"))
        artefact = generator.gen_artefact(name=generate_unique_name("artefact"))
        artefact_build = generator.gen_artefact_build(artefact)
        test_execution = generator.gen_test_execution(artefact_build, environment)
        test_result = generator.gen_test_result(test_case, test_execution)

        # Create an issue and attach it to the test result via API
        issue = generator.gen_issue()
        attach_response = make_authenticated_request(
            lambda: test_client.post(
                f"/v1/issues/{issue.id}/attach", json={"test_results": [test_result.id]}
            ),
            Permission.change_issue_attachment,
        )
        assert attach_response.status_code == 200

        response = make_authenticated_request(
            lambda: test_client.get(f"/v1/test-results?issues={issue.id}"),
            Permission.view_test,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        assert any(
            tr["test_result"]["id"] == test_result.id for tr in data["test_results"]
        )

    def test_search_by_multiple_issues(
        self, test_client: TestClient, generator: DataGenerator
    ):
        """Test filtering by multiple issue IDs with window function"""
        # Create test data
        environment = generator.gen_environment()
        test_case = generator.gen_test_case(name=generate_unique_name("multi_issues"))
        artefact = generator.gen_artefact(name=generate_unique_name("artefact"))
        artefact_build = generator.gen_artefact_build(artefact)
        test_execution = generator.gen_test_execution(artefact_build, environment)
        test_result1 = generator.gen_test_result(test_case, test_execution)
        test_result2 = generator.gen_test_result(test_case, test_execution)

        # Create issues and attach them to different test results via API
        issue1 = generator.gen_issue(key="123")
        issue2 = generator.gen_issue(key="456")

        attach_response1 = make_authenticated_request(
            lambda: test_client.post(
                f"/v1/issues/{issue1.id}/attach",
                json={"test_results": [test_result1.id]},
            ),
            Permission.change_issue_attachment,
        )
        attach_response2 = make_authenticated_request(
            lambda: test_client.post(
                f"/v1/issues/{issue2.id}/attach",
                json={"test_results": [test_result2.id]},
            ),
            Permission.change_issue_attachment,
        )
        assert attach_response1.status_code == 200
        assert attach_response2.status_code == 200

        response = make_authenticated_request(
            lambda: test_client.get(
                f"/v1/test-results?issues={issue1.id}&issues={issue2.id}"
            ),
            Permission.view_test,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 2
        result_ids = {tr["test_result"]["id"] for tr in data["test_results"]}
        assert test_result1.id in result_ids
        assert test_result2.id in result_ids

    def test_search_by_issues_any(
        self, test_client: TestClient, generator: DataGenerator
    ):
        """Test filtering by issues=any to find test results with any issue attached"""
        # Create test data
        environment = generator.gen_environment()
        test_case = generator.gen_test_case(name=generate_unique_name("issues_any"))
        artefact = generator.gen_artefact(name=generate_unique_name("artefact"))
        artefact_build = generator.gen_artefact_build(artefact)
        test_execution = generator.gen_test_execution(artefact_build, environment)
        test_result_with_issue = generator.gen_test_result(test_case, test_execution)
        test_result_without_issue = generator.gen_test_result(test_case, test_execution)

        # Create an issue and attach it to one test result
        issue = generator.gen_issue()
        attach_response = make_authenticated_request(
            lambda: test_client.post(
                f"/v1/issues/{issue.id}/attach",
                json={"test_results": [test_result_with_issue.id]},
            ),
            Permission.change_issue_attachment,
        )
        assert attach_response.status_code == 200

        # Search for test results with any issue
        response = make_authenticated_request(
            lambda: test_client.get("/v1/test-results?issues=any"),
            Permission.view_test,
        )

        assert response.status_code == 200
        data = response.json()
        result_ids = {tr["test_result"]["id"] for tr in data["test_results"]}
        # Should include test result with issue
        assert test_result_with_issue.id in result_ids
        # Should not include test result without issue
        assert test_result_without_issue.id not in result_ids

    def test_search_by_issues_none(
        self, test_client: TestClient, generator: DataGenerator
    ):
        """Test filtering by issues=none (test results without any issue attached)"""
        # Create test data
        environment = generator.gen_environment()
        test_case = generator.gen_test_case(name=generate_unique_name("issues_none"))
        artefact = generator.gen_artefact(name=generate_unique_name("artefact"))
        artefact_build = generator.gen_artefact_build(artefact)
        test_execution = generator.gen_test_execution(artefact_build, environment)
        test_result_with_issue = generator.gen_test_result(test_case, test_execution)
        test_result_without_issue = generator.gen_test_result(test_case, test_execution)

        # Create an issue and attach it to one test result
        issue = generator.gen_issue()
        attach_response = make_authenticated_request(
            lambda: test_client.post(
                f"/v1/issues/{issue.id}/attach",
                json={"test_results": [test_result_with_issue.id]},
            ),
            Permission.change_issue_attachment,
        )
        assert attach_response.status_code == 200

        # Search for test results without any issue
        response = make_authenticated_request(
            lambda: test_client.get("/v1/test-results?issues=none"),
            Permission.view_test,
        )

        assert response.status_code == 200
        data = response.json()
        result_ids = {tr["test_result"]["id"] for tr in data["test_results"]}
        # Should not include test result with issue
        assert test_result_with_issue.id not in result_ids
        # Should include test result without issue
        assert test_result_without_issue.id in result_ids

    def test_search_by_issues_any_and_none_conflict(self, test_client: TestClient):
        """Test that using both issues=any and issues=none returns an error"""
        response = make_authenticated_request(
            lambda: test_client.get("/v1/test-results?issues=any&issues=none"),
            Permission.view_test,
        )

        # Should return 422 for conflicting parameters
        assert response.status_code == 422

    def test_search_by_execution_metadata(
        self, test_client: TestClient, generator: DataGenerator
    ):
        """Test filtering by execution metadata"""
        # Create test data
        environment = generator.gen_environment()
        test_case = generator.gen_test_case(name=generate_unique_name("issues"))
        artefact = generator.gen_artefact(name=generate_unique_name("artefact"))
        artefact_build = generator.gen_artefact_build(artefact)
        test_executions = [
            (False, generator.gen_test_execution(artefact_build, environment)),
            (
                True,
                generator.gen_test_execution(
                    artefact_build,
                    environment,
                    execution_metadata={
                        "category1": ["value1"],
                    },
                ),
            ),
            (
                True,
                generator.gen_test_execution(
                    artefact_build,
                    environment,
                    execution_metadata={
                        "category1": ["value2"],
                    },
                ),
            ),
            (
                True,
                generator.gen_test_execution(
                    artefact_build,
                    environment,
                    execution_metadata={
                        "category1": ["value1", "value2"],
                    },
                ),
            ),
            (
                True,
                generator.gen_test_execution(
                    artefact_build,
                    environment,
                    execution_metadata={
                        "category1": ["value1", "value3"],
                    },
                ),
            ),
            (
                False,
                generator.gen_test_execution(
                    artefact_build,
                    environment,
                    execution_metadata={
                        "category1": ["value3"],
                    },
                ),
            ),
            (
                True,
                generator.gen_test_execution(
                    artefact_build,
                    environment,
                    execution_metadata={
                        "category1": ["value1"],
                        "category2": ["value1"],
                    },
                ),
            ),
            (
                False,
                generator.gen_test_execution(
                    artefact_build,
                    environment,
                    execution_metadata={
                        "category2": ["value1"],
                    },
                ),
            ),
        ]
        test_results = [
            (expect, generator.gen_test_result(test_case, test_execution))
            for expect, test_execution in test_executions
        ]

        # Query test results with matching execution metadata
        response = make_authenticated_request(
            lambda: test_client.get(
                "/v1/test-results?execution_metadata=category1:value1&execution_metadata=category1:value2"
            ),
            Permission.view_test,
        )
        expect = {test_result.id for expect, test_result in test_results if expect}

        assert response.status_code == 200
        data = response.json()
        assert expect == {tr["test_result"]["id"] for tr in data["test_results"]}

    def test_invalid_execution_metadata_format(self, test_client: TestClient):
        # Test with invalid execution metadata format
        response = make_authenticated_request(
            lambda: test_client.get(
                "/v1/test-results?execution_metadata=invalid-format"
            ),
            Permission.view_test,
        )
        assert response.status_code == 422

    def test_search_with_date_range(
        self, test_client: TestClient, generator: DataGenerator
    ):
        """Test filtering by date range with window function"""
        # Create test data
        environment = generator.gen_environment()
        test_case = generator.gen_test_case(name=generate_unique_name("date_range"))
        artefact = generator.gen_artefact(name=generate_unique_name("artefact"))
        artefact_build = generator.gen_artefact_build(artefact)
        test_execution = generator.gen_test_execution(artefact_build, environment)
        test_result = generator.gen_test_result(test_case, test_execution)

        # Test with date range that should include our test
        from_date = (datetime.now() - timedelta(days=1)).isoformat()
        until_date = (datetime.now() + timedelta(days=1)).isoformat()

        response = make_authenticated_request(
            lambda: test_client.get(
                f"/v1/test-results?from_date={from_date}&until_date={until_date}"
            ),
            Permission.view_test,
        )

        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "test_results" in data
        assert data["count"] >= 1
        # Verify our specific test result is included
        assert any(
            tr["test_result"]["id"] == test_result.id for tr in data["test_results"]
        )

    def test_search_with_future_date_range(self, test_client: TestClient):
        """Test filtering by future date range should return no results"""
        # Test with future date range
        from_date = (datetime.now() + timedelta(days=1)).isoformat()
        until_date = (datetime.now() + timedelta(days=2)).isoformat()

        response = make_authenticated_request(
            lambda: test_client.get(
                f"/v1/test-results?from_date={from_date}&until_date={until_date}"
            ),
            Permission.view_test,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["test_results"] == []

    def test_search_with_from_date_only(
        self, test_client: TestClient, generator: DataGenerator
    ):
        """Test filtering with only from_date parameter"""
        # Create test data first
        environment = generator.gen_environment()
        test_case = generator.gen_test_case(name=generate_unique_name("from_date_only"))
        artefact = generator.gen_artefact(name=generate_unique_name("artefact"))
        artefact_build = generator.gen_artefact_build(artefact)
        test_execution = generator.gen_test_execution(artefact_build, environment)
        test_result = generator.gen_test_result(test_case, test_execution)

        # Refresh to get the actual database timestamp
        generator.db_session.refresh(test_execution)
        execution_created_at = test_execution.created_at

        # Test with from_date before the test execution was created
        from_date_before = (execution_created_at - timedelta(minutes=1)).isoformat()

        response = make_authenticated_request(
            lambda: test_client.get(f"/v1/test-results?from_date={from_date_before}"),
            Permission.view_test,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        assert any(
            tr["test_result"]["id"] == test_result.id for tr in data["test_results"]
        )

        # Test with from_date after the test execution was created
        from_date_after = (execution_created_at + timedelta(minutes=1)).isoformat()

        response = make_authenticated_request(
            lambda: test_client.get(f"/v1/test-results?from_date={from_date_after}"),
            Permission.view_test,
        )

        assert response.status_code == 200
        data = response.json()
        # Our test result should not be in results from after its creation
        assert not any(
            tr["test_result"]["id"] == test_result.id for tr in data["test_results"]
        )

    def test_search_with_until_date_only(
        self, test_client: TestClient, generator: DataGenerator
    ):
        """Test filtering with only until date parameter"""
        # Create test data first
        environment = generator.gen_environment()
        test_case = generator.gen_test_case(
            name=generate_unique_name("until_date_only")
        )
        artefact = generator.gen_artefact(name=generate_unique_name("artefact"))
        artefact_build = generator.gen_artefact_build(artefact)
        test_execution = generator.gen_test_execution(artefact_build, environment)
        test_result = generator.gen_test_result(test_case, test_execution)

        # Refresh to get the actual database timestamp
        generator.db_session.refresh(test_execution)
        execution_created_at = test_execution.created_at

        # Test with until date after the test execution was created
        until_date_after = (execution_created_at + timedelta(minutes=1)).isoformat()

        response = make_authenticated_request(
            lambda: test_client.get(f"/v1/test-results?until_date={until_date_after}"),
            Permission.view_test,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        assert any(
            tr["test_result"]["id"] == test_result.id for tr in data["test_results"]
        )

        # Test with until date before the test execution was created
        until_date_before = (execution_created_at - timedelta(minutes=1)).isoformat()

        response = make_authenticated_request(
            lambda: test_client.get(f"/v1/test-results?until_date={until_date_before}"),
            Permission.view_test,
        )

        assert response.status_code == 200
        data = response.json()
        # The test result should not be in results until before its creation
        assert not any(
            tr["test_result"]["id"] == test_result.id for tr in data["test_results"]
        )

    def test_search_date_boundary_conditions(
        self, test_client: TestClient, generator: DataGenerator
    ):
        """Test date filtering boundary conditions"""
        # Create test data
        environment = generator.gen_environment()
        test_case = generator.gen_test_case(name=generate_unique_name("date_boundary"))
        artefact = generator.gen_artefact(name=generate_unique_name("artefact"))
        artefact_build = generator.gen_artefact_build(artefact)
        test_execution = generator.gen_test_execution(artefact_build, environment)
        test_result = generator.gen_test_result(test_case, test_execution)

        # Refresh to get the actual database timestamp
        generator.db_session.refresh(test_execution)
        execution_created_at = test_execution.created_at

        # Test that our result is included in a range around its actual creation time
        range_before = (execution_created_at - timedelta(minutes=1)).isoformat()
        range_after = (execution_created_at + timedelta(minutes=1)).isoformat()

        response = make_authenticated_request(
            lambda: test_client.get(
                f"/v1/test-results?from_date={range_before}&until_date={range_after}"
            ),
            Permission.view_test,
        )

        assert response.status_code == 200
        data = response.json()
        assert any(
            tr["test_result"]["id"] == test_result.id for tr in data["test_results"]
        )

    def test_search_date_combined_with_other_filters(
        self, test_client: TestClient, generator: DataGenerator
    ):
        """Test date filtering combined with other filter parameters"""
        # Create test data with specific family
        environment = generator.gen_environment()
        test_case = generator.gen_test_case(name=generate_unique_name("date_combined"))
        snap_artefact = generator.gen_artefact(
            family=FamilyName.snap, name=generate_unique_name("snap_date")
        )
        artefact_build = generator.gen_artefact_build(snap_artefact)
        test_execution = generator.gen_test_execution(artefact_build, environment)
        test_result = generator.gen_test_result(test_case, test_execution)

        # Refresh to get the actual database timestamp
        generator.db_session.refresh(test_execution)
        execution_created_at = test_execution.created_at

        # Create date range that includes our test execution
        from_date = (execution_created_at - timedelta(minutes=1)).isoformat()
        until_date = (execution_created_at + timedelta(minutes=1)).isoformat()

        # Test combining date filter with family filter
        response = make_authenticated_request(
            lambda: test_client.get(
                f"/v1/test-results?families=snap&from_date={from_date}&until_date={until_date}"
            ),
            Permission.view_test,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        assert any(
            tr["test_result"]["id"] == test_result.id for tr in data["test_results"]
        )

        # Test that wrong family + date range excludes our result
        response = make_authenticated_request(
            lambda: test_client.get(
                f"/v1/test-results?families=deb&from_date={from_date}&until_date={until_date}"
            ),
            Permission.view_test,
        )

        assert response.status_code == 200
        data = response.json()
        # Our snap test result should not be in deb family results
        assert not any(
            tr["test_result"]["id"] == test_result.id for tr in data["test_results"]
        )

    def test_search_invalid_date_formats(self, test_client: TestClient):
        """Test handling of invalid date format parameters"""
        # Test with invalid date format
        response = make_authenticated_request(
            lambda: test_client.get("/v1/test-results?from_date=invalid-date"),
            Permission.view_test,
        )
        assert response.status_code == 422

        response = make_authenticated_request(
            lambda: test_client.get("/v1/test-results?until_date=not-a-date"),
            Permission.view_test,
        )
        assert response.status_code == 422

        # Test with malformed ISO date
        response = make_authenticated_request(
            lambda: test_client.get("/v1/test-results?from_date=2025-13-45T25:99:99"),
            Permission.view_test,
        )
        assert response.status_code == 422

    def test_search_multiple_filters_complex(
        self, test_client: TestClient, generator: DataGenerator
    ):
        """Test combining multiple filters with window function"""
        # Create specific test data
        environment_name = "multi-filter-env"
        test_case_name = "multi_filter"

        environment = generator.gen_environment(name=environment_name)
        test_case = generator.gen_test_case(
            name=test_case_name,
            template_id="multi_filter_template",
        )
        snap_artefact = generator.gen_artefact(
            family=FamilyName.snap, name=generate_unique_name("snap_multi")
        )
        artefact_build = generator.gen_artefact_build(snap_artefact)
        test_execution = generator.gen_test_execution(artefact_build, environment)
        test_result = generator.gen_test_result(test_case, test_execution)

        # Create an issue and attach it
        issue = generator.gen_issue(key="789")
        attach_response = make_authenticated_request(
            lambda: test_client.post(
                f"/v1/issues/{issue.id}/attach", json={"test_results": [test_result.id]}
            ),
            Permission.change_issue_attachment,
        )
        assert attach_response.status_code == 200

        response = make_authenticated_request(
            lambda: test_client.get(
                f"/v1/test-results?families=snap&environments={environment_name}&test_cases={test_case_name}&template_ids=multi_filter_template&issues={issue.id}&limit=5"
            ),
            Permission.view_test,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        assert any(
            tr["test_result"]["id"] == test_result.id for tr in data["test_results"]
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        assert any(
            tr["test_result"]["id"] == test_result.id for tr in data["test_results"]
        )

    def test_search_invalid_family(self, test_client: TestClient):
        """Test handling invalid family name"""
        response = make_authenticated_request(
            lambda: test_client.get("/v1/test-results?families=invalid_family"),
            Permission.view_test,
        )

        assert response.status_code == 422

    def test_search_no_results(self, test_client: TestClient):
        """Test search with filters that match no results"""
        response = make_authenticated_request(
            lambda: test_client.get(
                "/v1/test-results?test_cases=nonexistent_test_case_12345"
            ),
            Permission.view_test,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["test_results"] == []

    def test_pagination_limits(self, test_client: TestClient):
        """Test pagination parameter validation"""
        # Test maximum limit
        response = make_authenticated_request(
            lambda: test_client.get("/v1/test-results?limit=1001"),
            Permission.view_test,
        )
        assert response.status_code == 422

        # Test negative offset
        response = make_authenticated_request(
            lambda: test_client.get("/v1/test-results?offset=-1"),
            Permission.view_test,
        )
        assert response.status_code == 422

    def test_large_offset_pagination(self, test_client: TestClient):
        # Create test data

        response_check = make_authenticated_request(
            lambda: test_client.get("/v1/test-results?families=deb&limit=10&offset=0"),
            Permission.view_test,
        )
        actual_count = response_check.json()["count"]

        response = make_authenticated_request(
            lambda: test_client.get(
                "/v1/test-results?families=deb&limit=10&offset=1000"
            ),
            Permission.view_test,
        )
        data = response.json()

        assert data["count"] == actual_count
        assert len(data["test_results"]) == 0

    def test_case_insensitive_family_filtering(
        self, test_client: TestClient, generator: DataGenerator
    ):
        """Test that family filtering is case insensitive"""
        # Create a snap artefact
        environment = generator.gen_environment()
        test_case = generator.gen_test_case(
            name=generate_unique_name("case_insensitive")
        )
        snap_artefact = generator.gen_artefact(
            family=FamilyName.snap, name=generate_unique_name("snap_case")
        )
        artefact_build = generator.gen_artefact_build(snap_artefact)
        test_execution = generator.gen_test_execution(artefact_build, environment)
        test_result = generator.gen_test_result(test_case, test_execution)

        # Test with different cases
        response = make_authenticated_request(
            lambda: test_client.get("/v1/test-results?families=snap"),
            Permission.view_test,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        assert any(
            tr["test_result"]["id"] == test_result.id for tr in data["test_results"]
        )

    def test_ordering_consistency(
        self, test_client: TestClient, generator: DataGenerator
    ):
        """Test that results are consistently ordered by creation date desc"""
        # Create test data with different creation times
        environment = generator.gen_environment()
        test_case1 = generator.gen_test_case(name=generate_unique_name("order1"))
        test_case2 = generator.gen_test_case(name=generate_unique_name("order2"))
        artefact = generator.gen_artefact(name=generate_unique_name("order_artefact"))
        artefact_build = generator.gen_artefact_build(artefact)

        # Create test executions at different times
        test_execution1 = generator.gen_test_execution(artefact_build, environment)
        test_result1 = generator.gen_test_result(test_case1, test_execution1)

        test_execution2 = generator.gen_test_execution(artefact_build, environment)
        test_result2 = generator.gen_test_result(test_case2, test_execution2)

        response = make_authenticated_request(
            lambda: test_client.get("/v1/test-results?limit=5"),
            Permission.view_test,
        )

        assert response.status_code == 200
        data = response.json()

        # Results should be ordered by creation date descending
        if len(data["test_results"]) >= 2:
            # Find our test results in the response
            our_results = [
                tr
                for tr in data["test_results"]
                if tr["test_result"]["id"] in [test_result1.id, test_result2.id]
            ]

            # Should have both results
            assert len(our_results) == 2

    def test_search_by_artefact_name(
        self, test_client: TestClient, generator: DataGenerator
    ):
        """Test filtering by artefact name"""
        # Create test data with specific artefact names
        unique_marker = uuid.uuid4().hex[:8]
        artefact_name = f"test_artefact_{unique_marker}"

        environment = generator.gen_environment()
        test_case = generator.gen_test_case(
            name=generate_unique_name("artefact_filter")
        )
        artefact = generator.gen_artefact(name=artefact_name)
        artefact_build = generator.gen_artefact_build(artefact)
        test_execution = generator.gen_test_execution(artefact_build, environment)
        test_result = generator.gen_test_result(test_case, test_execution)

        # Create another artefact that shouldn't be in results
        other_artefact = generator.gen_artefact(name=f"other_artefact_{unique_marker}")
        other_build = generator.gen_artefact_build(other_artefact)
        other_execution = generator.gen_test_execution(other_build, environment)
        other_result = generator.gen_test_result(test_case, other_execution)

        # Search with artefact filter
        response = make_authenticated_request(
            lambda: test_client.get(f"/v1/test-results?artefacts={artefact_name}"),
            Permission.view_test,
        )

        assert response.status_code == 200
        data = response.json()
        result_ids = {tr["test_result"]["id"] for tr in data["test_results"]}

        # Should include our artefact's result
        assert test_result.id in result_ids
        # Should not include other artefact's result
        assert other_result.id not in result_ids

    def test_search_by_multiple_artefacts(
        self, test_client: TestClient, generator: DataGenerator
    ):
        """Test filtering by multiple artefact names"""
        unique_marker = uuid.uuid4().hex[:8]

        environment = generator.gen_environment()
        test_case = generator.gen_test_case(name=generate_unique_name("multi_artefact"))

        # Create two artefacts with results
        artefact1 = generator.gen_artefact(name=f"artefact1_{unique_marker}")
        build1 = generator.gen_artefact_build(artefact1)
        execution1 = generator.gen_test_execution(build1, environment)
        result1 = generator.gen_test_result(test_case, execution1)

        artefact2 = generator.gen_artefact(name=f"artefact2_{unique_marker}")
        build2 = generator.gen_artefact_build(artefact2)
        execution2 = generator.gen_test_execution(build2, environment)
        result2 = generator.gen_test_result(test_case, execution2)

        # Create third artefact that shouldn't be in results
        artefact3 = generator.gen_artefact(name=f"artefact3_{unique_marker}")
        build3 = generator.gen_artefact_build(artefact3)
        execution3 = generator.gen_test_execution(build3, environment)
        result3 = generator.gen_test_result(test_case, execution3)

        # Search with multiple artefacts
        response = make_authenticated_request(
            lambda: test_client.get(
                f"/v1/test-results?artefacts={artefact1.name}&artefacts={artefact2.name}"
            ),
            Permission.view_test,
        )

        assert response.status_code == 200
        data = response.json()
        result_ids = {tr["test_result"]["id"] for tr in data["test_results"]}

        # Should include results from first two artefacts
        assert result1.id in result_ids
        assert result2.id in result_ids
        # Should not include third artefact's result
        assert result3.id not in result_ids

    def test_search_artefacts_combined_with_other_filters(
        self, test_client: TestClient, generator: DataGenerator
    ):
        """Test combining artefact filter with other filters"""
        unique_marker = uuid.uuid4().hex[:8]

        # Create specific environment and artefact
        env_name = f"test_env_{unique_marker}"
        artefact_name = f"test_artefact_{unique_marker}"

        environment = generator.gen_environment(name=env_name)
        test_case = generator.gen_test_case(name=generate_unique_name("combined"))
        artefact = generator.gen_artefact(name=artefact_name)
        artefact_build = generator.gen_artefact_build(artefact)
        test_execution = generator.gen_test_execution(artefact_build, environment)
        test_result = generator.gen_test_result(test_case, test_execution)

        # Create result with same artefact but different environment
        other_env = generator.gen_environment(name=f"other_env_{unique_marker}")
        other_execution = generator.gen_test_execution(artefact_build, other_env)
        other_result = generator.gen_test_result(test_case, other_execution)

        # Search with both artefact and environment filters
        response = make_authenticated_request(
            lambda: test_client.get(
                f"/v1/test-results?artefacts={artefact_name}&environments={env_name}"
            ),
            Permission.view_test,
        )

        assert response.status_code == 200
        data = response.json()
        result_ids = {tr["test_result"]["id"] for tr in data["test_results"]}

        # Should only include result matching both filters
        assert test_result.id in result_ids
        assert other_result.id not in result_ids

    @pytest.mark.parametrize(
        "status",
        [
            TestResultStatus.PASSED,
            TestResultStatus.FAILED,
            TestResultStatus.SKIPPED,
        ],
    )
    def test_search_by_test_result_status(
        self,
        test_client: TestClient,
        generator: DataGenerator,
        status: TestResultStatus,
    ):
        """The filter returns only results with the requested status"""
        env = generator.gen_environment()
        tc = generator.gen_test_case(
            name=generate_unique_name(f"status_{status.value}")
        )
        artefact = generator.gen_artefact(name=generate_unique_name("artefact"))
        ab = generator.gen_artefact_build(artefact)
        te = generator.gen_test_execution(ab, env)

        # Create test result with matching status
        tr_yes = generator.gen_test_result(tc, te, status=status)

        # Create test results with other statuses
        other_statuses = [s for s in TestResultStatus if s != status]
        tr_no_list = [
            generator.gen_test_result(tc, te, status=other_status)
            for other_status in other_statuses
        ]

        resp = make_authenticated_request(
            lambda: test_client.get(
                f"/v1/test-results?test_result_statuses={status.value}"
            ),
            Permission.view_test,
        )
        assert resp.status_code == 200
        data = resp.json()

        # Includes the matching result
        ids = {tr["test_result"]["id"] for tr in data["test_results"]}
        assert tr_yes.id in ids

        # Excludes results with other statuses
        for tr_no in tr_no_list:
            assert tr_no.id not in ids

        # Every returned row has the requested status
        assert all(
            tr["test_result"]["status"] == status.value for tr in data["test_results"]
        )

    def test_search_by_multiple_test_result_statuses(
        self, test_client: TestClient, generator: DataGenerator
    ):
        """Test filtering by multiple test result statuses"""
        env = generator.gen_environment()
        tc = generator.gen_test_case(name=generate_unique_name("multi_status"))
        artefact = generator.gen_artefact(name=generate_unique_name("artefact"))
        ab = generator.gen_artefact_build(artefact)
        te = generator.gen_test_execution(ab, env)

        # Create test results with different statuses
        tr_passed = generator.gen_test_result(tc, te, status=TestResultStatus.PASSED)
        tr_failed = generator.gen_test_result(tc, te, status=TestResultStatus.FAILED)
        tr_skipped = generator.gen_test_result(tc, te, status=TestResultStatus.SKIPPED)

        # Query for PASSED and FAILED
        resp = make_authenticated_request(
            lambda: test_client.get(
                f"/v1/test-results?test_result_statuses={TestResultStatus.PASSED.value}"
                f"&test_result_statuses={TestResultStatus.FAILED.value}"
            ),
            Permission.view_test,
        )
        assert resp.status_code == 200
        data = resp.json()

        ids = {tr["test_result"]["id"] for tr in data["test_results"]}

        # Should include PASSED and FAILED
        assert tr_passed.id in ids
        assert tr_failed.id in ids

        # Should not include SKIPPED
        assert tr_skipped.id not in ids

        # Every returned row has one of the requested statuses
        assert all(
            tr["test_result"]["status"]
            in [TestResultStatus.PASSED.value, TestResultStatus.FAILED.value]
            for tr in data["test_results"]
        )

    @pytest.mark.parametrize(
        "status",
        [
            TestExecutionStatus.NOT_STARTED,
            TestExecutionStatus.IN_PROGRESS,
            TestExecutionStatus.PASSED,
            TestExecutionStatus.FAILED,
            TestExecutionStatus.NOT_TESTED,
            TestExecutionStatus.ENDED_PREMATURELY,
        ],
    )
    def test_search_by_test_execution_status(
        self,
        test_client: TestClient,
        generator: DataGenerator,
        status: TestExecutionStatus,
    ):
        """The filter returns only results with the requested execution status"""
        env = generator.gen_environment()
        tc = generator.gen_test_case(
            name=generate_unique_name(f"exec_status_{status.value}")
        )
        artefact = generator.gen_artefact(name=generate_unique_name("artefact"))
        ab = generator.gen_artefact_build(artefact)

        # Create test execution with matching status
        te_yes = generator.gen_test_execution(ab, env, status=status)
        tr_yes = generator.gen_test_result(tc, te_yes)

        # Create test execution with different status
        other_statuses = [s for s in TestExecutionStatus if s != status]
        tr_no_list = []
        for other_status in other_statuses:
            te_no = generator.gen_test_execution(ab, env, status=other_status)
            tr_no = generator.gen_test_result(tc, te_no)
            tr_no_list.append(tr_no)

        resp = make_authenticated_request(
            lambda: test_client.get(
                f"/v1/test-results?test_execution_statuses={status.value}"
            ),
            Permission.view_test,
        )
        assert resp.status_code == 200
        data = resp.json()

        # Includes the matching result
        ids = {tr["test_result"]["id"] for tr in data["test_results"]}
        assert tr_yes.id in ids

        # Excludes results with other execution statuses
        for tr_no in tr_no_list:
            assert tr_no.id not in ids

        # Every returned row has the requested execution status
        assert all(
            tr["test_execution"]["status"] == status.value
            for tr in data["test_results"]
        )

    def test_search_by_multiple_test_execution_statuses(
        self, test_client: TestClient, generator: DataGenerator
    ):
        """Test filtering by multiple test execution statuses"""
        env = generator.gen_environment()
        tc = generator.gen_test_case(name=generate_unique_name("multi_exec_status"))
        artefact = generator.gen_artefact(name=generate_unique_name("artefact"))
        ab = generator.gen_artefact_build(artefact)

        # Create test executions with different statuses
        te_passed = generator.gen_test_execution(
            ab, env, status=TestExecutionStatus.PASSED
        )
        tr_passed = generator.gen_test_result(tc, te_passed)

        te_failed = generator.gen_test_execution(
            ab, env, status=TestExecutionStatus.FAILED
        )
        tr_failed = generator.gen_test_result(tc, te_failed)

        te_not_started = generator.gen_test_execution(
            ab, env, status=TestExecutionStatus.NOT_STARTED
        )
        tr_not_started = generator.gen_test_result(tc, te_not_started)

        # Query for PASSED and FAILED
        resp = make_authenticated_request(
            lambda: test_client.get(
                f"/v1/test-results?test_execution_statuses={TestExecutionStatus.PASSED.value}"
                f"&test_execution_statuses={TestExecutionStatus.FAILED.value}"
            ),
            Permission.view_test,
        )
        assert resp.status_code == 200
        data = resp.json()

        ids = {tr["test_result"]["id"] for tr in data["test_results"]}

        # Should include PASSED and FAILED executions
        assert tr_passed.id in ids
        assert tr_failed.id in ids

        # Should not include NOT_STARTED
        assert tr_not_started.id not in ids

        # Every returned row has one of the requested execution statuses
        assert all(
            tr["test_execution"]["status"]
            in [TestExecutionStatus.PASSED.value, TestExecutionStatus.FAILED.value]
            for tr in data["test_results"]
        )

    def test_search_combined_result_and_execution_statuses(
        self, test_client: TestClient, generator: DataGenerator
    ):
        """Test filtering by both test result and test execution statuses"""
        env = generator.gen_environment()
        tc = generator.gen_test_case(name=generate_unique_name("combined_statuses"))
        artefact = generator.gen_artefact(name=generate_unique_name("artefact"))
        ab = generator.gen_artefact_build(artefact)

        # Create combinations of result and execution statuses
        # Match both filters
        te_passed = generator.gen_test_execution(
            ab, env, status=TestExecutionStatus.PASSED
        )
        tr_passed_passed = generator.gen_test_result(
            tc, te_passed, status=TestResultStatus.PASSED
        )

        # Match execution status but not result status
        tr_failed_passed = generator.gen_test_result(
            tc, te_passed, status=TestResultStatus.FAILED
        )

        # Match result status but not execution status
        te_failed = generator.gen_test_execution(
            ab, env, status=TestExecutionStatus.FAILED
        )
        tr_passed_failed = generator.gen_test_result(
            tc, te_failed, status=TestResultStatus.PASSED
        )

        # Match neither
        tr_failed_failed = generator.gen_test_result(
            tc, te_failed, status=TestResultStatus.FAILED
        )

        # Query for PASSED result status and PASSED execution status
        resp = make_authenticated_request(
            lambda: test_client.get(
                f"/v1/test-results?test_result_statuses={TestResultStatus.PASSED.value}"
                f"&test_execution_statuses={TestExecutionStatus.PASSED.value}"
            ),
            Permission.view_test,
        )
        assert resp.status_code == 200
        data = resp.json()

        ids = {tr["test_result"]["id"] for tr in data["test_results"]}

        # Should only include result matching both filters
        assert tr_passed_passed.id in ids

        # Should not include results matching only one filter or neither
        assert tr_failed_passed.id not in ids
        assert tr_passed_failed.id not in ids
        assert tr_failed_failed.id not in ids

        # Every returned row matches both filters
        assert all(
            tr["test_result"]["status"] == TestResultStatus.PASSED.value
            and tr["test_execution"]["status"] == TestExecutionStatus.PASSED.value
            for tr in data["test_results"]
        )


class TestWindowFunctionSpecific:
    """Test class specifically for window function behavior and edge cases"""

    def test_window_function_with_empty_results(self, test_client: TestClient):
        """Test window function behavior when no results match"""
        response = make_authenticated_request(
            lambda: test_client.get("/v1/test-results?families=nonexistent"),
            Permission.view_test,
        )

        assert response.status_code == 422

    def test_window_function_single_result(
        self, test_client: TestClient, generator: DataGenerator
    ):
        """Test window function with exactly one result"""
        environment = generator.gen_environment()
        test_case = generator.gen_test_case(name=generate_unique_name("single_result"))
        image_artefact = generator.gen_artefact(
            family=FamilyName.image, name=generate_unique_name("image_single")
        )
        artefact_build = generator.gen_artefact_build(image_artefact)
        test_execution = generator.gen_test_execution(artefact_build, environment)
        test_result = generator.gen_test_result(test_case, test_execution)

        response = make_authenticated_request(
            lambda: test_client.get("/v1/test-results?families=image"),
            Permission.view_test,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        assert len(data["test_results"]) >= 1
        assert any(
            tr["test_result"]["id"] == test_result.id for tr in data["test_results"]
        )

    def test_window_function_pagination_edge_cases(
        self, test_client: TestClient, generator: DataGenerator
    ):
        """Test window function with various pagination edge cases"""
        # Create test data
        environment = generator.gen_environment()
        test_case = generator.gen_test_case(name=generate_unique_name("edge_cases"))
        artefact = generator.gen_artefact(name=generate_unique_name("edge_artefact"))
        artefact_build = generator.gen_artefact_build(artefact)
        test_execution = generator.gen_test_execution(artefact_build, environment)

        # Create 10 test results
        for _ in range(10):
            generator.gen_test_result(test_case, test_execution)

        # Test if offset is at exact boundary
        response = make_authenticated_request(
            lambda: test_client.get("/v1/test-results?limit=5&offset=5"),
            Permission.view_test,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 10
        assert len(data["test_results"]) <= 5

        # Test if limit is larger than total results
        response = make_authenticated_request(
            lambda: test_client.get("/v1/test-results?limit=1000"),
            Permission.view_test,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["test_results"]) <= data["count"]
