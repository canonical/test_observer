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


from fastapi.testclient import TestClient

from tests.asserts import assert_fails_validation
from tests.conftest import make_authenticated_request
from tests.data_generator import DataGenerator
from test_observer.common.permissions import Permission
from test_observer.data_access.models_enums import IssueSource, IssueStatus

endpoint = "/v1/issues"
valid_put_data = {
    "url": "https://github.com/canonical/test_observer/issues/71",
    "title": "some title",
    "status": "open",
}


def test_empty_get_all(test_client: TestClient):
    response = make_authenticated_request(
        lambda: test_client.get(endpoint),
        Permission.view_issue,
    )
    assert response.status_code == 200
    assert response.json() == {"issues": []}


def test_get_all(test_client: TestClient, generator: DataGenerator):
    issue = generator.gen_issue()

    response = make_authenticated_request(
        lambda: test_client.get(endpoint),
        Permission.view_issue,
    )

    assert response.status_code == 200
    assert response.json() == {
        "issues": [
            {
                "id": issue.id,
                "source": issue.source,
                "project": issue.project,
                "key": issue.key,
                "title": issue.title,
                "status": issue.status,
                "url": issue.url,
            }
        ],
    }


def test_get_issue(test_client: TestClient, generator: DataGenerator):
    issue = generator.gen_issue()

    response = make_authenticated_request(
        lambda: test_client.get(endpoint + f"/{issue.id}"),
        Permission.view_issue,
    )

    assert response.status_code == 200
    assert set(response.json().keys()) == {
        "attachment_rules",
        "url",
        "key",
        "id",
        "project",
        "source",
        "title",
        "status",
    }
    assert response.json()["id"] == issue.id
    assert response.json()["source"] == issue.source
    assert response.json()["project"] == issue.project
    assert response.json()["key"] == issue.key
    assert response.json()["title"] == issue.title
    assert response.json()["status"] == issue.status
    assert response.json()["url"] == issue.url


def test_patch_invalid_status(test_client: TestClient):
    put_response = make_authenticated_request(
        lambda: test_client.put(endpoint, json=valid_put_data),
        Permission.change_issue,
    )
    response = make_authenticated_request(
        lambda: test_client.patch(
            endpoint + f"/{put_response.json()['id']}",
            json={"status": "unknown-status"},
        ),
        Permission.change_issue,
    )
    assert response.status_code == 422


def test_patch_no_change(test_client: TestClient):
    put_response = make_authenticated_request(
        lambda: test_client.put(endpoint, json=valid_put_data),
        Permission.change_issue,
    )
    response = make_authenticated_request(
        lambda: test_client.patch(endpoint + f"/{put_response.json()['id']}", json={}),
        Permission.change_issue,
    )
    assert put_response.json() == response.json()


def test_patch_all(test_client: TestClient):
    put_response = make_authenticated_request(
        lambda: test_client.put(endpoint, json=valid_put_data),
        Permission.change_issue,
    )
    response = make_authenticated_request(
        lambda: test_client.patch(
            endpoint + f"/{put_response.json()['id']}",
            json={"title": "new title", "status": "closed"},
        ),
        Permission.change_issue,
    )
    assert response.json()["title"] == "new title"
    assert response.json()["status"] == "closed"


def test_put_requires_url(test_client: TestClient):
    response = make_authenticated_request(
        lambda: test_client.put(endpoint, json={}),
        Permission.change_issue,
    )
    assert_fails_validation(response, "url", "missing")


def test_put_indempotent(test_client: TestClient):
    make_authenticated_request(
        lambda: test_client.put(endpoint, json=valid_put_data),
        Permission.change_issue,
    )
    make_authenticated_request(
        lambda: test_client.put(endpoint, json=valid_put_data),
        Permission.change_issue,
    )
    response = make_authenticated_request(
        lambda: test_client.get(endpoint),
        Permission.view_issue,
    )
    assert len(response.json()["issues"]) == 1


def test_put_update_existing(test_client: TestClient):
    make_authenticated_request(
        lambda: test_client.put(endpoint, json=valid_put_data),
        Permission.change_issue,
    )
    make_authenticated_request(
        lambda: test_client.put(
            endpoint, json={**valid_put_data, "title": "new title"}
        ),
        Permission.change_issue,
    )
    response = make_authenticated_request(
        lambda: test_client.get(endpoint),
        Permission.view_issue,
    )
    assert response.json()["issues"][0]["title"] == "new title"


def test_put_invalid_url(test_client: TestClient):
    put_data = {**valid_put_data, "url": "http://unknown.com/bug/1"}
    response = make_authenticated_request(
        lambda: test_client.put(endpoint, json=put_data),
        Permission.change_issue,
    )
    assert response.status_code == 422


