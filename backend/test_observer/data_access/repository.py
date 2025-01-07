# Copyright 2023 Canonical Ltd.
# All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Written by:
#        Nadzeya Hutsko <nadzeya.hutsko@canonical.com>
#        Omar Selo <omar.selo@canonical.com>
"""Services for working with objects from DB"""


from collections.abc import Iterable
from typing import Any

from sqlalchemy import and_, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from .models import Artefact, ArtefactBuild, DataModel
from .models_enums import FamilyName


def get_artefacts_by_family(
    session: Session,
    family: FamilyName,
    latest_only: bool = True,
    load_environment_reviews: bool = False,
    order_by_columns: Iterable[Any] | None = None,
) -> list[Artefact]:
    """
    Get all the artefacts

    :session: DB session
    :family: name of the family
    :latest_only: return only latest artefacts, i.e. for each group of artefacts
                  with the same name and source but different version return
                  the latest one in a stage
    :load_stage: whether to eagerly load stage object in all artefacts
    :return: list of Artefacts
    """
    if latest_only:
        base_query = (
            session.query(
                Artefact.stage,
                Artefact.name,
                func.max(Artefact.created_at).label("max_created"),
            )
            .filter(Artefact.family == family)
            .group_by(Artefact.stage, Artefact.name)
        )

        match family:
            case FamilyName.snap:
                subquery = (
                    base_query.add_columns(Artefact.track)
                    .group_by(Artefact.track)
                    .subquery()
                )

                query = session.query(Artefact).join(
                    subquery,
                    and_(
                        Artefact.stage == subquery.c.stage,
                        Artefact.name == subquery.c.name,
                        Artefact.created_at == subquery.c.max_created,
                        Artefact.track == subquery.c.track,
                    ),
                )

            case FamilyName.deb:
                subquery = (
                    base_query.add_columns(Artefact.repo, Artefact.series)
                    .group_by(Artefact.repo, Artefact.series)
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
                    ),
                )

            case FamilyName.charm:
                subquery = (
                    base_query.join(ArtefactBuild)
                    .add_columns(Artefact.track, ArtefactBuild.architecture)
                    .group_by(Artefact.track, ArtefactBuild.architecture)
                    .subquery()
                )

                query = (
                    session.query(Artefact)
                    .join(ArtefactBuild)
                    .join(
                        subquery,
                        and_(
                            Artefact.stage == subquery.c.stage,
                            Artefact.name == subquery.c.name,
                            Artefact.created_at == subquery.c.max_created,
                            Artefact.track == subquery.c.track,
                            ArtefactBuild.architecture == subquery.c.architecture,
                        ),
                    )
                    .distinct()
                )

    else:
        query = session.query(Artefact).filter(Artefact.family == family)

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
