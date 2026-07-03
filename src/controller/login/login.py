from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import status
from src.model.login.login_request import LoginRequest, SignUpRequest
from src.model.base import User
from src.model.database import DbSession

router = APIRouter(tags=["login"])


@router.post("/login")
async def get_login(data: LoginRequest):
    return {"message": f"Hi {data.username}"}


@router.post("/signup")
async def get_sign_up(data: SignUpRequest):
    if data.password != data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords don't match",
        )

    return {}
