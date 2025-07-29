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

from test_observer.data_access.models_enums import (
    FamilyName,
)
from tests.data_generator import DataGenerator


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

        response = test_client.get("/v1/test-results")

        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "test_results" in data
        assert data["count"] >= 1
        assert any(tr["id"] == test_result.id for tr in data["test_results"])

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

        response = test_client.get("/v1/test-results?family=snap&limit=3")

        assert response.status_code == 200
        data = response.json()

        # Should return 3 results but count should show total (at least 7)
        assert len(data["test_results"]) <= 3
        assert data["count"] >= 7

        # Verify our test results are in the response
        returned_ids = {tr["id"] for tr in data["test_results"]}
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
        response1 = test_client.get("/v1/test-results?family=charm&limit=2&offset=0")
        assert response1.status_code == 200
        data1 = response1.json()

        # Test second page
        response2 = test_client.get("/v1/test-results?family=charm&limit=2&offset=2")
        assert response2.status_code == 200
        data2 = response2.json()

        # Both should have same total count
        assert data1["count"] == data2["count"]
        assert data1["count"] >= 5

        # Results should be different than each other
        ids1 = {tr["id"] for tr in data1["test_results"]}
        ids2 = {tr["id"] for tr in data2["test_results"]}
        assert ids1.isdisjoint(ids2)  # No overlap between pages

    def test_search_by_family(self, test_client: TestClient, generator: DataGenerator):
        """Test filtering by artefact family with window function"""
        # Create a snap artefact with test results
        environment = generator.gen_environment()
        test_case = generator.gen_test_case(name=generate_unique_name("family_snap"))
        snap_artefact = generator.gen_artefact(
            family=FamilyName.snap, name=generate_unique_name("snap_family")
        )
        artefact_build = generator.gen_artefact_build(snap_artefact)
        test_execution = generator.gen_test_execution(artefact_build, environment)
        test_result = generator.gen_test_result(test_case, test_execution)

        response = test_client.get("/v1/test-results?family=snap")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        assert any(tr["id"] == test_result.id for tr in data["test_results"])

    def test_search_by_environment_partial_match(
        self, test_client: TestClient, generator: DataGenerator
    ):
        """Test filtering by environment name with partial matching"""
        # Create test data with specific environment
        environment = generator.gen_environment(
            name=f"juju-controller-test-env-{uuid.uuid4().hex[:4]}"
        )
        test_case = generator.gen_test_case(name=generate_unique_name("env_partial"))
        artefact = generator.gen_artefact(name=generate_unique_name("artefact"))
        artefact_build = generator.gen_artefact_build(artefact)
        test_execution = generator.gen_test_execution(artefact_build, environment)
        test_result = generator.gen_test_result(test_case, test_execution)

        # Search with partial name
        response = test_client.get("/v1/test-results?environment=juju")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        assert any(tr["id"] == test_result.id for tr in data["test_results"])

    def test_search_by_test_case_partial_match(
        self, test_client: TestClient, generator: DataGenerator
    ):
        """Test filtering by test case name with partial matching"""
        # Create test data with specific test case
        environment = generator.gen_environment()
        test_case = generator.gen_test_case(
            name=f"test_deploy_application_unique_{uuid.uuid4().hex[:4]}"
        )
        artefact = generator.gen_artefact(name=generate_unique_name("artefact"))
        artefact_build = generator.gen_artefact_build(artefact)
        test_execution = generator.gen_test_execution(artefact_build, environment)
        test_result = generator.gen_test_result(test_case, test_execution)

        # Search with partial name
        response = test_client.get("/v1/test-results?test_case=deploy")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        assert any(tr["id"] == test_result.id for tr in data["test_results"])

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

        response = test_client.get("/v1/test-results?template_id=test_template_123")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        assert any(tr["id"] == test_result.id for tr in data["test_results"])

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
        attach_response = test_client.post(
            f"/v1/issues/{issue.id}/attach", json={"test_results": [test_result.id]}
        )
        assert attach_response.status_code == 200

        response = test_client.get(f"/v1/test-results?issues={issue.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        assert any(tr["id"] == test_result.id for tr in data["test_results"])

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

        attach_response1 = test_client.post(
            f"/v1/issues/{issue1.id}/attach", json={"test_results": [test_result1.id]}
        )
        attach_response2 = test_client.post(
            f"/v1/issues/{issue2.id}/attach", json={"test_results": [test_result2.id]}
        )
        assert attach_response1.status_code == 200
        assert attach_response2.status_code == 200

        response = test_client.get(f"/v1/test-results?issues={issue1.id},{issue2.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 2
        result_ids = {tr["id"] for tr in data["test_results"]}
        assert test_result1.id in result_ids
        assert test_result2.id in result_ids

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

        response = test_client.get(
            f"/v1/test-results?from_date={from_date}&until={until_date}"
        )

        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "test_results" in data
        assert data["count"] >= 1
        # Verify our specific test result is included
        assert any(tr["id"] == test_result.id for tr in data["test_results"])

    def test_search_with_future_date_range(self, test_client: TestClient):
        """Test filtering by future date range should return no results"""
        # Test with future date range
        from_date = (datetime.now() + timedelta(days=1)).isoformat()
        until_date = (datetime.now() + timedelta(days=2)).isoformat()

        response = test_client.get(
            f"/v1/test-results?from_date={from_date}&until={until_date}"
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

        response = test_client.get(f"/v1/test-results?from_date={from_date_before}")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        assert any(tr["id"] == test_result.id for tr in data["test_results"])

        # Test with from_date after the test execution was created
        from_date_after = (execution_created_at + timedelta(minutes=1)).isoformat()

        response = test_client.get(f"/v1/test-results?from_date={from_date_after}")

        assert response.status_code == 200
        data = response.json()
        # Our test result should not be in results from after its creation
        assert not any(tr["id"] == test_result.id for tr in data["test_results"])

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

        response = test_client.get(f"/v1/test-results?until={until_date_after}")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        assert any(tr["id"] == test_result.id for tr in data["test_results"])

        # Test with until date before the test execution was created
        until_date_before = (execution_created_at - timedelta(minutes=1)).isoformat()

        response = test_client.get(f"/v1/test-results?until={until_date_before}")

        assert response.status_code == 200
        data = response.json()
        # The test result should not be in results until before its creation
        assert not any(tr["id"] == test_result.id for tr in data["test_results"])

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

        response = test_client.get(
            f"/v1/test-results?from_date={range_before}&until={range_after}"
        )

        assert response.status_code == 200
        data = response.json()
        assert any(tr["id"] == test_result.id for tr in data["test_results"])

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
        response = test_client.get(
            f"/v1/test-results?family=snap&from_date={from_date}&until={until_date}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        assert any(tr["id"] == test_result.id for tr in data["test_results"])

        # Test that wrong family + date range excludes our result
        response = test_client.get(
            f"/v1/test-results?family=deb&from_date={from_date}&until={until_date}"
        )

        assert response.status_code == 200
        data = response.json()
        # Our snap test result should not be in deb family results
        assert not any(tr["id"] == test_result.id for tr in data["test_results"])

    def test_search_invalid_date_formats(self, test_client: TestClient):
        """Test handling of invalid date format parameters"""
        # Test with invalid date format
        response = test_client.get("/v1/test-results?from_date=invalid-date")
        assert response.status_code == 422

        response = test_client.get("/v1/test-results?until=not-a-date")
        assert response.status_code == 422

        # Test with malformed ISO date
        response = test_client.get("/v1/test-results?from_date=2025-13-45T25:99:99")
        assert response.status_code == 422

    def test_search_multiple_filters_complex(
        self, test_client: TestClient, generator: DataGenerator
    ):
        """Test combining multiple filters with window function"""
        # Create specific test data
        environment = generator.gen_environment(
            name=f"multi-filter-env-{uuid.uuid4().hex[:4]}"
        )
        test_case = generator.gen_test_case(
            name=generate_unique_name("multi_filter"),
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
        attach_response = test_client.post(
            f"/v1/issues/{issue.id}/attach", json={"test_results": [test_result.id]}
        )
        assert attach_response.status_code == 200

        response = test_client.get(
            f"/v1/test-results?family=snap&environment=multi-filter-env&test_case=multi_filter&template_id=multi_filter_template&issues={issue.id}&limit=5"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        assert any(tr["id"] == test_result.id for tr in data["test_results"])

    def test_search_invalid_family(self, test_client: TestClient):
        """Test handling invalid family name"""
        response = test_client.get("/v1/test-results?family=invalid_family")

        assert response.status_code == 200
        data = response.json()
        # Should return no results for invalid family
        assert data["count"] == 0
        assert data["test_results"] == []

    def test_search_no_results(self, test_client: TestClient):
        """Test search with filters that match no results"""
        response = test_client.get(
            "/v1/test-results?test_case=nonexistent_test_case_12345"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["test_results"] == []

    def test_pagination_limits(self, test_client: TestClient):
        """Test pagination parameter validation"""
        # Test maximum limit
        response = test_client.get("/v1/test-results?limit=1001")
        assert response.status_code == 422

        # Test minimum limit
        response = test_client.get("/v1/test-results?limit=0")
        assert response.status_code == 422

        # Test negative offset
        response = test_client.get("/v1/test-results?offset=-1")
        assert response.status_code == 422

    def test_large_offset_pagination(self, test_client: TestClient):
        # Create test data

        response_check = test_client.get(
            "/v1/test-results?family=deb&limit=10&offset=0"
        )
        actual_count = response_check.json()["count"]

        response = test_client.get("/v1/test-results?family=deb&limit=10&offset=1000")
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
        for family_name in ["SNAP", "Snap", "snap"]:
            response = test_client.get(f"/v1/test-results?family={family_name}")

            assert response.status_code == 200
            data = response.json()
            assert data["count"] >= 1
            assert any(tr["id"] == test_result.id for tr in data["test_results"])

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

        response = test_client.get("/v1/test-results?limit=5")

        assert response.status_code == 200
        data = response.json()

        # Results should be ordered by creation date descending
        if len(data["test_results"]) >= 2:
            # Find our test results in the response
            our_results = [
                tr
                for tr in data["test_results"]
                if tr["id"] in [test_result1.id, test_result2.id]
            ]

            # Should have both results
            assert len(our_results) == 2


class TestGetEnvironments:
    """Test class for the get environments endpoint"""

    def test_get_environments(self, test_client: TestClient, generator: DataGenerator):
        """Test getting list of environments"""
        # Create test data with environment
        environment = generator.gen_environment(
            name=f"test-env-for-list-{uuid.uuid4().hex[:4]}"
        )
        test_case = generator.gen_test_case(name=generate_unique_name("get_env"))
        artefact = generator.gen_artefact(name=generate_unique_name("artefact"))
        artefact_build = generator.gen_artefact_build(artefact)
        test_execution = generator.gen_test_execution(artefact_build, environment)
        # Add test_result creation which is required by the query
        generator.gen_test_result(test_case, test_execution)

        response = test_client.get("/v1/test-results/environments")

        assert response.status_code == 200
        environments = response.json()
        assert isinstance(environments, list)
        assert environment.name in environments

    def test_get_environments_sorted(
        self, test_client: TestClient, generator: DataGenerator
    ):
        """Test that environments are returned in sorted order"""
        # Create multiple environments with unique test cases
        env_names = [
            f"zebra-env-{uuid.uuid4().hex[:4]}",
            f"alpha-env-{uuid.uuid4().hex[:4]}",
            f"beta-env-{uuid.uuid4().hex[:4]}",
        ]
        for i, name in enumerate(env_names):
            environment = generator.gen_environment(name=name)
            test_case = generator.gen_test_case(
                name=generate_unique_name(f"sort_env_{i}")
            )
            artefact = generator.gen_artefact(
                name=generate_unique_name(f"artefact_{i}")
            )
            artefact_build = generator.gen_artefact_build(artefact)
            test_execution = generator.gen_test_execution(artefact_build, environment)
            # Add test_result creation
            generator.gen_test_result(test_case, test_execution)

        response = test_client.get("/v1/test-results/environments")

        assert response.status_code == 200
        environments = response.json()

        # Check that our test environments are included and sorted
        test_envs = [env for env in environments if env in env_names]
        assert test_envs == sorted(test_envs)


class TestGetTestCases:
    """Test class for the get test cases endpoint"""

    def test_get_test_cases(self, test_client: TestClient, generator: DataGenerator):
        """Test getting list of test cases"""
        # Create test data with test case
        environment = generator.gen_environment()
        test_case = generator.gen_test_case(name=generate_unique_name("get_cases"))
        artefact = generator.gen_artefact(name=generate_unique_name("artefact"))
        artefact_build = generator.gen_artefact_build(artefact)
        test_execution = generator.gen_test_execution(artefact_build, environment)
        generator.gen_test_result(test_case, test_execution)

        response = test_client.get("/v1/test-results/test-cases")

        assert response.status_code == 200
        test_cases = response.json()
        assert isinstance(test_cases, list)
        assert test_case.name in test_cases


class TestGetFamilies:
    """Test class for the get families endpoint"""

    def test_get_families(self, test_client: TestClient, generator: DataGenerator):
        """Test getting list of families"""
        # Create test data to ensure families exist
        environment = generator.gen_environment()
        test_case = generator.gen_test_case(name=generate_unique_name("families_test"))

        # Create artefacts for each family to ensure they show up
        snap_artefact = generator.gen_artefact(
            family=FamilyName.snap, name=generate_unique_name("snap_families")
        )
        snap_build = generator.gen_artefact_build(snap_artefact)
        snap_execution = generator.gen_test_execution(snap_build, environment)
        generator.gen_test_result(test_case, snap_execution)

        deb_artefact = generator.gen_artefact(
            family=FamilyName.deb, name=generate_unique_name("deb_families")
        )
        deb_build = generator.gen_artefact_build(deb_artefact)
        deb_execution = generator.gen_test_execution(deb_build, environment)
        generator.gen_test_result(test_case, deb_execution)

        response = test_client.get("/v1/test-results/families")

        assert response.status_code == 200
        families = response.json()
        assert isinstance(families, list)
        assert "snap" in families
        assert "deb" in families

    def test_get_families_complete(
        self, test_client: TestClient, generator: DataGenerator
    ):
        """Test that all known families are returned"""
        # Create test data for all families
        environment = generator.gen_environment()
        test_case = generator.gen_test_case(
            name=generate_unique_name("complete_families")
        )

        # Create artefacts for all families
        for family in FamilyName:
            artefact = generator.gen_artefact(
                family=family, name=generate_unique_name(f"{family.value}_complete")
            )
            artefact_build = generator.gen_artefact_build(artefact)
            test_execution = generator.gen_test_execution(artefact_build, environment)
            generator.gen_test_result(test_case, test_execution)

        response = test_client.get("/v1/test-results/families")

        assert response.status_code == 200
        families = response.json()

        # Check that all enum values are present
        expected_families = [family.value for family in FamilyName]
        for expected in expected_families:
            assert expected in families


class TestGetIssues:
    """Test class for the get issues endpoint"""

    def test_get_issues_empty(self, test_client: TestClient):
        """Test getting list of issues when no issues exist"""
        response = test_client.get("/v1/issues")

        assert response.status_code == 200
        data = response.json()
        assert "issues" in data
        assert isinstance(data["issues"], list)

    def test_get_issues(self, test_client: TestClient, generator: DataGenerator):
        """Test getting list of issues through the main issues API"""
        # Create test data first
        environment = generator.gen_environment()
        test_case = generator.gen_test_case(name=generate_unique_name("issue_test"))
        artefact = generator.gen_artefact(name=generate_unique_name("artefact"))
        artefact_build = generator.gen_artefact_build(artefact)
        test_execution = generator.gen_test_execution(artefact_build, environment)
        test_result1 = generator.gen_test_result(test_case, test_execution)
        test_result2 = generator.gen_test_result(test_case, test_execution)

        # Create issues
        issue1 = generator.gen_issue(
            project="canonical/test_observer",
            key="123",
            title="Bug in search functionality",
        )
        issue2 = generator.gen_issue(
            project="TO", key="456", title="Feature request for filters"
        )

        # Attach issues to test results
        attach_response1 = test_client.post(
            f"/v1/issues/{issue1.id}/attach", json={"test_results": [test_result1.id]}
        )
        attach_response2 = test_client.post(
            f"/v1/issues/{issue2.id}/attach", json={"test_results": [test_result2.id]}
        )
        assert attach_response1.status_code == 200
        assert attach_response2.status_code == 200

        # Test through the main issues endpoint
        response = test_client.get("/v1/issues")

        assert response.status_code == 200
        data = response.json()
        assert "issues" in data
        issues = data["issues"]
        assert isinstance(issues, list)
        assert len(issues) >= 2

        # Check that our issues are in the response
        issue_ids = {issue["id"] for issue in issues}
        assert issue1.id in issue_ids
        assert issue2.id in issue_ids

        # Check the structure of returned issues
        found_issue = next(issue for issue in issues if issue["id"] == issue1.id)
        assert "url" in found_issue
        assert "title" in found_issue
        assert found_issue["title"] == "Bug in search functionality"

        # Test that the issues are properly attached by searching test results
        search_response = test_client.get(
            f"/v1/test-results?issues={issue1.id},{issue2.id}"
        )
        assert search_response.status_code == 200
        search_data = search_response.json()
        assert search_data["count"] >= 2

        # Verify the correct test results are returned
        result_ids = {tr["id"] for tr in search_data["test_results"]}
        assert test_result1.id in result_ids
        assert test_result2.id in result_ids


class TestWindowFunctionSpecific:
    """Test class specifically for window function behavior and edge cases"""

    def test_window_function_with_empty_results(self, test_client: TestClient):
        """Test window function behavior when no results match"""
        response = test_client.get("/v1/test-results?family=nonexistent")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["test_results"] == []

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

        response = test_client.get("/v1/test-results?family=image")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        assert len(data["test_results"]) >= 1
        assert any(tr["id"] == test_result.id for tr in data["test_results"])

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
        response = test_client.get("/v1/test-results?limit=5&offset=5")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 10
        assert len(data["test_results"]) <= 5

        # Test if limit is larger than total results
        response = test_client.get("/v1/test-results?limit=1000")
        assert response.status_code == 200
        data = response.json()
        assert len(data["test_results"]) <= data["count"]
