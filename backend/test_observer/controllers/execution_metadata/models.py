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


from pydantic import BaseModel, RootModel

from collections import defaultdict
from collections.abc import Sequence

from test_observer.data_access.models import TestExecutionMetadata


class ExecutionMetadata(RootModel[dict[str, list[str]]]):
    @classmethod
    def from_rows(cls, values: Sequence[TestExecutionMetadata]) -> "ExecutionMetadata":
        grouped = defaultdict(list)
        for row in values:
            grouped[row.category].append(row.value)
        return cls(dict(grouped))

    def to_rows(self) -> list[TestExecutionMetadata]:
        return [
            TestExecutionMetadata(category=category, value=value)
            for category, values in self.root.items()
            for value in values
        ]


class ExecutionMetadataGetResponse(BaseModel):
    execution_metadata: ExecutionMetadata


class ExecutionMetadataPostRequest(BaseModel):
    execution_metadata: ExecutionMetadata