def test_put_invalid_status(test_client: TestClient):
    put_data = {**valid_put_data, "status": "random"}
    response = make_authenticated_request(
        lambda: test_client.put(endpoint, json=put_data),
        Permission.change_issue,
    )
    assert response.status_code == 422


def test_put_defaults(test_client: TestClient):
    put_data = {"url": valid_put_data["url"]}
    response = make_authenticated_request(
        lambda: test_client.put(endpoint, json=put_data),
        Permission.change_issue,
    )
    assert response.json()["title"] == ""
    assert response.json()["status"] == "unknown"


def test_get_all_filter_by_source(test_client: TestClient, generator: DataGenerator):
    github_issue = generator.gen_issue(source=IssueSource.GITHUB)
    generator.gen_issue(source=IssueSource.JIRA)

    response = make_authenticated_request(
        lambda: test_client.get(endpoint, params={"source": "github"}),
        Permission.view_issue,
    )

    assert response.status_code == 200
    issues = response.json()["issues"]
    assert len(issues) == 1
    assert issues[0]["id"] == github_issue.id
    assert issues[0]["source"] == "github"


def test_get_all_filter_by_project(test_client: TestClient, generator: DataGenerator):
    project_a_issue = generator.gen_issue(project="ProjectA")
    generator.gen_issue(project="ProjectB")

    response = make_authenticated_request(
        lambda: test_client.get(endpoint, params={"project": "ProjectA"}),
        Permission.view_issue,
    )

    assert response.status_code == 200
    issues = response.json()["issues"]
    assert len(issues) == 1
    assert issues[0]["id"] == project_a_issue.id
    assert issues[0]["project"] == "ProjectA"


def test_get_all_filter_by_source_and_project(
    test_client: TestClient, generator: DataGenerator
):
    target_issue = generator.gen_issue(source=IssueSource.GITHUB, project="ProjectA")
    generator.gen_issue(source=IssueSource.GITHUB, project="ProjectB")
    generator.gen_issue(source=IssueSource.JIRA, project="ProjectA")

    response = make_authenticated_request(
        lambda: test_client.get(
            endpoint, params={"source": "github", "project": "ProjectA"}
        ),
        Permission.view_issue,
    )

    assert response.status_code == 200
    issues = response.json()["issues"]
    assert len(issues) == 1
    assert issues[0]["id"] == target_issue.id


def test_get_all_with_limit(test_client: TestClient, generator: DataGenerator):
    for i in range(5):
        generator.gen_issue(key=f"ISSUE-{i}")

    response = make_authenticated_request(
        lambda: test_client.get(endpoint, params={"limit": 3}),
        Permission.view_issue,
    )

    assert response.status_code == 200
    assert len(response.json()["issues"]) == 3


def test_get_all_with_offset(test_client: TestClient, generator: DataGenerator):
    [generator.gen_issue(key=f"ISSUE-{i}") for i in range(5)]

    response = make_authenticated_request(
        lambda: test_client.get(endpoint, params={"offset": 2}),
        Permission.view_issue,
    )

    assert response.status_code == 200
    assert len(response.json()["issues"]) == 3


def test_get_all_with_limit_and_offset(
    test_client: TestClient, generator: DataGenerator
):
    for i in range(10):
        generator.gen_issue(key=f"ISSUE-{i}")

    response = make_authenticated_request(
        lambda: test_client.get(endpoint, params={"limit": 3, "offset": 5}),
        Permission.view_issue,
    )

    assert response.status_code == 200
    assert len(response.json()["issues"]) == 3


def test_get_all_search_by_key(test_client: TestClient, generator: DataGenerator):
    target_issue = generator.gen_issue(key="KERNEL-123")
    generator.gen_issue(key="LP-456")

    response = make_authenticated_request(
        lambda: test_client.get(endpoint, params={"q": "KERNEL-123"}),
        Permission.view_issue,
    )

    assert response.status_code == 200
    issues = response.json()["issues"]
    assert len(issues) == 1
    assert issues[0]["id"] == target_issue.id


def test_get_all_search_by_title(test_client: TestClient, generator: DataGenerator):
    target_issue = generator.gen_issue(key="MEM-1", title="Memory leak in kernel")
    generator.gen_issue(key="UI-1", title="UI rendering bug")

    response = make_authenticated_request(
        lambda: test_client.get(endpoint, params={"q": "memory leak"}),
        Permission.view_issue,
    )

    assert response.status_code == 200
    issues = response.json()["issues"]
    assert len(issues) == 1
    assert issues[0]["id"] == target_issue.id


def test_get_all_search_case_insensitive(
    test_client: TestClient, generator: DataGenerator
):
    target_issue = generator.gen_issue(title="Bug in System Startup")

    response = make_authenticated_request(
        lambda: test_client.get(endpoint, params={"q": "bug system"}),
        Permission.view_issue,
    )

    assert response.status_code == 200
    issues = response.json()["issues"]
    assert len(issues) == 1
    assert issues[0]["id"] == target_issue.id


