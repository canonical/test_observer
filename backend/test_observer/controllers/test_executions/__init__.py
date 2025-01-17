# Copyright (C) 2023 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from fastapi import APIRouter

from . import (
    end_test,
    get_test_results,
    patch,
    post_results,
    reruns,
    start_test,
    status_update,
)

router = APIRouter(tags=["test-executions"])
router.include_router(start_test.router)
router.include_router(get_test_results.router)
router.include_router(end_test.router)
router.include_router(patch.router)
router.include_router(reruns.router)
router.include_router(status_update.router)
router.include_router(post_results.router)
