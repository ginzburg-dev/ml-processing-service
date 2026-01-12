from backend.app.config import MLServiceConfig

from backend.app.routers.denoise import router as router_denoise
from backend.app.routers.auth import router as router_auth

from fastapi import FastAPI, Depends
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()

config = MLServiceConfig(dotenv=True)

app.add_middleware(
    SessionMiddleware,
    secret_key = config.session_secret,
    same_site="lax",
    https_only=False,
    max_age=None,
)

app.include_router(router=router_denoise)
app.include_router(router=router_auth)

@app.get("/")
async def root():
    return {"message": "ML Processing Service"}

@app.get("/health")
async def health():
    return {"ok": True}
