# Copyright 2026 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

import pytest
import requests
from fastapi.testclient import TestClient
from httpx import Response
from requests_mock import Mocker

from test_observer.common import config
from test_observer.common.enums import Permission
from test_observer.data_access.models_enums import FamilyName, StageName
from tests.conftest import make_authenticated_request
from tests.data_generator import DataGenerator

C3_BASE_URL = "https://c3.test"
POOLS_URL = f"{C3_BASE_URL}/api/v2/testing-pools/"


def _env(name: str, arch: str = "amd64", *, queue: str | None = None, metadata: dict | None = None) -> dict:
    return {"name": name, "queue": queue or name, "arch": arch, "metadata": metadata or {}}


def _snap_metadata(snap: str = "core", track: str = "latest", channel: str = "beta", store: str = "ubuntu") -> dict:
    return {"snap": snap, "track": track, "channel": channel, "store": store}


@pytest.fixture
def c3_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "C3_API_TOKEN", "test-token")
    monkeypatch.setattr(config, "C3_API_BASE_URL", C3_BASE_URL)


def _get(test_client: TestClient, artefact_id: int) -> Response:
    return make_authenticated_request(
        lambda: test_client.get(f"/v1/artefacts/{artefact_id}/missing-environments"),
        Permission.view_artefact,
    )


def test_get_404_when_artefact_not_found(test_client: TestClient):
    response = _get(test_client, 1)
    assert response.status_code == 404


