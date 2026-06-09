from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()

app.mount("/static_login", StaticFiles(directory="./src/view/"), name="view")


@app.get("/")
async def login():
    return FileResponse("./src/view/login_demo/login_prototype.html")
