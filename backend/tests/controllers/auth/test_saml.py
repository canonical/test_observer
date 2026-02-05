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

from base64 import b64decode
from datetime import datetime, timedelta
from html.parser import HTMLParser
import json

import itsdangerous
import pytest
import requests
from sqlalchemy.orm import Session

from test_observer.common.config import SESSIONS_SECRET
from test_observer.data_access.models import UserSession, User, Team
from test_observer.data_access.repository import get_or_create
from test_observer.data_access.setup import SessionLocal


@pytest.fixture()
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class SimpleFormParser(HTMLParser):
    """Simple HTML parser to extract form data"""

    def __init__(self):
        super().__init__()
        self.inputs = {}
        self.in_form = False

    def handle_starttag(self, tag: str, attrs: list):
        attrs_dict = dict(attrs)

        if tag == "form":
            self.in_form = True

        elif tag == "input" and self.in_form:
            name = attrs_dict.get("name")
            value = attrs_dict.get("value", "")
            if name:
                self.inputs[name] = value

    def handle_endtag(self, tag: str):
        if tag == "form":
            self.in_form = False


class TestSAMLAuthentication:
    """Test SAML authentication workflow"""

    CREDENTIALS = {"username": "mark", "password": "password"}

    def test_complete_saml_flow(self, db_session: Session):
        """Test our SAML Service Provider (SP) implementation with end-to-end workflow

        This test focuses on validating our SP behavior:
        - SAML login initiation and redirect generation
        - ACS endpoint SAML response processing
        - User data extraction and response formatting
        - SAML logout and session clearing

        Uses a SimpleSAMLPHP IdP for integration testing
        """
        # Use a persistent session to maintain cookies and state throughout entire flow
        self.session = requests.Session()
        self.api_url = "http://localhost:30000"
        self.db_session = db_session

        sso_url = self._initiate_saml_login()
        auth_state, login_form_url = self._fetch_and_parse_login_form(sso_url)
        auth_response = self._submit_credentials(auth_state, login_form_url)
        api_response = self._process_saml_response(auth_response)
        self._verify_session(api_response)
        self._logout_and_verify_session_cleared()

    def _initiate_saml_login(self) -> str:
        response = self.session.get(
            f"{self.api_url}/v1/auth/saml/login", allow_redirects=False
        )
        # Test our SP: should redirect to IdP for authentication
        assert response.status_code == 307
        assert "location" in response.headers
        return response.headers["location"]

    def _fetch_and_parse_login_form(self, idp_url: str) -> tuple[str, str]:
        idp_response = self.session.get(idp_url, allow_redirects=True)

        parser = SimpleFormParser()
        parser.feed(idp_response.text)

        return parser.inputs["AuthState"], idp_response.url

    def _submit_credentials(
        self, auth_state: str, login_form_url: str
    ) -> requests.Response:
        login_data = {**self.CREDENTIALS, "AuthState": auth_state}
        return self.session.post(login_form_url, data=login_data, allow_redirects=False)

    def _process_saml_response(
        self, auth_response: requests.Response
    ) -> requests.Response:
        parser = SimpleFormParser()
        parser.feed(auth_response.text)

        return self.session.post(
            f"{self.api_url}/v1/auth/saml/acs",
            data={
                "SAMLResponse": parser.inputs.get("SAMLResponse"),
                "RelayState": parser.inputs.get("RelayState"),
            },
        )

    def _verify_session(self, response: requests.Response) -> None:
        assert response.status_code == 200
        assert "session" in response.cookies

        signer = itsdangerous.TimestampSigner(str(SESSIONS_SECRET))
        session = json.loads(b64decode(signer.unsign(response.cookies["session"])))
        assert "id" in session

        session = self.db_session.get(UserSession, session["id"])
        assert session
        assert session.expires_at < datetime.now() + timedelta(days=14)
        self._session_id = session.id

        user = session.user
        assert user
        assert user.name == "Mark"
        assert user.email == "mark@electricdemon.com"
        assert user.launchpad_handle == self.CREDENTIALS["username"]

    def _logout_and_verify_session_cleared(self) -> None:
        logout_response = self.session.get(
            f"{self.api_url}/v1/auth/saml/logout",
            headers={"X-CSRF-Token": "test"},
            allow_redirects=False,
        )

        assert logout_response.status_code == 307
        assert "location" in logout_response.headers

        logout_url = logout_response.headers["location"]
        self.session.get(logout_url, headers={"X-CSRF-Token": "test"})

        session = self.db_session.get(UserSession, self._session_id)
        assert session is None

    def _create_session_and_login(self) -> requests.Response:
        self.session = requests.Session()

        sso_url = self._initiate_saml_login()
        auth_state, login_form_url = self._fetch_and_parse_login_form(sso_url)
        auth_response = self._submit_credentials(auth_state, login_form_url)
        login_response = self._process_saml_response(auth_response)

        return login_response

    def test_team_membership_persists_after_login(self, db_session: Session):
        """Test that team membership persists after user logs in again

        This test verifies that when a user is added to a team, their membership
        is maintained even after logging in again. The SAML _create_user function
        should preserve existing team memberships when reassigning teams from
        SAML attributes.
        """
        self.api_url = "http://localhost:30000"
        self.db_session = db_session

        # Create user by logging in for the first time
        login_response = self._create_session_and_login()
        assert login_response.status_code == 200

        # Get user from database
        user = db_session.query(User).filter_by(email="mark@electricdemon.com").first()
        assert user is not None
        assert user.name == "Mark"

        # Create a team
        test_team = get_or_create(
            db_session,
            Team,
            {"name": "test-team"},
            {"permissions": [], "reviewer_families": []},
        )
        db_session.commit()

        # Add user to the team
        if user not in test_team.members:
            test_team.members.append(user)
            db_session.commit()

        # Verify user is in the team
        db_session.refresh(user)
        team_names = [t.name for t in user.teams]
        assert "test-team" in team_names

        # Log the user in again (create a new session to make it a fresh login)
        second_login_response = self._create_session_and_login()
        assert second_login_response.status_code == 200

        # User should still belong to the team
        db_session.refresh(user)
        team_names_after_login = [t.name for t in user.teams]
        assert "test-team" in team_names_after_login, (
            f"User should be in test-team after login. Teams: {team_names_after_login}"
        )
