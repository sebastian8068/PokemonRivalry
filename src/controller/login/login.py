from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from src.model.login.login_request import LoginRequest, SignUpRequest
from src.model.login.login_response import Token
from src.model.login.auth_service import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)
from src.model.base import User
from src.model.database import DbSession

router = APIRouter(tags=["login"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    db: DbSession, token: str = Depends(oauth2_scheme)
) -> User:
    token_data = decode_token(token)
    if token_data is None or token_data.username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    result = await db.execute(
        select(User).where(User.Name == token_data.username)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


@router.post("/signup")
async def sign_up(data: SignUpRequest, response: Response, db: DbSession):
    if data.password != data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords don't match",
        )
    result = await db.execute(select(User).where(User.Name == data.username))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )
    hashed_pw = hash_password(data.password)
    new_user = User(Name=data.username, Password=hashed_pw)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    token = create_access_token({"sub": new_user.Name})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=3600,
        samesite="lax",
        path="/",
    )
    return Token(access_token=token)


@router.post("/login")
async def login(data: LoginRequest, response: Response, db: DbSession):
    result = await db.execute(select(User).where(User.Name == data.username))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(data.password, user.Password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    token = create_access_token({"sub": user.Name})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=3600,
        samesite="lax",
        path="/",
    )
    return Token(access_token=token)


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {"username": current_user.Name, "score": current_user.Score}
