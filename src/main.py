from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from src.model.login.rate_limiting import limiter
from src.controller.pages import router as page_router
from src.controller.login.login import router as login
from src.controller.team import router as team_router
from src.controller.battle import router as battle_router
from src.controller.ws_manager import router as ws_router

app = FastAPI(title="Pokemon Rivalry")
app.include_router(page_router)
app.include_router(login, prefix="/auth")
app.include_router(team_router)
app.include_router(battle_router)
app.include_router(ws_router)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.mount("/static", StaticFiles(directory="./src/view/"), name="view")
