from pydantic import BaseModel


class EnvironmentDTO(BaseModel):
    id: int
    name: str
    architecture: str

    class Config:
        orm_mode = True


class TestExecutionDTO(BaseModel):
    id: int
    jenkins_link: str | None
    c3_link: str | None
    environment: EnvironmentDTO

    class Config:
        orm_mode = True


class ArtefactBuildDTO(BaseModel):
    id: int
    revision: int | None
    test_executions: list[TestExecutionDTO]

    class Config:
        orm_mode = True
