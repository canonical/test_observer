# Copyright 2026 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

from datetime import datetime

from pydantic import BaseModel

from test_observer.data_access.models_enums import FamilyName, TestResultStatus


class SearchPageTestResult(BaseModel):
    id: int
    created_at: datetime
    name: str
    category: str
    status: TestResultStatus


class SearchPageEnvironment(BaseModel):
    name: str


class SearchPageTestExecution(BaseModel):
    id: int
    environment: SearchPageEnvironment
    test_plan: str


class SearchPageArtefact(BaseModel):
    id: int
    name: str
    version: str
    track: str
    family: FamilyName


class SearchPageArtefactBuild(BaseModel):
    architecture: str


class TestResultSearchPageRow(BaseModel):
    test_result: SearchPageTestResult
    test_execution: SearchPageTestExecution
    artefact: SearchPageArtefact
    artefact_build: SearchPageArtefactBuild


class TestResultSearchPage(BaseModel):
    limit: int
    offset: int
    test_results: list[TestResultSearchPageRow]
