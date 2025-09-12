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


"""Services for working with objects from DB"""

from collections.abc import Iterable
from typing import Any
from pydantic import HttpUrl

from sqlalchemy import and_, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from .models import Artefact, ArtefactBuild, DataModel, TestExecutionRelevantLink
from .models_enums import FamilyName


def get_artefacts_by_family(
    session: Session,
    family: FamilyName,
    load_environment_reviews: bool = False,
    order_by_columns: Iterable[Any] | None = None,
) -> list[Artefact]:
    """
    Get all the artefacts

    :session: DB session
    :family: name of the family
    :load_stage: whether to eagerly load stage object in all artefacts
    :return: list of Artefacts
    """
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

        case FamilyName.charm | FamilyName.snap:
            query = session.query(Artefact).where(
                and_(
                    Artefact.family == family,
                    Artefact.archived.is_(False),
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

    if load_environment_reviews:
        query = query.options(
            joinedload(Artefact.builds).joinedload(ArtefactBuild.environment_reviews)
        )

    if order_by_columns:
        query = query.order_by(*order_by_columns)

    return query.all()


def get_or_create(
    db: Session,
    model: type[DataModel],
    filter_kwargs: dict,
    creation_kwargs: dict | None = None,
) -> DataModel:
    """
    Creates an object if it doesn't exist, otherwise returns the existing one

    :db: DB session
    :model: model to create e.g. Stage, Family, Artefact
    :filter_kwargs: arguments to pass to the model when querying and creating
    :creation_kwargs: extra arguments to pass to the model when creating only
    """
    creation_kwargs = creation_kwargs or {}
    instance = model(**filter_kwargs, **creation_kwargs)

    try:
        # Attempt to add and commit the new instance
        # Use a nested transaction to avoid rolling back the entire session
        with db.begin_nested():
            db.add(instance)
    except IntegrityError:
        # Query and return the existing instance
        instance = db.query(model).filter_by(**filter_kwargs).one()
    db.commit()
    return instance


def create_test_execution_relevant_link(
    session: Session, test_execution_id: int, label: str, url: HttpUrl
) -> TestExecutionRelevantLink:
    new_link = TestExecutionRelevantLink(
        test_execution_id=test_execution_id, label=label, url=url
    )
    session.add(new_link)
    session.commit()
    session.refresh(new_link)
    return new_link
