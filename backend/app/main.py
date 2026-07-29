import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import signals, pairs, backtest, news
from app.api import ws as ws_router
from app.api import auth as auth_router
from app.config import settings
from app.services.price_streamer import stream_loop
from app.services.scheduler import start_scheduler
from app.services.auth import init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    price_task = asyncio.create_task(stream_loop())
    scheduler_task = asyncio.create_task(start_scheduler())
    logger.info("Background tasks started")
    yield
    price_task.cancel()
    scheduler_task.cancel()


app = FastAPI(
    title="FX Signal AI",
    description="中期FX通貨ペア売買タイミング通知API",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(signals.router, prefix="/api/v1")
app.include_router(pairs.router, prefix="/api/v1")
app.include_router(backtest.router, prefix="/api/v1")
app.include_router(news.router, prefix="/api/v1")
app.include_router(ws_router.router)
app.include_router(auth_router.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "app": settings.app_name,
        "version": "2.0.0",
        "docs": "/docs",
        "pairs": settings.fx_pairs,
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
