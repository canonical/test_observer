from pydantic import BaseModel


class StartTestExecutionRequest(BaseModel):
    family: str
    name: str
    version: str
    revision: int | None = None
    source: dict
    arch: str
    execution_stage: str
    environment: str
