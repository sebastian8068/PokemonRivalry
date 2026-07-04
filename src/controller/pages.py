from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from src.model.login.auth_service import decode_token
from src.model.base import User
from src.model.database import DbSession

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="src/view/templates")


@router.get("/")
async def login_page(request: Request):
    return templates.TemplateResponse(
        request, "pages/login.html", {"request": request}
    )


@router.get("/home")
async def home_page(request: Request, db: DbSession):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/")
    token_data = decode_token(token)
    if token_data is None or token_data.username is None:
        return RedirectResponse(url="/")
    result = await db.execute(
        select(User).where(User.Name == token_data.username)
    )
    user = result.scalar_one_or_none()
    if user is None:
        return RedirectResponse(url="/")
    return templates.TemplateResponse(
        request,
        "pages/home.html",
        {"request": request, "username": user.Name, "score": user.Score},
    )
