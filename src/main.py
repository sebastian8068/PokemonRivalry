from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from src.controller.pages import router as page_router
from src.controller.login.login import router as login

app = FastAPI(title="Pokemon Rivalry")
app.include_router(page_router)
app.include_router(login, prefix="/auth")

app.mount("/static_login", StaticFiles(directory="./src/view/"), name="view")
