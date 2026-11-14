from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import chat
from app.redis_client import r


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Each module's startup/shutdown nests here. Add more `async with` lines as modules need them.
    async with chat.lifespan(app):
        yield
    await r.aclose()    # shared client, so it's closed here rather than inside a module


app = FastAPI(lifespan=lifespan)
app.include_router(chat.router)
# app.include_router(auth.router)
# app.include_router(profiles.router)
# app.include_router(discovery.router)
# app.include_router(swipes.router)
# app.include_router(safety.router)
