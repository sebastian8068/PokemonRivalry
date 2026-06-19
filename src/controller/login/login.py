from fastapi import APIRouter
from src.model.login.login_request import LoginRequest, SignUpRequest

router = APIRouter(tags=["login"])


@router.post("/login")
async def get_login(data: LoginRequest):
    print("username:", data.username, "password:", data.password)
    return {"message": f"Hi {data.username}"}


@router.post("/signup")
async def get_sign_up(data: SignUpRequest):
    print(
        "username:",
        data.username,
        "password:",
        data.password,
        "confirmpassword:",
        data.confirm_password,
    )
    return {"message": f"Hi {data.username}"}
