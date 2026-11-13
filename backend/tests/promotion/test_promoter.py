# Copyright 2024 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

"""Test promoter API"""

from collections.abc import Sequence
from contextlib import nullcontext
from datetime import datetime, timedelta

import pytest
from requests_mock import Mocker
from sqlalchemy import update
from sqlalchemy.orm import Session

from tasks import celery as celery_tasks
from test_observer.data_access.models import Artefact, ArtefactBuild
from test_observer.data_access.models_enums import ArtefactStatus, FamilyName
from test_observer.promotion import promoter
from tests.data_generator import DataGenerator


def _run_promoter(db_session: Session) -> None:
    """Run the real task against the transactional test session."""
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(celery_tasks, "SessionLocal", lambda: nullcontext(db_session))
        celery_tasks.run_promote_artefacts.run()


def _get_artefact(db_session: Session, artefact: Artefact) -> Artefact:
    persisted_artefact = db_session.get(Artefact, artefact.id)
    assert persisted_artefact is not None
    return persisted_artefact


@pytest.mark.parametrize("family,stage", [(FamilyName.snap, "edge"), (FamilyName.deb, "proposed")])
def test_run_promoter_defers_artefacts_without_builds(
    db_session: Session, generator: DataGenerator, requests_mock: Mocker, family: FamilyName, stage: str
) -> None:
    artefact = generator.gen_artefact(family=family, stage=stage, series="noble", repo="main")
    requests_mock.get(
        f"https://api.snapcraft.io/v2/snaps/info/{artefact.name}",
        json={"channel-map": []},
    )

    _run_promoter(db_session)

    persisted_artefact = _get_artefact(db_session, artefact)
    assert persisted_artefact.archived is False
    assert persisted_artefact.stage == stage
    assert requests_mock.called is False


