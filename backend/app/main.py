from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import signals, pairs, backtest, news
from app.config import settings

app = FastAPI(
    title="FX Signal AI",
    description="中期FX通貨ペア売買タイミング通知API",
    version="1.0.0",
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


@app.get("/")
async def root():
    return {
        "app": settings.app_name,
        "version": "1.0.0",
        "docs": "/docs",
        "pairs": settings.fx_pairs,
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
