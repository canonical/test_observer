# Copyright 2023 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2023 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

"""Services for working with objects from DB"""

from collections.abc import Iterable
from typing import Any

from pydantic import HttpUrl
from sqlalchemy import and_, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy.orm.attributes import set_committed_value

from .models import Artefact, ArtefactBuild, DataModel, Environment, TestExecution, TestExecutionRelevantLink
from .models_enums import FamilyName


def get_artefacts_by_family(
    session: Session,
    family: FamilyName,
    load_environment_reviews: bool = False,
    load_builds: bool = False,
    order_by_columns: Iterable[Any] | None = None,
) -> list[Artefact]:
    """
    Get the most recent instance of every artefact belonging to a given family

    :session: DB session
    :family: name of the family
    :load_environment_reviews: whether to eagerly load each build's environment reviews
    :load_builds: whether to eagerly load each artefact's builds
    :order_by_columns: optional columns to order the results by
    :return: list of Artefacts
    """
    if family == FamilyName.charm:
        # For charm family, only filter by archived status
        query = session.query(Artefact).filter(Artefact.family == family, Artefact.archived.is_(False))
    else:
        base_query = (
            session.query(
                Artefact.stage,
                Artefact.name,
                func.max(Artefact.created_at).label("max_created"),
            )
            .filter(Artefact.family == family, Artefact.archived.is_(False))
            .group_by(Artefact.stage, Artefact.name)
        )

        match family:
            case FamilyName.snap:
                subquery = (
                    base_query.add_columns(Artefact.track, Artefact.branch)
                    .group_by(Artefact.track, Artefact.branch)
                    .subquery()
                )

                query = session.query(Artefact).join(
                    subquery,
                    and_(
                        Artefact.stage == subquery.c.stage,
                        Artefact.name == subquery.c.name,
                        Artefact.created_at == subquery.c.max_created,
                        Artefact.track == subquery.c.track,
                        Artefact.branch == subquery.c.branch,
                    ),
                )

            case FamilyName.deb:
                subquery = (
                    base_query.add_columns(Artefact.repo, Artefact.series, Artefact.source)
                    .group_by(Artefact.repo, Artefact.series, Artefact.source)
                    .subquery()
                )

                query = session.query(Artefact).join(
                    subquery,
                    and_(
                        Artefact.stage == subquery.c.stage,
                        Artefact.name == subquery.c.name,
                        Artefact.created_at == subquery.c.max_created,
                        Artefact.repo == subquery.c.repo,
                        Artefact.series == subquery.c.series,
                        Artefact.source == subquery.c.source,
                    ),
                )

            case FamilyName.image:
                subquery = (
                    base_query.add_columns(Artefact.os, Artefact.release)
                    .group_by(Artefact.os, Artefact.release)
                    .subquery()
                )

                query = session.query(Artefact).join(
                    subquery,
                    and_(
                        Artefact.stage == subquery.c.stage,
                        Artefact.name == subquery.c.name,
                        Artefact.created_at == subquery.c.max_created,
                        Artefact.os == subquery.c.os,
                        Artefact.release == subquery.c.release,
                    ),
                )

            case FamilyName.solution:
                subquery = (
                    base_query.add_columns(Artefact.source, Artefact.track)
                    .group_by(Artefact.source, Artefact.track)
                    .subquery()
                )

                query = session.query(Artefact).join(
                    subquery,
                    and_(
                        Artefact.stage == subquery.c.stage,
                        Artefact.name == subquery.c.name,
                        Artefact.created_at == subquery.c.max_created,
                        Artefact.source == subquery.c.source,
                        Artefact.track == subquery.c.track,
                    ),
                )

    if load_environment_reviews:
        query = query.options(selectinload(Artefact.builds).selectinload(ArtefactBuild.environment_reviews))
    elif load_builds:
        query = query.options(joinedload(Artefact.builds))

    if order_by_columns:
        query = query.order_by(*order_by_columns)

    return query.all()


