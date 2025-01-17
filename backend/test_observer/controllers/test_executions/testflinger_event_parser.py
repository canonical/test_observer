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

from test_observer.data_access.models import TestEvent


class TestflingerEventParser:
    def __init__(self):
        self.is_done = False
        self.has_issues = False
        self.resource_url = None

    def process_events(self, events: list[TestEvent]):
        final_event = events[-1]
        if final_event.event_name == "job_end":
            self.is_done = True
            if final_event.detail != "normal_exit":
                self.has_issues = True

        if events[0].event_name == "job_start":
            self.resource_url = events[0].detail
