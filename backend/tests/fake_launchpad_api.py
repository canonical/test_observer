from test_observer.external_apis.launchpad.launchpad_api import LaunchpadAPI
from test_observer.external_apis.launchpad.models import LaunchpadUser


class FakeLaunchpadAPI(LaunchpadAPI):
    def __init__(self):
        # override superclass init
        pass

    def get_user_by_email(self, email: str) -> LaunchpadUser | None:
        if email == "john.doe@canonical.com":
            return LaunchpadUser(handle="john-doe", email=email, name="John Doe")
        return None