def test_get_all_search_multiple_segments(
    test_client: TestClient, generator: DataGenerator
):
    target_issue = generator.gen_issue(
        key="KERN-1", source=IssueSource.JIRA, project="KERNEL", title="Memory leak"
    )
    generator.gen_issue(
        key="KERN-2", source=IssueSource.JIRA, project="KERNEL", title="Other bug"
    )
    generator.gen_issue(
        key="TEST-1", source=IssueSource.GITHUB, project="TEST", title="Memory leak"
    )

    response = make_authenticated_request(
        lambda: test_client.get(endpoint, params={"q": "jira kernel memory"}),
        Permission.view_issue,
    )

    assert response.status_code == 200
    issues = response.json()["issues"]
    assert len(issues) == 1
    assert issues[0]["id"] == target_issue.id


def test_get_all_search_by_id(test_client: TestClient, generator: DataGenerator):
    target_issue = generator.gen_issue()

    response = make_authenticated_request(
        lambda: test_client.get(endpoint, params={"q": str(target_issue.id)}),
        Permission.view_issue,
    )

    assert response.status_code == 200
    issues = response.json()["issues"]
    assert len(issues) == 1
    assert issues[0]["id"] == target_issue.id


def test_get_all_search_by_status(test_client: TestClient, generator: DataGenerator):
    open_issue = generator.gen_issue(key="OPEN-1", status=IssueStatus.OPEN)
    generator.gen_issue(key="CLOSED-1", status=IssueStatus.CLOSED)

    response = make_authenticated_request(
        lambda: test_client.get(endpoint, params={"q": "open"}),
        Permission.view_issue,
    )

    assert response.status_code == 200
    issues = response.json()["issues"]
    assert len(issues) == 1
    assert issues[0]["id"] == open_issue.id


def test_get_all_search_no_results(test_client: TestClient, generator: DataGenerator):
    generator.gen_issue(title="Some bug")

    response = make_authenticated_request(
        lambda: test_client.get(endpoint, params={"q": "nonexistent"}),
        Permission.view_issue,
    )

    assert response.status_code == 200
    assert response.json()["issues"] == []


def test_get_all_ordering(test_client: TestClient, generator: DataGenerator):
    # Create issues in mixed order
    # IssueSource enum order is: JIRA, GITHUB, LAUNCHPAD
    issue3 = generator.gen_issue(source=IssueSource.LAUNCHPAD, project="B", key="LP-3")
    issue1 = generator.gen_issue(source=IssueSource.GITHUB, project="A", key="GH-1")
    issue4 = generator.gen_issue(source=IssueSource.LAUNCHPAD, project="B", key="LP-1")
    issue2 = generator.gen_issue(source=IssueSource.JIRA, project="C", key="JIRA-1")

    response = make_authenticated_request(
        lambda: test_client.get(endpoint),
        Permission.view_issue,
    )

    assert response.status_code == 200
    issues = response.json()["issues"]
    # Should be ordered by source (enum order), then project, then key
    # Filter to only the 4 issues we created (in case there are others from other tests)
    created_ids = {issue1.id, issue2.id, issue3.id, issue4.id}
    our_issues = [i for i in issues if i["id"] in created_ids]

    assert len(our_issues) == 4
    # Verify the relative ordering of our issues
    # Expected: jira C JIRA-1, then github A GH-1, then launchpad B LP-1, LP-3
    id_to_index = {i["id"]: idx for idx, i in enumerate(our_issues)}
    assert id_to_index[issue2.id] < id_to_index[issue1.id]  # jira < github (enum order)
    assert id_to_index[issue1.id] < id_to_index[issue4.id]  # github < launchpad
    assert (
        id_to_index[issue4.id] < id_to_index[issue3.id]
    )  # LP-1 < LP-3 (same source/project)


def test_get_all_combined_filters(test_client: TestClient, generator: DataGenerator):
    target_issue = generator.gen_issue(
        key="KERN-MEM-1",
        source=IssueSource.JIRA,
        project="KERNEL",
        title="Memory leak in startup",
    )
    generator.gen_issue(
        key="KERN-OTHER-1", source=IssueSource.JIRA, project="KERNEL", title="Other bug"
    )
    generator.gen_issue(
        key="UI-MEM-1", source=IssueSource.JIRA, project="UI", title="Memory leak"
    )
    generator.gen_issue(
        key="GH-MEM-1", source=IssueSource.GITHUB, project="KERNEL", title="Memory leak"
    )

    response = make_authenticated_request(
        lambda: test_client.get(
            endpoint,
            params={"source": "jira", "project": "KERNEL", "q": "memory", "limit": 10},
        ),
        Permission.view_issue,
    )

    assert response.status_code == 200
    issues = response.json()["issues"]
    assert len(issues) == 1
    assert issues[0]["id"] == target_issue.id
