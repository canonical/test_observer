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

from tests.data_generator import DataGenerator
from test_observer.data_access.models import FamilyName

attach_endpoint = "/v1/issues/{id}/attach"
detach_endpoint = "/v1/issues/{id}/detach"


def gen_test_results(generator: DataGenerator):
    environment = generator.gen_environment()
    test_case = generator.gen_test_case()
    artefact = generator.gen_artefact()
    artefact_build = generator.gen_artefact_build(artefact)
    test_execution = generator.gen_test_execution(artefact_build, environment)
    test_result_1 = generator.gen_test_result(test_case, test_execution)
    test_result_2 = generator.gen_test_result(test_case, test_execution)
    return test_result_1, test_result_2


def test_issue_attach_empty(test_client: TestClient, generator: DataGenerator):
    issue = generator.gen_issue()
    test_client.post(
        attach_endpoint.format(id=issue.id),
        json={"test_results": []},
    )
    assert issue.test_result_attachments == []


def test_issue_attach_one(test_client: TestClient, generator: DataGenerator):
    test_result = gen_test_results(generator)[0]
    issue = generator.gen_issue()
    test_client.post(
        attach_endpoint.format(id=issue.id), json={"test_results": [test_result.id]}
    )
    assert {
        attachment.test_result.id for attachment in issue.test_result_attachments
    } == {test_result.id}


def test_issue_attach_repeat(test_client: TestClient, generator: DataGenerator):
    test_result = gen_test_results(generator)[0]
    issue = generator.gen_issue()
    test_client.post(
        attach_endpoint.format(id=issue.id), json={"test_results": [test_result.id]}
    )
    test_client.post(
        attach_endpoint.format(id=issue.id), json={"test_results": [test_result.id]}
    )
    assert {
        attachment.test_result.id for attachment in issue.test_result_attachments
    } == {test_result.id}


def test_issue_attach_multiple(test_client: TestClient, generator: DataGenerator):
    test_results = gen_test_results(generator)
    issue = generator.gen_issue()
    test_client.post(
        attach_endpoint.format(id=issue.id), json={"test_results": [test_results[0].id]}
    )
    test_client.post(
        attach_endpoint.format(id=issue.id), json={"test_results": [test_results[1].id]}
    )
    assert {
        attachment.test_result.id for attachment in issue.test_result_attachments
    } == {test_results[0].id, test_results[1].id}


def test_issue_detach_one(test_client: TestClient, generator: DataGenerator):
    test_result = gen_test_results(generator)[0]
    issue = generator.gen_issue()
    test_client.post(
        attach_endpoint.format(id=issue.id), json={"test_results": [test_result.id]}
    )
    test_client.post(
        detach_endpoint.format(id=issue.id), json={"test_results": [test_result.id]}
    )
    assert issue.test_result_attachments == []


def test_issue_detach_repeat(test_client: TestClient, generator: DataGenerator):
    test_result = gen_test_results(generator)[0]
    issue = generator.gen_issue()
    test_client.post(
        attach_endpoint.format(id=issue.id), json={"test_results": [test_result.id]}
    )
    test_client.post(
        detach_endpoint.format(id=issue.id), json={"test_results": [test_result.id]}
    )
    test_client.post(
        detach_endpoint.format(id=issue.id), json={"test_results": [test_result.id]}
    )
    assert issue.test_result_attachments == []


def test_issue_detach_some(test_client: TestClient, generator: DataGenerator):
    test_results = gen_test_results(generator)
    issue = generator.gen_issue()
    test_client.post(
        attach_endpoint.format(id=issue.id),
        json={"test_results": [test_results[0].id, test_results[1].id]},
    )
    test_client.post(
        detach_endpoint.format(id=issue.id), json={"test_results": [test_results[0].id]}
    )
    assert {
        attachment.test_result.id for attachment in issue.test_result_attachments
    } == {test_results[1].id}


def test_issue_attach_with_filters_family(
    test_client: TestClient, generator: DataGenerator
):
    # Create two artefacts with different families
    artefact_snap = generator.gen_artefact(family=FamilyName.snap, name="snap1")
    artefact_charm = generator.gen_artefact(family=FamilyName.charm, name="charm1")
    build_snap = generator.gen_artefact_build(artefact_snap)
    build_charm = generator.gen_artefact_build(artefact_charm)
    env = generator.gen_environment()
    te_snap = generator.gen_test_execution(build_snap, env)
    te_charm = generator.gen_test_execution(build_charm, env)
    tc = generator.gen_test_case()
    tr_snap = generator.gen_test_result(tc, te_snap)
    tr_charm = generator.gen_test_result(tc, te_charm)
    issue = generator.gen_issue()

    # Attach only snap test results using filters
    resp = test_client.post(
        attach_endpoint.format(id=issue.id),
        json={"test_results_filters": {"families": ["snap"]}},
    )
    assert resp.status_code == 200
    attached_ids = {a.test_result.id for a in issue.test_result_attachments}
    assert tr_snap.id in attached_ids
    assert tr_charm.id not in attached_ids


