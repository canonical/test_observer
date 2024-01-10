from pydantic import BaseModel, EmailStr, constr


class LaunchpadUser(BaseModel):
    handle: constr(min_length=1)
    email: EmailStr
    name: constr(min_length=1)
