from pydantic import BaseModel, EmailStr


class CreateUserRequest(BaseModel):
    launchpad_email: EmailStr


class UserDTO(BaseModel):
    id: int
    launchpad_handle: str
    launchpad_email: str
    name: str
