from pydantic import BaseModel, field_validator


class CreateUserRequest(BaseModel):
    launchpad_handle: str

    @field_validator("launchpad_handle")
    @classmethod
    def validate_handle(cls: type["CreateUserRequest"], launchpad_handle: str) -> str:
        if not launchpad_handle:
            raise ValueError("Must pass launchpad_handle")
        return launchpad_handle


class UserDTO(BaseModel):
    id: int
    launchpad_handle: str
