from typing import Annotated

from pydantic import BaseModel, EmailStr, constr


class LaunchpadUser(BaseModel):
    handle: Annotated[str, constr(min_length=1)]
    email: EmailStr
    name: Annotated[str, constr(min_length=1)]
