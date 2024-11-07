from pydantic import BaseModel, Field
from typing import Optional, List

class UserAuthSchema(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
class UserResponse(BaseModel):
    username: str

    class Config:
        from_attributes = True
