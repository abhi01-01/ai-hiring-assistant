import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from api.core.config import settings
from api.core.database import Base, engine, wait_for_database
from api.core.migrations import run_compatible_migrations
from api.repositories import models  # noqa: F401 - register SQLAlchemy models
from api.routers import candidates, search, webhooks

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    wait_for_database()

    if settings.DB_AUTO_MIGRATE:
        run_compatible_migrations()
    elif settings.DB_AUTO_CREATE:
        Base.metadata.create_all(bind=engine)

    timeout = httpx.Timeout(20.0, connect=5.0)
    app.state.http_client = httpx.AsyncClient(timeout=timeout)
    try:
        yield
    finally:
        await app.state.http_client.aclose()
        engine.dispose()


app = FastAPI(title=settings.APP_NAME, version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Hunar-Signature"],
)


@app.get("/api/health")
def health_check():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ok", "environment": settings.ENVIRONMENT}


app.include_router(candidates.router, prefix="/api")
app.include_router(webhooks.router, prefix="/api")
app.include_router(search.router, prefix="/api")
