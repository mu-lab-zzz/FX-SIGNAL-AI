from fastapi import APIRouter
from app.services.news_analyzer import get_recent_news
from app.services.fundamental_analysis import get_interest_rate_data

router = APIRouter(prefix="/news", tags=["news"])


@router.get("/recent")
async def get_news():
    """Return recent FX-relevant news with AI classification."""
    return {"items": get_recent_news(limit=20)}


@router.get("/rates")
async def get_interest_rates():
    """Return current central bank interest rates."""
    return {"rates": get_interest_rate_data()}
