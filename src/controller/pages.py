from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="src/view/templates")


@router.get("/")
async def login_page(request: Request):
    return templates.TemplateResponse(request, "pages/login.html", {"request": request})


@router.get("/home")
async def home_page(request: Request):
    return templates.TemplateResponse(request, "pages/home.html", {"request": request})