def test_issue_detach_with_filters_environment(
    test_client: TestClient, generator: DataGenerator
):
    # Create two environments
    env1 = generator.gen_environment(name="laptop")
    env2 = generator.gen_environment(name="server")
    artefact = generator.gen_artefact()
    build = generator.gen_artefact_build(artefact)
    tc = generator.gen_test_case()
    te1 = generator.gen_test_execution(build, env1)
    te2 = generator.gen_test_execution(build, env2)
    tr1 = generator.gen_test_result(tc, te1)
    tr2 = generator.gen_test_result(tc, te2)
    issue = generator.gen_issue()
    # Attach both
    test_client.post(
        attach_endpoint.format(id=issue.id),
        json={"test_results": [tr1.id, tr2.id]},
    )
    # Detach only env1 using filters
    resp = test_client.post(
        detach_endpoint.format(id=issue.id),
        json={"test_results_filters": {"environments": ["laptop"]}},
    )
    assert resp.status_code == 200
    remaining_ids = {a.test_result.id for a in issue.test_result_attachments}
    assert tr1.id not in remaining_ids
    assert tr2.id in remaining_ids


def test_issue_attach_with_filters_execution_metadata(
    test_client: TestClient, generator: DataGenerator
):
    artefact = generator.gen_artefact()
    build = generator.gen_artefact_build(artefact)
    env = generator.gen_environment()
    tc = generator.gen_test_case()
    te1 = generator.gen_test_execution(
        build, env, execution_metadata={"hw": ["laptop"]}
    )
    te2 = generator.gen_test_execution(
        build, env, execution_metadata={"hw": ["server"]}
    )
    tr1 = generator.gen_test_result(tc, te1)
    tr2 = generator.gen_test_result(tc, te2)
    issue = generator.gen_issue()
    # Attach only test results with hw:laptop
    resp = test_client.post(
        attach_endpoint.format(id=issue.id),
        json={"test_results_filters": {"execution_metadata": [["hw", "laptop"]]}},
    )
    assert resp.status_code == 200
    attached_ids = {a.test_result.id for a in issue.test_result_attachments}
    assert tr1.id in attached_ids
    assert tr2.id not in attached_ids


def test_issue_attach_with_filters_template_id_unique_names(
    test_client: TestClient, generator: DataGenerator
):
    artefact = generator.gen_artefact()
    build = generator.gen_artefact_build(artefact)
    env = generator.gen_environment()
    tc1 = generator.gen_test_case(name="camera/detect-1", template_id="tmpl-1")
    tc2 = generator.gen_test_case(name="camera/detect-2", template_id="tmpl-2")
    te = generator.gen_test_execution(build, env)
    tr1 = generator.gen_test_result(tc1, te)
    tr2 = generator.gen_test_result(tc2, te)
    issue = generator.gen_issue()
    # Attach only test results with template_id tmpl-1
    resp = test_client.post(
        attach_endpoint.format(id=issue.id),
        json={"test_results_filters": {"template_ids": ["tmpl-1"]}},
    )
    assert resp.status_code == 200
    attached_ids = {a.test_result.id for a in issue.test_result_attachments}
    assert tr1.id in attached_ids
    assert tr2.id not in attached_ids


def test_issue_detach_with_filters_template_id_unique_names(
    test_client: TestClient, generator: DataGenerator
):
    artefact = generator.gen_artefact()
    build = generator.gen_artefact_build(artefact)
    env = generator.gen_environment()
    tc1 = generator.gen_test_case(name="camera/detect-3", template_id="tmpl-1")
    tc2 = generator.gen_test_case(name="camera/detect-4", template_id="tmpl-2")
    te = generator.gen_test_execution(build, env)
    tr1 = generator.gen_test_result(tc1, te)
    tr2 = generator.gen_test_result(tc2, te)
    issue = generator.gen_issue()
    # Attach both
    test_client.post(
        attach_endpoint.format(id=issue.id),
        json={"test_results": [tr1.id, tr2.id]},
    )
    # Detach only tmpl-1
    resp = test_client.post(
        detach_endpoint.format(id=issue.id),
        json={"test_results_filters": {"template_ids": ["tmpl-1"]}},
    )
    assert resp.status_code == 200
    remaining_ids = {a.test_result.id for a in issue.test_result_attachments}
    assert tr1.id not in remaining_ids
    assert tr2.id in remaining_ids


def test_issue_attach_with_filters_template_id_repeat(
    test_client: TestClient, generator: DataGenerator
):
    artefact = generator.gen_artefact()
    build = generator.gen_artefact_build(artefact)
    env = generator.gen_environment()
    tc1 = generator.gen_test_case(name="camera/detect-5", template_id="tmpl-1")
    te = generator.gen_test_execution(build, env)
    tr1 = generator.gen_test_result(tc1, te)
    issue = generator.gen_issue()
    # Attach with filter multiple times
    for _ in range(3):
        resp = test_client.post(
            attach_endpoint.format(id=issue.id),
            json={"test_results_filters": {"template_ids": ["tmpl-1"]}},
        )
        assert resp.status_code == 200
    attached_ids = {a.test_result.id for a in issue.test_result_attachments}
    assert tr1.id in attached_ids
    # Should not duplicate
    assert len(attached_ids) == 1
