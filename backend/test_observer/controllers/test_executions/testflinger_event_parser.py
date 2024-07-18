# Copyright 2024 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from test_observer.data_access.models import TestEvent


class TestflingerEventParser:
    def __init__(self):
        self.is_completed = False
        self.resource_url = None

    def process_events(self, events: list[TestEvent]):
        final_event = events[-1]
        if final_event.event_name == "job_end":
            self.is_completed = True
        if events[0].event_name == "job_start":
            self.resource_url = events[0].detail
