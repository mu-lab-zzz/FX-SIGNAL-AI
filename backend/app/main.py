import asyncio
import logging
import time
from contextlib import asynccontextmanager
from collections import defaultdict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.api import signals, pairs, backtest, news, prices
from app.api import ws as ws_router
from app.api import auth as auth_router
from app.config import settings
from app.services.price_streamer import stream_loop
from app.services.scheduler import start_scheduler
from app.services.auth import init_db

logger = logging.getLogger(__name__)

_DEFAULT_JWT_SECRET = "change-me-in-production"


def _check_jwt_secret() -> None:
    if settings.jwt_secret == _DEFAULT_JWT_SECRET:
        logger.warning(
            "JWT_SECRET is set to the default value. "
            "Set a strong secret in your .env file before deploying to production."
        )


# ── Simple in-memory rate limiter ────────────────────────────────────────────
_rate_buckets: dict[str, list[float]] = defaultdict(list)

RATE_LIMIT_REQUESTS = 60   # requests per window
RATE_LIMIT_WINDOW   = 60   # seconds

RATE_LIMITED_PATHS = {"/api/v1/signals", "/api/v1/pairs/ranking", "/api/v1/backtest"}


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if not any(path.startswith(p) for p in RATE_LIMITED_PATHS):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        bucket = _rate_buckets[client_ip]

        # Evict timestamps outside the window
        cutoff = now - RATE_LIMIT_WINDOW
        _rate_buckets[client_ip] = [t for t in bucket if t > cutoff]

        if len(_rate_buckets[client_ip]) >= RATE_LIMIT_REQUESTS:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please slow down."},
                headers={"Retry-After": str(RATE_LIMIT_WINDOW)},
            )

        _rate_buckets[client_ip].append(now)
        return await call_next(request)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _check_jwt_secret()
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

# ── CORS ─────────────────────────────────────────────────────────────────────
_cors_origins = (
    ["*"]
    if settings.cors_origins.strip() == "*"
    else [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=_cors_origins != ["*"],
)

app.add_middleware(RateLimitMiddleware)

app.include_router(signals.router, prefix="/api/v1")
app.include_router(pairs.router, prefix="/api/v1")
app.include_router(backtest.router, prefix="/api/v1")
app.include_router(news.router, prefix="/api/v1")
app.include_router(prices.router, prefix="/api/v1")
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
