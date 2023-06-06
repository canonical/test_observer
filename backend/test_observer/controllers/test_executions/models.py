from pydantic import BaseModel

from test_observer.data_access.models_enums import TestExecutionStatus


class TestExecutionsPatchRequest(BaseModel):
    c3_link: str
    jenkins_link: str
    status: TestExecutionStatus
