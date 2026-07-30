from fastapi import APIRouter, Query
from app.services.news_fetcher import fetch_live_news
from app.services.fundamental_analysis import get_interest_rate_data
from app.services.economic_calendar import fetch_events

router = APIRouter(prefix="/news", tags=["news"])


@router.get("/recent")
async def get_news(limit: int = Query(20, ge=1, le=50)):
    """Return recent FX-relevant news (live via NewsAPI, fallback to demo)."""
    items = await fetch_live_news(limit=limit)
    return {"items": items}


@router.get("/rates")
async def get_interest_rates():
    """Return current central bank interest rates."""
    return {"rates": get_interest_rate_data()}


@router.get("/calendar")
async def get_calendar():
    """Return upcoming/recent high-impact economic events."""
    events = await fetch_events()
    return {"events": events}
