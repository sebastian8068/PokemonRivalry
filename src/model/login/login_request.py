from pydantic import BaseModel
from pydantic import Field


class LoginRequest(BaseModel):
    username: str
    password: str


class SignUpRequest(BaseModel):
    username: str = Field(min_length=3, max_length=20)
    password: str = Field(min_length=6, max_length=20)
    confirm_password: str = Field(min_length=6, max_length=20)