def test_no_missing_when_c3_not_configured(
    test_client: TestClient, generator: DataGenerator, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(config, "C3_API_TOKEN", "")
    a = generator.gen_artefact(StageName.beta, family=FamilyName.snap)

    response = _get(test_client, a.id)

    assert response.status_code == 200
    assert response.json() == {
        "missing_environments": [],
        "previous_artefact_link": None,
    }


@pytest.mark.usefixtures("c3_configured")
def test_no_missing_for_family_without_c3(test_client: TestClient, generator: DataGenerator):
    a = generator.gen_artefact(StageName.pending, family=FamilyName.charm)

    response = _get(test_client, a.id)

    assert response.status_code == 200
    assert response.json()["missing_environments"] == []


@pytest.mark.usefixtures("c3_configured")
def test_c3_outage_returns_502(
    test_client: TestClient,
    generator: DataGenerator,
    requests_mock: Mocker,
):
    a = generator.gen_artefact(StageName.beta, family=FamilyName.snap)
    requests_mock.get(POOLS_URL, exc=requests.exceptions.ConnectionError)

    response = _get(test_client, a.id)

    assert response.status_code == 502


@pytest.mark.usefixtures("c3_configured")
def test_missing_environments_reported_with_previous_link(
    test_client: TestClient,
    generator: DataGenerator,
    requests_mock: Mocker,
):
    previous = generator.gen_artefact(StageName.beta, family=FamilyName.snap, version="1.0.0")
    current = generator.gen_artefact(StageName.beta, family=FamilyName.snap, version="1.0.1")
    build = generator.gen_artefact_build(current, architecture="amd64")
    env = generator.gen_environment("queue-a", architecture="amd64")
    generator.gen_artefact_build_environment_review(build, env)

    requests_mock.get(
        POOLS_URL,
        json={
            "results": [
                {
                    "name": "core-latest-beta",
                    "family": "snap",
                    "metadata": _snap_metadata(),
                    "environments": [_env("queue-a"), _env("queue-b")],
                    "description": "",
                }
            ],
            "next": None,
        },
    )

    response = _get(test_client, current.id)

    assert response.status_code == 200
    body = response.json()
    assert body["missing_environments"] == [{"name": "queue-b", "architecture": "amd64"}]
    assert body["previous_artefact_link"] == (f"http://localhost:30001/snaps/{previous.id}?Environment=queue-b")


@pytest.mark.usefixtures("c3_configured")
def test_no_missing_when_all_expected_present(
    test_client: TestClient,
    generator: DataGenerator,
    requests_mock: Mocker,
):
    a = generator.gen_artefact(StageName.beta, family=FamilyName.snap)
    build = generator.gen_artefact_build(a, architecture="amd64")
    for name in ("queue-a", "queue-b"):
        env = generator.gen_environment(name, architecture="amd64")
        generator.gen_artefact_build_environment_review(build, env)

    requests_mock.get(
        POOLS_URL,
        json={
            "results": [
                {
                    "name": "core-latest-beta",
                    "family": "snap",
                    "metadata": _snap_metadata(),
                    "environments": [_env("queue-a"), _env("queue-b")],
                }
            ],
            "next": None,
        },
    )

    response = _get(test_client, a.id)

    assert response.status_code == 200
    body = response.json()
    assert body["missing_environments"] == []
    assert body["previous_artefact_link"] is None


@pytest.mark.usefixtures("c3_configured")
def test_non_matching_pools_yield_no_missing(
    test_client: TestClient,
    generator: DataGenerator,
    requests_mock: Mocker,
):
    a = generator.gen_artefact(StageName.beta, family=FamilyName.snap, name="core")
    generator.gen_artefact_build(a, architecture="amd64")

    requests_mock.get(
        POOLS_URL,
        json={
            "results": [
                # Different snap, and a matching snap on a different channel:
                # neither should match on metadata.
                {
                    "name": "other-latest-beta",
                    "family": "snap",
                    "metadata": _snap_metadata(snap="other"),
                    "environments": [_env("queue-x")],
                },
                {
                    "name": "core-latest-stable",
                    "family": "snap",
                    "metadata": _snap_metadata(channel="stable"),
                    "environments": [_env("queue-y")],
                },
            ],
            "next": None,
        },
    )

    response = _get(test_client, a.id)

    assert response.status_code == 200
    assert response.json()["missing_environments"] == []


@pytest.mark.usefixtures("c3_configured")
def test_missing_environments_for_deb_matched_by_metadata(
    test_client: TestClient,
    generator: DataGenerator,
    requests_mock: Mocker,
):
    a = generator.gen_artefact(StageName.proposed, family=FamilyName.deb, name="linux-raspi", series="jammy")
    generator.gen_artefact_build(a, architecture="arm64")

    requests_mock.get(
        POOLS_URL,
        json={
            "results": [
                {
                    "name": "linux-raspi-jammy-main-proposed",
                    "family": "deb",
                    # source maps to the artefact's stage (the SRU pocket).
                    "metadata": {"kernel": "linux-raspi", "series": "jammy", "repo": "main", "source": "proposed"},
                    "environments": [_env("cm3-arm64", "arm64"), _env("rpi4b8g-arm64", "arm64")],
                }
            ],
            "next": None,
        },
    )

    response = _get(test_client, a.id)

    assert response.status_code == 200
    body = response.json()
    assert body["missing_environments"] == [
        {"name": "cm3-arm64", "architecture": "arm64"},
        {"name": "rpi4b8g-arm64", "architecture": "arm64"},
    ]


@pytest.mark.usefixtures("c3_configured")
def test_deb_stage_mismatch_yields_no_missing(
    test_client: TestClient,
    generator: DataGenerator,
    requests_mock: Mocker,
):
    a = generator.gen_artefact(StageName.proposed, family=FamilyName.deb, name="linux-raspi", series="jammy")
    generator.gen_artefact_build(a, architecture="arm64")

    requests_mock.get(
        POOLS_URL,
        json={
            "results": [
                {
                    "name": "linux-raspi-jammy-main-updates",
                    "family": "deb",
                    # Same kernel/series/repo but a different pocket (updates vs proposed).
                    "metadata": {"kernel": "linux-raspi", "series": "jammy", "repo": "main", "source": "updates"},
                    "environments": [_env("cm3-arm64", "arm64")],
                }
            ],
            "next": None,
        },
    )

    response = _get(test_client, a.id)

    assert response.status_code == 200
    assert response.json()["missing_environments"] == []


@pytest.mark.usefixtures("c3_configured")
def test_deb_metadata_mismatch_yields_no_missing(
    test_client: TestClient,
    generator: DataGenerator,
    requests_mock: Mocker,
):
    a = generator.gen_artefact(StageName.proposed, family=FamilyName.deb, name="linux-raspi", series="jammy")
    generator.gen_artefact_build(a, architecture="arm64")

    requests_mock.get(
        POOLS_URL,
        json={
            "results": [
                {
                    "name": "noble-linux-raspi-arm64",
                    "family": "deb",
                    "metadata": {"kernel": "linux-raspi", "series": "noble"},
                    "environments": [_env("cm3-arm64", "arm64")],
                }
            ],
            "next": None,
        },
    )

    response = _get(test_client, a.id)

    assert response.status_code == 200
    assert response.json()["missing_environments"] == []


@pytest.mark.usefixtures("c3_configured")
def test_missing_is_computed_per_name_and_arch(
    test_client: TestClient,
    generator: DataGenerator,
    requests_mock: Mocker,
):
    a = generator.gen_artefact(StageName.proposed, family=FamilyName.deb, name="linux-raspi", series="jammy")
    build = generator.gen_artefact_build(a, architecture="arm64")
    env = generator.gen_environment("rpi400", architecture="arm64")
    generator.gen_artefact_build_environment_review(build, env)

    requests_mock.get(
        POOLS_URL,
        json={
            "results": [
                {
                    "name": "jammy-linux-raspi",
                    "family": "deb",
                    "metadata": {"kernel": "linux-raspi", "series": "jammy"},
                    "environments": [
                        _env("rpi400", "arm64"),  # present: matched on name + arch
                        _env("rpi5b8g-server", "arm64"),  # missing
                        _env("nuc-amd64", "amd64"),  # missing: compared by its own arch
                    ],
                }
            ],
            "next": None,
        },
    )

    response = _get(test_client, a.id)

    assert response.status_code == 200
    assert response.json()["missing_environments"] == [
        {"name": "nuc-amd64", "architecture": "amd64"},
        {"name": "rpi5b8g-server", "architecture": "arm64"},
    ]


@pytest.mark.usefixtures("c3_configured")
def test_same_name_on_two_arches_is_disambiguated(
    test_client: TestClient,
    generator: DataGenerator,
    requests_mock: Mocker,
):
    a = generator.gen_artefact(StageName.proposed, family=FamilyName.deb, name="linux-raspi", series="jammy")
    build = generator.gen_artefact_build(a, architecture="arm64")
    # Same environment name present on arm64 but not amd64.
    env = generator.gen_environment("rpi400", architecture="arm64")
    generator.gen_artefact_build_environment_review(build, env)

    requests_mock.get(
        POOLS_URL,
        json={
            "results": [
                {
                    "name": "jammy-linux-raspi",
                    "family": "deb",
                    "metadata": {"kernel": "linux-raspi", "series": "jammy"},
                    "environments": [
                        _env("rpi400", "arm64"),  # present
                        _env("rpi400", "amd64"),  # missing: same name, different arch
                    ],
                }
            ],
            "next": None,
        },
    )

    response = _get(test_client, a.id)

    assert response.status_code == 200
    assert response.json()["missing_environments"] == [{"name": "rpi400", "architecture": "amd64"}]


@pytest.mark.usefixtures("c3_configured")
def test_multiple_environments_can_share_a_queue(
    test_client: TestClient,
    generator: DataGenerator,
    requests_mock: Mocker,
):
    a = generator.gen_artefact(StageName.proposed, family=FamilyName.deb, name="linux-raspi", series="jammy")
    generator.gen_artefact_build(a, architecture="arm64")

    requests_mock.get(
        POOLS_URL,
        json={
            "results": [
                {
                    "name": "jammy-linux-raspi",
                    "family": "deb",
                    "metadata": {"kernel": "linux-raspi", "series": "jammy"},
                    # Distinct environments may share a queue + arch (e.g. flavors).
                    "environments": [
                        _env("rpi3b-server", "arm64", queue="rpi3b"),
                        _env("rpi3b-desktop", "arm64", queue="rpi3b"),
                    ],
                }
            ],
            "next": None,
        },
    )

    response = _get(test_client, a.id)

    assert response.status_code == 200
    assert response.json()["missing_environments"] == [
        {"name": "rpi3b-desktop", "architecture": "arm64"},
        {"name": "rpi3b-server", "architecture": "arm64"},
    ]


@pytest.mark.usefixtures("c3_configured")
def test_null_pool_metadata_is_tolerated(
    test_client: TestClient,
    generator: DataGenerator,
    requests_mock: Mocker,
):
    a = generator.gen_artefact(StageName.beta, family=FamilyName.snap)
    generator.gen_artefact_build(a, architecture="amd64")

    requests_mock.get(
        POOLS_URL,
        json={
            "results": [
                {
                    "name": "core-latest-beta-amd64",
                    "family": "snap",
                    "metadata": None,
                    "environments": [_env("queue-a"), _env("queue-b")],
                }
            ],
            "next": None,
        },
    )

    response = _get(test_client, a.id)

    # null metadata is coerced to {} (no crash); with no keys it simply doesn't match.
    assert response.status_code == 200
    assert response.json()["missing_environments"] == []
