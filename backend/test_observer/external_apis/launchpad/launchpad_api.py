from launchpadlib.launchpad import Launchpad
from pydantic import EmailStr

from .models import LaunchpadUser


class LaunchpadAPI:
    def __init__(self):
        self.launchpad = Launchpad.login_anonymously(
            "test-observer", "production", version="devel"
        )

    def get_user_by_email(self, email: EmailStr) -> LaunchpadUser:
        user = self.launchpad.people.getByEmail(email=email)
        return LaunchpadUser(handle=user.name, email=email, name=user.display_name)