def populate_expected_environment_status(session: Session, artefacts: Iterable[Artefact]) -> None:
    artefacts_by_id = {artefact.id: artefact for artefact in artefacts}
    artefact_ids = list(artefacts_by_id)
    if not artefact_ids:
        return

    expected_environments_by_artefact: dict[int, list[Environment]] = {artefact_id: [] for artefact_id in artefact_ids}
    expected_environment_rows = session.execute(
        select(Artefact.id, Environment)
        .join(Artefact.expected_environments)
        .where(Artefact.id.in_(artefact_ids))
        .order_by(Artefact.id, Environment.name, Environment.architecture)
    ).all()
    artefact_ids_with_expectations: set[int] = set()
    for artefact_id, environment in expected_environment_rows:
        expected_environments_by_artefact[artefact_id].append(environment)
        artefact_ids_with_expectations.add(artefact_id)

    for artefact_id, artefact in artefacts_by_id.items():
        set_committed_value(artefact, "expected_environments", expected_environments_by_artefact[artefact_id])
        object.__setattr__(artefact, "_missing_expected_environments_cache", [])

    if not artefact_ids_with_expectations:
        return

    latest_builds = (
        select(
            ArtefactBuild.id.label("build_id"),
            ArtefactBuild.artefact_id.label("artefact_id"),
            func.row_number()
            .over(
                partition_by=(ArtefactBuild.artefact_id, ArtefactBuild.architecture),
                order_by=func.coalesce(ArtefactBuild.revision, 0).desc(),
            )
            .label("build_rank"),
        )
        .where(ArtefactBuild.artefact_id.in_(artefact_ids_with_expectations))
        .subquery()
    )
    tested_environment_rows = session.execute(
        select(latest_builds.c.artefact_id, TestExecution.environment_id)
        .select_from(latest_builds)
        .join(TestExecution, TestExecution.artefact_build_id == latest_builds.c.build_id)
        .where(latest_builds.c.build_rank == 1)
        .distinct()
    ).all()
    tested_environment_ids_by_artefact: dict[int, set[int]] = {
        artefact_id: set() for artefact_id in artefact_ids_with_expectations
    }
    for artefact_id, environment_id in tested_environment_rows:
        tested_environment_ids_by_artefact[artefact_id].add(environment_id)

    for artefact_id in artefact_ids_with_expectations:
        artefact = artefacts_by_id[artefact_id]
        expected_environments = expected_environments_by_artefact[artefact_id]
        object.__setattr__(
            artefact,
            "_missing_expected_environments_cache",
            [
                environment
                for environment in expected_environments
                if environment.id not in tested_environment_ids_by_artefact[artefact_id]
            ],
        )


def get_or_create(
    db: Session,
    model: type[DataModel],
    filter_kwargs: dict,
    creation_kwargs: dict | None = None,
) -> DataModel:
    """
    Creates an object if it doesn't exist, otherwise returns the existing one.

    To ensure atomicity, this function does NOT commit the transaction.
    The caller is responsible for committing the session when appropriate.

    WARNING: Be cautious when filtering by nullable fields that have unique constraints,
    as PostgreSQL allows multiple NULL values in unique constraints. This can cause
    queries like filter_by(field=None) to match multiple records and return an
    arbitrary one. If you need to create records with NULL unique fields, create
    them directly instead of using get_or_create.

    :db: DB session
    :model: model to create e.g. Stage, Family, Artefact
    :filter_kwargs: arguments to pass to the model when querying and creating
    :creation_kwargs: extra arguments to pass to the model when creating only
    """

    # A previous version of this function would always try to create a new instance
    # and only query for the existing one if there was an IntegrityError.
    # This filled the PostgreSQL logs with errors on nearly every call,
    # which made the logs very noisy.
    # Example log message:

    # <timestamp> STATEMENT:  INSERT INTO <table> (<fields>) VALUES (<values>) RETURNING <outputs> # noqa: E501
    # <timestamp> ERROR:  duplicate key value violates unique constraint "<key>"
    # <timestamp> DETAIL:  Key (<key>)=(<value>) already exists.

    # We now check for the instance first to avoid this
    instance = db.query(model).filter_by(**filter_kwargs).first()
    if instance:
        return instance

    creation_kwargs = creation_kwargs or {}
    instance = model(**filter_kwargs, **creation_kwargs)

    # The instance did not exist when we queried,
    # but it might have been created by another process before we try to add it.
    # Thus, we still need to catch the IntegrityError
    # and query for the instance in that case, but this should be much rarer
    try:
        # Attempt to add and commit the new instance
        # Use a nested transaction to avoid rolling back the entire session
        with db.begin_nested():
            db.add(instance)
            # Ensure the INSERT is executed immediately
            # to catch IntegrityError here if it occurs
            db.flush()
    except IntegrityError:
        # Query and return the existing instance
        instance = db.query(model).filter_by(**filter_kwargs).one()

    return instance


def create_test_execution_relevant_link(
    session: Session, test_execution_id: int, label: str, url: HttpUrl
) -> TestExecutionRelevantLink:
    new_link = TestExecutionRelevantLink(test_execution_id=test_execution_id, label=label, url=url)
    session.add(new_link)
    session.commit()
    session.refresh(new_link)
    return new_link
