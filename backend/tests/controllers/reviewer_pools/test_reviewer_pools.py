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

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from test_observer.data_access.models import ReviewerPool, User
from test_observer.common.permissions import Permission
from tests.conftest import make_authenticated_request


class TestReviewerPoolsAPI:
    """Tests for reviewer pools endpoints"""

    def test_get_all_pools(self, test_client: TestClient):
        """Test getting all reviewer pools"""
        response = make_authenticated_request(
            lambda: test_client.get("/v1/reviewer-pools"),
            Permission.view_user,
        )

        assert response.status_code == 200
        pools = response.json()
        assert len(pools) == 2

        cert_pool = next((p for p in pools if p["name"] == "cert"), None)
        assert cert_pool is not None
        assert "snap" in cert_pool["families"]

        sqa_pool = next((p for p in pools if p["name"] == "sqa"), None)
        assert sqa_pool is not None
        assert "charm" in sqa_pool["families"]

    def test_get_pool_by_id(self, test_client: TestClient):
        """Test getting a specific reviewer pool"""
        response = make_authenticated_request(
            lambda: test_client.get("/v1/reviewer-pools/1"),
            Permission.view_user,
        )

        assert response.status_code == 200
        pool = response.json()
        assert pool["id"] == 1
        assert pool["name"] == "cert"

    def test_get_nonexistent_pool(self, test_client: TestClient):
        """Test getting a pool that doesn't exist"""
        response = make_authenticated_request(
            lambda: test_client.get("/v1/reviewer-pools/9999"),
            Permission.view_user,
        )

        assert response.status_code == 404

    def test_add_member_returns_403_for_non_admin(self, test_client: TestClient):
        """Test that non-admin cannot add members"""
        response = make_authenticated_request(
            lambda: test_client.post("/v1/reviewer-pools/1/members/1"),
            Permission.change_user,
        )
        assert response.status_code == 403

    def test_remove_member_returns_403_for_non_admin(self, test_client: TestClient):
        """Test that non-admin cannot remove members"""
        response = make_authenticated_request(
            lambda: test_client.delete("/v1/reviewer-pools/1/members/1"),
            Permission.change_user,
        )
        assert response.status_code == 403


class TestReviewerPoolModel:
    """Tests for ReviewerPool ORM model"""

    def test_pool_created_with_families(self, db_session: Session):
        """Test that pools are created with correct families"""
        cert_pool = db_session.query(ReviewerPool).filter_by(name="cert").first()
        assert cert_pool is not None
        assert cert_pool.families == ["snap", "deb", "image"]

        sqa_pool = db_session.query(ReviewerPool).filter_by(name="sqa").first()
        assert sqa_pool is not None
        assert sqa_pool.families == ["charm"]

    def test_pool_members_relationship(self, db_session: Session):
        """Test pool and user relationship"""
        user = User(
            email="pool_member_test@canonical.com",
            name="Pool Member Test",
            is_reviewer=True,
            is_admin=False,
        )
        db_session.add(user)
        db_session.commit()

        pool = db_session.query(ReviewerPool).filter_by(name="cert").first()
        assert pool is not None
        pool.members.append(user)
        db_session.commit()

        assert user in pool.members
        assert pool in user.reviewer_pools

    def test_remove_member_from_pool(self, db_session: Session):
        """Test removing a member from a pool"""
        user = User(
            email="pool_remove_test@canonical.com",
            name="Pool Remove Test",
            is_reviewer=True,
            is_admin=False,
        )
        db_session.add(user)
        db_session.commit()

        pool = db_session.query(ReviewerPool).filter_by(name="cert").first()
        assert pool is not None
        pool.members.append(user)
        db_session.commit()

        assert user in pool.members

        pool.members.remove(user)
        db_session.commit()

        assert user not in pool.members

    def test_pool_unique_constraint(self, db_session: Session):
        """Test that pool names are unique"""
        pool = ReviewerPool(
            name="cert",
            families=["test"],
        )
        db_session.add(pool)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_pools_have_correct_families(self, db_session: Session):
        """Test all families are correctly assigned to pools"""
        cert_pool = db_session.query(ReviewerPool).filter_by(name="cert").first()
        assert cert_pool is not None

        sqa_pool = db_session.query(ReviewerPool).filter_by(name="sqa").first()
        assert sqa_pool is not None

        assert "snap" in cert_pool.families
        assert "deb" in cert_pool.families
        assert "image" in cert_pool.families

        assert "charm" in sqa_pool.families
        assert "snap" not in sqa_pool.families