def test_run_promoter_preserves_concurrent_review_changes(
    db_session: Session,
    generator: DataGenerator,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artefact = generator.gen_artefact(
        "edge",
        family=FamilyName.snap,
        status=ArtefactStatus.UNDECIDED,
    )
    generator.gen_artefact_build(artefact)

    def promote(
        snap_artefacts: Sequence[Artefact],
        _deb_artefacts: Sequence[Artefact],
    ) -> tuple[dict[int, bool | None], dict[int, str], dict[int, promoter.PromotionUpdate]]:
        db_session.execute(
            update(Artefact)
            .where(Artefact.id == artefact.id)
            .values(status=ArtefactStatus.APPROVED, comment="Reviewed during promotion")
        )
        snap_artefacts[0].stage = "beta"
        snap_artefacts[0].archived = True
        return {artefact.id: True}, {}, {artefact.id: {"stage": "beta", "archived": True}}

    monkeypatch.setattr(celery_tasks, "process_artefact_promotions", promote)

    _run_promoter(db_session)

    persisted_artefact = _get_artefact(db_session, artefact)
    assert persisted_artefact.stage == "beta"
    assert persisted_artefact.archived is True
    assert persisted_artefact.status == ArtefactStatus.APPROVED
    assert persisted_artefact.comment == "Reviewed during promotion"


def test_run_promoter_skips_update_when_patched_field_changed_concurrently(
    db_session: Session,
    generator: DataGenerator,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artefact = generator.gen_artefact("edge", name="concurrently-promoted-snap")
    generator.gen_artefact_build(artefact)

    def fetch_snap(_artefact: Artefact) -> str:
        db_session.execute(update(Artefact).where(Artefact.id == artefact.id).values(stage="stable"))
        return "beta"

    monkeypatch.setattr(promoter, "fetch_snap_promotion", fetch_snap)

    _run_promoter(db_session)

    persisted_artefact = _get_artefact(db_session, artefact)
    assert persisted_artefact.stage == "stable"
    assert persisted_artefact.archived is False


def test_run_promoter_skips_archive_update_when_archived_changed_concurrently(
    db_session: Session,
    generator: DataGenerator,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artefact = generator.gen_artefact(
        "proposed",
        family=FamilyName.deb,
        name="linux-generic",
        version="1.0",
        series="noble",
        repo="main",
    )
    generator.gen_artefact_build(artefact, "amd64")

    def fetch_deb(_artefact: Artefact) -> tuple[bool, str | None]:
        db_session.execute(update(Artefact).where(Artefact.id == artefact.id).values(archived=True))
        return False, None

    monkeypatch.setattr(promoter, "fetch_deb_promotion", fetch_deb)

    _run_promoter(db_session)

    persisted_artefact = _get_artefact(db_session, artefact)
    assert persisted_artefact.stage == "proposed"
    assert persisted_artefact.archived is True


def test_run_promoter_does_not_write_fields_after_fetch_failure(
    db_session: Session,
    generator: DataGenerator,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artefact = generator.gen_artefact("edge", family=FamilyName.snap)
    generator.gen_artefact_build(artefact)

    def fail_fetch(_artefact: Artefact) -> str | None:
        db_session.execute(update(Artefact).where(Artefact.id == artefact.id).values(stage="stable", archived=True))
        raise RuntimeError("Snapcraft unavailable")

    monkeypatch.setattr(promoter, "fetch_snap_promotion", fail_fetch)

    _run_promoter(db_session)

    persisted_artefact = _get_artefact(db_session, artefact)
    assert persisted_artefact.stage == "stable"
    assert persisted_artefact.archived is True


def test_run_promoter_skips_deb_without_fetch_result(
    db_session: Session,
    generator: DataGenerator,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artefact = generator.gen_artefact(
        "proposed",
        family=FamilyName.deb,
        name="linux-generic",
        version="1.0",
        series="noble",
        repo="main",
    )
    generator.gen_artefact_build(artefact, "amd64")
    db_session.execute(update(Artefact).where(Artefact.id == artefact.id).values(stage=""))

    def no_fetch_result(_artefact: Artefact) -> tuple[bool, str | None] | None:
        db_session.execute(update(Artefact).where(Artefact.id == artefact.id).values(stage="updates", archived=True))
        return None

    monkeypatch.setattr(promoter, "fetch_deb_promotion", no_fetch_result)

    _run_promoter(db_session)

    persisted_artefact = _get_artefact(db_session, artefact)
    assert persisted_artefact.stage == "updates"
    assert persisted_artefact.archived is True


def test_run_promoter_updates_only_fields_changed_by_fetch(
    db_session: Session,
    generator: DataGenerator,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    promoted_snap = generator.gen_artefact("edge", name="promoted-snap")
    archived_snap = generator.gen_artefact("edge", name="archived-snap")
    deb = generator.gen_artefact(
        "proposed",
        family=FamilyName.deb,
        name="linux-generic",
        version="1.0",
        series="noble",
        repo="main",
    )
    generator.gen_artefact_build(promoted_snap)
    generator.gen_artefact_build(archived_snap)
    generator.gen_artefact_build(deb, "amd64")

    def fetch_snap(artefact: Artefact) -> str | None:
        if artefact.id == promoted_snap.id:
            db_session.execute(update(Artefact).where(Artefact.id == artefact.id).values(archived=True))
            return "beta"
        db_session.execute(update(Artefact).where(Artefact.id == artefact.id).values(stage="stable"))
        return None

    def fetch_deb(_artefact: Artefact) -> tuple[bool, str | None]:
        db_session.execute(update(Artefact).where(Artefact.id == deb.id).values(stage="stable"))
        return True, None

    monkeypatch.setattr(promoter, "fetch_snap_promotion", fetch_snap)
    monkeypatch.setattr(promoter, "fetch_deb_promotion", fetch_deb)

    _run_promoter(db_session)

    promoted_after = _get_artefact(db_session, promoted_snap)
    archived_after = _get_artefact(db_session, archived_snap)
    deb_after = _get_artefact(db_session, deb)
    assert promoted_after.stage == "beta"
    assert promoted_after.archived is True
    assert archived_after.stage == "stable"
    assert archived_after.archived is False
    assert deb_after.stage == "stable"
    assert deb_after.archived is False


def test_run_promoter_tracks_same_name_version_rows_independently(
    db_session: Session,
    generator: DataGenerator,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failed_artefact = generator.gen_artefact(
        "edge",
        family=FamilyName.snap,
        name="same-snap",
        version="1.0",
        track="latest",
    )
    successful_artefact = generator.gen_artefact(
        "edge",
        family=FamilyName.snap,
        name="same-snap",
        version="1.0",
        track="2.0",
    )
    generator.gen_artefact_build(failed_artefact)
    generator.gen_artefact_build(successful_artefact)

    def fetch_snap(artefact: Artefact) -> str | None:
        if artefact.id == failed_artefact.id:
            db_session.execute(
                update(Artefact).where(Artefact.id == failed_artefact.id).values(stage="stable", archived=True)
            )
            raise RuntimeError("Snapcraft unavailable")
        return "beta"

    monkeypatch.setattr(promoter, "fetch_snap_promotion", fetch_snap)

    _run_promoter(db_session)

    failed_after_promotion = _get_artefact(db_session, failed_artefact)
    successful_after_promotion = _get_artefact(db_session, successful_artefact)
    assert failed_after_promotion.stage == "stable"
    assert failed_after_promotion.archived is True
    assert successful_after_promotion.stage == "beta"
    assert successful_after_promotion.archived is False


def test_run_to_move_artefact_snap(
    db_session: Session,
    requests_mock: Mocker,
    generator: DataGenerator,
):
    """
    If artefact's current stage name is different to its stage name on
    snapcraft, the artefact is moved to the next stage
    """
    # Arrange
    artefact = generator.gen_artefact(
        "edge",
        family=FamilyName.snap,
        name="core20",
        version="1.1.1",
        store="ubuntu",
        created_at=datetime.utcnow(),
    )
    build = generator.gen_artefact_build(artefact, revision=1)

    requests_mock.get(
        "https://api.snapcraft.io/v2/snaps/info/core20",
        json={
            "channel-map": [
                {
                    "channel": {
                        "architecture": build.architecture,
                        "name": "beta",
                        "released-at": "2023-05-17T12:39:07.471800+00:00",
                        "risk": "beta",
                        "track": "latest",
                    },
                    "created-at": "2023-04-10T09:59:22.309277+00:00",
                    "download": {
                        "deltas": [],
                        "sha3-384": "70f0",
                        "size": 130830336,
                        "url": "https://api.snapcraft.io/api/v1/snaps/download/...",
                    },
                    "revision": build.revision,
                    "type": "app",
                    "version": "1.1.1",
                },
            ]
        },
    )

    # Act
    _run_promoter(db_session)

    persisted_artefact = _get_artefact(db_session, artefact)

    # Assert
    assert persisted_artefact.stage == "beta"


def test_archives_snap_if_not_found(
    generator: DataGenerator,
    db_session: Session,
    requests_mock: Mocker,
):
    a = generator.gen_artefact(
        family=FamilyName.snap,
        stage="edge",
        name="core20",
        version="1.1.1",
        store="ubuntu",
    )
    generator.gen_artefact_build(a)

    requests_mock.get(
        f"https://api.snapcraft.io/v2/snaps/info/{a.name}",
        json={"channel-map": []},
    )

    _run_promoter(db_session)

    assert _get_artefact(db_session, a).archived


def test_custom_named_snaps_not_archived(
    generator: DataGenerator,
    db_session: Session,
    requests_mock: Mocker,
):
    a = generator.gen_artefact(
        family=FamilyName.snap,
        stage="edge",
        name="mycore20",
        version="1.1.1",
        store="ubuntu",
    )
    generator.gen_artefact_build(a)

    requests_mock.get(f"https://api.snapcraft.io/v2/snaps/info/{a.name}", status_code=404)

    _run_promoter(db_session)

    assert not _get_artefact(db_session, a).archived


def test_unknown_snapcraft_risk_does_not_archive_snap(
    generator: DataGenerator,
    db_session: Session,
    requests_mock: Mocker,
):
    artefact = generator.gen_artefact(stage="edge", name="custom-risk-snap", version="1", store="ubuntu")
    generator.gen_artefact_build(artefact)
    requests_mock.get(
        f"https://api.snapcraft.io/v2/snaps/info/{artefact.name}",
        json={
            "channel-map": [
                {
                    "channel": {
                        "architecture": "amd64",
                        "risk": "custom-risk",
                        "track": artefact.track,
                    },
                    "revision": 1,
                    "type": "app",
                    "version": artefact.version,
                }
            ]
        },
    )

    _run_promoter(db_session)

    promoted = _get_artefact(db_session, artefact)
    assert promoted.stage == "edge"
    assert promoted.archived is False


def test_custom_snap_and_deb_stages_are_not_promoted_or_archived(
    generator: DataGenerator,
    db_session: Session,
):
    snap = generator.gen_artefact(stage="custom", family=FamilyName.snap, name="custom-stage-snap")
    deb = generator.gen_artefact(
        stage="custom",
        family=FamilyName.deb,
        name="custom-stage-deb",
        version="1.0",
        series="noble",
        repo="main",
    )
    generator.gen_artefact_build(snap)
    generator.gen_artefact_build(deb, "amd64")

    _run_promoter(db_session)

    for artefact in (snap, deb):
        persisted = _get_artefact(db_session, artefact)
        assert persisted.stage == "custom"
        assert persisted.archived is False


def test_promote_snap_from_beta_to_stable(
    db_session: Session,
    requests_mock: Mocker,
    generator: DataGenerator,
):
    artefact = generator.gen_artefact("beta", store="ubuntu")
    build = generator.gen_artefact_build(artefact, revision=1)

    requests_mock.get(
        f"https://api.snapcraft.io/v2/snaps/info/{artefact.name}",
        json={
            "channel-map": [
                {
                    "channel": {
                        "architecture": build.architecture,
                        "risk": "stable",
                        "track": artefact.track,
                    },
                    "revision": build.revision,
                    "type": "app",
                    "version": artefact.version,
                },
            ]
        },
    )

    _run_promoter(db_session)

    assert _get_artefact(db_session, artefact).stage == "stable"


def test_snap_that_is_in_two_stages(
    db_session: Session,
    requests_mock: Mocker,
    generator: DataGenerator,
):
    artefact = generator.gen_artefact("edge", store="ubuntu")
    build = generator.gen_artefact_build(artefact, revision=1)

    requests_mock.get(
        f"https://api.snapcraft.io/v2/snaps/info/{artefact.name}",
        json={
            "channel-map": [
                {
                    "channel": {
                        "architecture": build.architecture,
                        "risk": "beta",
                        "track": artefact.track,
                    },
                    "revision": build.revision,
                    "type": "app",
                    "version": artefact.version,
                },
                {
                    "channel": {
                        "architecture": build.architecture,
                        "risk": "edge",
                        "track": artefact.track,
                    },
                    "revision": build.revision,
                    "type": "app",
                    "version": artefact.version,
                },
            ]
        },
    )

    _run_promoter(db_session)

    assert _get_artefact(db_session, artefact).stage == "beta"


def test_run_to_move_artefact_deb(
    db_session: Session,
    requests_mock: Mocker,
    generator: DataGenerator,
):
    """
    If artefact's current stage name is different to its stage name on
    deb archive, the artefact is moved to the next stage
    """
    # Arrange
    artefact1 = generator.gen_artefact(
        "proposed",
        family=FamilyName.deb,
        name="linux-generic",
        version="5.19.0.43.39",
        series="kinetic",
        repo="main",
        created_at=datetime.utcnow(),
    )
    artefact2 = generator.gen_artefact(
        "proposed",
        family=FamilyName.deb,
        name="linux-oem-22_04a",
        version="6.1.0.1028.29",
        series="kinetic",
        repo="main",
        created_at=datetime.utcnow() - timedelta(days=1),
    )
    artefact3 = generator.gen_artefact(
        "proposed",
        family=FamilyName.deb,
        name="linux-cloud-tools-5_15.0-86",
        version="5.15.0-86.96",
        series="kinetic",
        repo="main",
        created_at=datetime.utcnow() - timedelta(days=1),
    )
    db_session.add_all(
        [
            ArtefactBuild(architecture="amd64", artefact=artefact1),
            ArtefactBuild(architecture="amd64", artefact=artefact2),
            ArtefactBuild(architecture="amd64", artefact=artefact3),
        ]
    )
    db_session.commit()

    _prepare_archive_mock(requests_mock)

    # Act
    _run_promoter(db_session)

    # Assert
    assert _get_artefact(db_session, artefact1).stage == "updates"
    assert _get_artefact(db_session, artefact2).stage == "updates"
    assert _get_artefact(db_session, artefact3).stage == "updates"


def test_archives_deb_if_version_not_found(generator: DataGenerator, db_session: Session, requests_mock: Mocker):
    a = generator.gen_artefact(
        family=FamilyName.deb,
        stage="updates",
        name="linux-generic",
        version="missing-version",
        series="kinetic",
        repo="main",
    )
    generator.gen_artefact_build(a, "amd64")

    _prepare_archive_mock(requests_mock)

    _run_promoter(db_session)

    assert _get_artefact(db_session, a).archived


def test_keeps_deb_unarchived_if_custom_name(generator: DataGenerator, db_session: Session, requests_mock: Mocker):
    a = generator.gen_artefact(
        family=FamilyName.deb,
        stage="updates",
        name="some-custom-name",
        version="5.15.0-86.96",
        series="kinetic",
        repo="main",
    )
    generator.gen_artefact_build(a, "amd64")

    _prepare_archive_mock(requests_mock)

    _run_promoter(db_session)

    assert not _get_artefact(db_session, a).archived


def _prepare_archive_mock(requests_mock: Mocker) -> None:
    with open("tests/test_data/Packages-proposed.gz", "rb") as f:
        proposed_content = f.read()
    with open("tests/test_data/Packages-updates.gz", "rb") as f:
        updates_content = f.read()

    requests_mock.get(
        "http://us.archive.ubuntu.com/ubuntu/dists/kinetic-proposed/main/binary-amd64/Packages.gz",
        content=proposed_content,
    )
    requests_mock.get(
        "http://us.archive.ubuntu.com/ubuntu/dists/kinetic-updates/main/binary-amd64/Packages.gz",
        content=updates_content,
    )
