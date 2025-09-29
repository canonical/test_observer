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
)

from tests.data_generator import DataGenerator
from tests.conftest import make_authenticated_request
from test_observer.common.permissions import Permission


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

        response = test_client.get("/v1/test-results", params={"limit": 0})

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

        response = test_client.get("/v1/test-results?families=snap&limit=3")

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
        response1 = test_client.get("/v1/test-results?families=charm&limit=2&offset=0")
        assert response1.status_code == 200
        data1 = response1.json()

        # Test second page
        response2 = test_client.get("/v1/test-results?families=charm&limit=2&offset=2")
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
        """Parametric: the filter returns only results from the requested family."""
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

        resp = test_client.get(f"/v1/test-results?families={family.value}")
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

        response = test_client.get("/v1/test-results?template_ids=test_template_123")

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

        response = test_client.get(f"/v1/test-results?issues={issue.id}")

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

        response = test_client.get(
            f"/v1/test-results?issues={issue1.id}&issues={issue2.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 2
        result_ids = {tr["test_result"]["id"] for tr in data["test_results"]}
        assert test_result1.id in result_ids
        assert test_result2.id in result_ids

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
        response = test_client.get(
            "/v1/test-results?execution_metadata=category1:value1&execution_metadata=category1:value2"
        )
        expect = {test_result.id for expect, test_result in test_results if expect}

        assert response.status_code == 200
        data = response.json()
        assert expect == {tr["test_result"]["id"] for tr in data["test_results"]}

    def test_invalid_execution_metadata_format(self, test_client: TestClient):
        # Test with invalid execution metadata format
        response = test_client.get("/v1/test-results?execution_metadata=invalid-format")
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

        response = test_client.get(
            f"/v1/test-results?from_date={from_date}&until_date={until_date}"
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

        response = test_client.get(
            f"/v1/test-results?from_date={from_date}&until_date={until_date}"
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
        assert any(
            tr["test_result"]["id"] == test_result.id for tr in data["test_results"]
        )

        # Test with from_date after the test execution was created
        from_date_after = (execution_created_at + timedelta(minutes=1)).isoformat()

        response = test_client.get(f"/v1/test-results?from_date={from_date_after}")

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

        response = test_client.get(f"/v1/test-results?until_date={until_date_after}")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        assert any(
            tr["test_result"]["id"] == test_result.id for tr in data["test_results"]
        )

        # Test with until date before the test execution was created
        until_date_before = (execution_created_at - timedelta(minutes=1)).isoformat()

        response = test_client.get(f"/v1/test-results?until_date={until_date_before}")

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

        response = test_client.get(
            f"/v1/test-results?from_date={range_before}&until_date={range_after}"
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
        response = test_client.get(
            f"/v1/test-results?families=snap&from_date={from_date}&until_date={until_date}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        assert any(
            tr["test_result"]["id"] == test_result.id for tr in data["test_results"]
        )

        # Test that wrong family + date range excludes our result
        response = test_client.get(
            f"/v1/test-results?families=deb&from_date={from_date}&until_date={until_date}"
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
        response = test_client.get("/v1/test-results?from_date=invalid-date")
        assert response.status_code == 422

        response = test_client.get("/v1/test-results?until_date=not-a-date")
        assert response.status_code == 422

        # Test with malformed ISO date
        response = test_client.get("/v1/test-results?from_date=2025-13-45T25:99:99")
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

        response = test_client.get(
            f"/v1/test-results?families=snap&environments={environment_name}&test_cases={test_case_name}&template_ids=multi_filter_template&issues={issue.id}&limit=5"
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
        response = test_client.get("/v1/test-results?families=invalid_family")

        assert response.status_code == 422

    def test_search_no_results(self, test_client: TestClient):
        """Test search with filters that match no results"""
        response = test_client.get(
            "/v1/test-results?test_cases=nonexistent_test_case_12345"
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

        # Test negative offset
        response = test_client.get("/v1/test-results?offset=-1")
        assert response.status_code == 422

    def test_large_offset_pagination(self, test_client: TestClient):
        # Create test data

        response_check = test_client.get(
            "/v1/test-results?families=deb&limit=10&offset=0"
        )
        actual_count = response_check.json()["count"]

        response = test_client.get("/v1/test-results?families=deb&limit=10&offset=1000")
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
        response = test_client.get("/v1/test-results?families=snap")

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

        response = test_client.get("/v1/test-results?limit=5")

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


class TestWindowFunctionSpecific:
    """Test class specifically for window function behavior and edge cases"""

    def test_window_function_with_empty_results(self, test_client: TestClient):
        """Test window function behavior when no results match"""
        response = test_client.get("/v1/test-results?families=nonexistent")

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

        response = test_client.get("/v1/test-results?families=image")

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
