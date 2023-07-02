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


from sqlalchemy import and_, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session, joinedload


from .models_enums import FamilyName
from .models import DataModel, Family, Stage, Artefact


def get_stage_by_name(
    session: Session, stage_name: str, family: Family
) -> Stage | None:
    """
    Get the stage object by its name

    :session: DB session
    :stage_name: name of the stage
    :family: the Family object where stages are located
    :return: Stage
    """
    stage = (
        session.query(Stage)
        .filter(Stage.name == stage_name, Stage.family == family)
        .one_or_none()
    )
    return stage


def get_artefacts_by_family_name(
    session: Session, family_name: FamilyName, latest_only: bool = True
) -> list[Artefact]:
    """
    Get all the artefacts in a family

    :session: DB session
    :family_name: name of the family
    :latest_only: return only latest artefacts, i.e. for each group of artefacts
                  with the same name and source but different version return
                  the latest one in a stage
    :return: list of Artefacts
    """
    if latest_only:
        subquery = (
            session.query(
                Artefact.stage_id,
                Artefact.name,
                Artefact.source,
                func.max(Artefact.created_at).label("max_created"),
            )
            .join(Stage)
            .filter(Stage.family.has(Family.name == family_name))
            .group_by(Artefact.stage_id, Artefact.name, Artefact.source)
            .subquery()
        )

        artefacts = (
            session.query(Artefact)
            .join(
                subquery,
                and_(
                    Artefact.stage_id == subquery.c.stage_id,
                    Artefact.name == subquery.c.name,
                    Artefact.source == subquery.c.source,
                    Artefact.created_at == subquery.c.max_created,
                ),
            )
            .all()
        )
    else:
        artefacts = (
            session.query(Artefact)
            .join(Stage)
            .filter(Stage.family.has(Family.name == family_name))
            .options(joinedload(Artefact.stage))
            .all()
        )
    return artefacts


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
    # Try to create first to avoid race conditions
    creation_kwargs = creation_kwargs or {}
    stmt = (
        insert(model)
        .values([{**filter_kwargs, **creation_kwargs}])
        .on_conflict_do_nothing()
        .returning(model)
    )

    result = db.execute(stmt).scalar_one_or_none()
    db.commit()

    if result is None:
        # If the object already existed, we need to query it
        result = db.query(model).filter_by(**filter_kwargs).one()

    return result
