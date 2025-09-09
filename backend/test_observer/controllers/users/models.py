from pydantic import BaseModel


class TeamMinimalResponse(BaseModel):
    id: int
    name: str
    permissions: list[str]


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    launchpad_handle: str | None = None
    teams: list[TeamMinimalResponse]
    is_reviewer: bool


class UserPatch(BaseModel):
    is_reviewer: bool | None = None
