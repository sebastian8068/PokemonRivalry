from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(tags=["pages"])


@router.get("/")
async def login_page():
    return FileResponse("./src/view/login/index.html")
