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
