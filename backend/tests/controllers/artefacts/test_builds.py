from fastapi.testclient import TestClient

from tests.data_generator import DataGenerator


def test_get_artefact_builds(test_client: TestClient, generator: DataGenerator):
    a = generator.gen_artefact("beta")
    ab = generator.gen_artefact_build(a)
    e = generator.gen_environment()
    te = generator.gen_test_execution(ab, e)

    response = test_client.get(f"/v1/artefacts/{a.id}/builds")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": ab.id,
            "revision": ab.revision,
            "architecture": ab.architecture,
            "test_executions": [
                {
                    "id": te.id,
                    "ci_link": te.ci_link,
                    "c3_link": te.c3_link,
                    "status": te.status.value,
                    "environment": {
                        "id": e.id,
                        "name": e.name,
                        "architecture": e.architecture,
                    },
                }
            ],
        }
    ]


def test_get_artefact_builds_sorts_test_executions_by_environment_name(
    test_client: TestClient, generator: DataGenerator
):
    a = generator.gen_artefact("beta")
    ab = generator.gen_artefact_build(a)
    e2 = generator.gen_environment("e2")
    e1 = generator.gen_environment("e1")
    te2 = generator.gen_test_execution(ab, e2)
    te1 = generator.gen_test_execution(ab, e1)

    assert test_client.get(f"/v1/artefacts/{a.id}/builds").json() == [
        {
            "id": ab.id,
            "revision": ab.revision,
            "architecture": ab.architecture,
            "test_executions": [
                {
                    "id": te1.id,
                    "ci_link": te1.ci_link,
                    "c3_link": te1.c3_link,
                    "status": te1.status.value,
                    "environment": {
                        "id": e1.id,
                        "name": e1.name,
                        "architecture": e1.architecture,
                    },
                },
                {
                    "id": te2.id,
                    "ci_link": te2.ci_link,
                    "c3_link": te2.c3_link,
                    "status": te2.status.value,
                    "environment": {
                        "id": e2.id,
                        "name": e2.name,
                        "architecture": e2.architecture,
                    },
                },
            ],
        }
    ]


def test_get_artefact_builds_only_latest(
    test_client: TestClient, generator: DataGenerator
):
    artefact = generator.gen_artefact("beta")
    generator.gen_artefact_build(artefact=artefact, revision=1)
    artefact_build2 = generator.gen_artefact_build(artefact=artefact, revision=2)

    response = test_client.get(f"/v1/artefacts/{artefact.id}/builds")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": artefact_build2.id,
            "revision": artefact_build2.revision,
            "architecture": artefact_build2.architecture,
            "test_executions": [],
        }
    ]
