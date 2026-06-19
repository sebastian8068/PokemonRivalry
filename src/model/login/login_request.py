from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class SignUpRequest(BaseModel):
    username: str
    password: str
    confirm_password: str
