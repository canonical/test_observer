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

from collections.abc import Mapping
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Security
from sqlalchemy import Table, desc, func, select
from sqlalchemy.orm import Session

from test_observer.common.config import MAX_LISTING_PAGE_LIMIT
from test_observer.common.enums import Permission
from test_observer.common.permissions import permission_checker
from test_observer.data_access.models import Base, ChangeAuthor
from test_observer.data_access.setup import get_db

from .models import AuditAuthorResponse, AuditDetailResponse, AuditHistoryResponse, AuditListItemResponse

router = APIRouter(tags=["audit"])

_AUDIT_TABLES: dict[str, tuple[Table, Table]] = {
    "artefacts": (
        Base.metadata.tables["artefact_audit"],
        Base.metadata.tables["artefact"],
    ),
    "environment-reviews": (
        Base.metadata.tables["artefact_build_environment_review_audit"],
        Base.metadata.tables["artefact_build_environment_review"],
    ),
}
_AUTHOR_COLUMNS = (
    ChangeAuthor.user_id.label("author_user_id"),
    ChangeAuthor.application_id.label("author_application_id"),
    ChangeAuthor.automation_name.label("author_automation_name"),
)


def _author_from_row(row: Mapping[str, Any]) -> AuditAuthorResponse:
    return AuditAuthorResponse(
        user_id=row["author_user_id"],
        application_id=row["author_application_id"],
        automation_name=row["author_automation_name"],
    )


def _list_history(
    db: Session,
    audit_table: Table,
    source_id: int,
    limit: int,
    offset: int,
) -> AuditHistoryResponse:
    count = db.execute(select(func.count()).select_from(audit_table).where(audit_table.c.id == source_id)).scalar_one()
    rows = db.execute(
        select(audit_table.c.audit_pk, audit_table.c.audit_timestamp, *_AUTHOR_COLUMNS)
        .join(ChangeAuthor, audit_table.c.audit_author_id == ChangeAuthor.id)
        .where(audit_table.c.id == source_id)
        .order_by(desc(audit_table.c.audit_timestamp), desc(audit_table.c.audit_pk))
        .limit(limit)
        .offset(offset)
    ).mappings()
    entries = [
        AuditListItemResponse(
            id=row["audit_pk"],
            created_at=row["audit_timestamp"],
            author=_author_from_row(dict(row)),
        )
        for row in rows
    ]
    return AuditHistoryResponse(entries=entries, count=count, limit=limit, offset=offset)


def _get_detail(
    db: Session,
    audit_table: Table,
    source_table: Table,
    source_id: int,
    audit_id: int,
) -> AuditDetailResponse:
    statement = (
        select(*audit_table.c, *_AUTHOR_COLUMNS)
        .join(ChangeAuthor, audit_table.c.audit_author_id == ChangeAuthor.id)
        .where(audit_table.c.id == source_id, audit_table.c.audit_pk == audit_id)
    )
    row = db.execute(statement).mappings().one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Audit entry {audit_id} not found")

    return AuditDetailResponse(
        id=row["audit_pk"],
        operation=row["audit_operation"],
        created_at=row["audit_timestamp"],
        author=_author_from_row(dict(row)),
        data={column.name: row[column.name] for column in source_table.columns},
    )


@router.get(
    "/artefacts/{artefact_id}",
    response_model=AuditHistoryResponse,
    dependencies=[Security(permission_checker, scopes=[Permission.view_artefact])],
)
def list_artefact_audit(
    artefact_id: int,
    limit: Annotated[
        int,
        Query(ge=1, le=MAX_LISTING_PAGE_LIMIT, description="Maximum number of results to return (default: 50)"),
    ] = 50,
    offset: Annotated[int, Query(ge=0, description="Number of results to skip for pagination (default: 0)")] = 0,
    db: Session = Depends(get_db),
) -> AuditHistoryResponse:
    audit_table, _ = _AUDIT_TABLES["artefacts"]
    return _list_history(db, audit_table, artefact_id, limit, offset)


@router.get(
    "/artefacts/{artefact_id}/{audit_id}",
    response_model=AuditDetailResponse,
    dependencies=[Security(permission_checker, scopes=[Permission.view_artefact])],
)
def get_artefact_audit(
    artefact_id: int,
    audit_id: int,
    db: Session = Depends(get_db),
) -> AuditDetailResponse:
    audit_table, source_table = _AUDIT_TABLES["artefacts"]
    return _get_detail(db, audit_table, source_table, artefact_id, audit_id)


@router.get(
    "/environment-reviews/{review_id}",
    response_model=AuditHistoryResponse,
    dependencies=[Security(permission_checker, scopes=[Permission.view_environment_review])],
)
def list_environment_review_audit(
    review_id: int,
    limit: Annotated[
        int,
        Query(ge=1, le=MAX_LISTING_PAGE_LIMIT, description="Maximum number of results to return (default: 50)"),
    ] = 50,
    offset: Annotated[int, Query(ge=0, description="Number of results to skip for pagination (default: 0)")] = 0,
    db: Session = Depends(get_db),
) -> AuditHistoryResponse:
    audit_table, _ = _AUDIT_TABLES["environment-reviews"]
    return _list_history(db, audit_table, review_id, limit, offset)


@router.get(
    "/environment-reviews/{review_id}/{audit_id}",
    response_model=AuditDetailResponse,
    dependencies=[Security(permission_checker, scopes=[Permission.view_environment_review])],
)
def get_environment_review_audit(
    review_id: int,
    audit_id: int,
    db: Session = Depends(get_db),
) -> AuditDetailResponse:
    audit_table, source_table = _AUDIT_TABLES["environment-reviews"]
    return _get_detail(db, audit_table, source_table, review_id, audit_id)
