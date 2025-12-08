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

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from test_observer.common.constants import QueryValue
from test_observer.controllers.execution_metadata.models import ExecutionMetadata
from test_observer.data_access.models_enums import (
    FamilyName,
    TestResultStatus,
    TestExecutionStatus,
)


class TestResultSearchFilters(BaseModel):
    families: list[FamilyName] = Field(default_factory=list)
    artefacts: list[str] = Field(default_factory=list)
    artefact_is_archived: bool | None = None
    environments: list[str] = Field(default_factory=list)
    test_cases: list[str] = Field(default_factory=list)
    template_ids: list[str] = Field(default_factory=list)
    execution_metadata: ExecutionMetadata = Field(default_factory=ExecutionMetadata)
    issues: list[int] | Literal[QueryValue.ANY, QueryValue.NONE] = Field(
        default_factory=list
    )
    test_result_statuses: list[TestResultStatus] = Field(default_factory=list)
    test_execution_statuses: list[TestExecutionStatus] = Field(default_factory=list)
    assignee_ids: list[int] | Literal[QueryValue.ANY, QueryValue.NONE] = Field(
        default_factory=list
    )
    rerun_is_requested: bool | None = None
    execution_is_latest: bool | None = None
    from_date: datetime | None = None
    until_date: datetime | None = None
    offset: int | None = None
    limit: int | None = None

    def has_filters(self) -> bool:
        """
        Check if at least one meaningful filter is provided.

        Excludes pagination and date range parameters.
        """
        return any(
            not (
                (isinstance(value, list) and len(value) == 0)
                or (isinstance(value, dict) and len(value) == 0)
                or value is None
            )
            for key, value in self.model_dump().items()
            if key not in ("from_date", "until_date", "offset", "limit")
        )
