"""
Real news fetcher using NewsAPI.org (free tier: 100 req/day).
Falls back to demo data when API key is absent.
"""

from __future__ import annotations
import httpx
import logging
from datetime import datetime, timedelta
from app.config import settings

logger = logging.getLogger(__name__)

# FX-relevant keywords for filtering
FX_KEYWORDS = (
    "central bank OR interest rate OR inflation OR GDP OR CPI OR "
    "employment OR Fed OR ECB OR BOJ OR RBA OR RBNZ OR BOE OR "
    "forex OR currency OR dollar OR yen OR euro OR sterling"
)

_cache: list[dict] = []
_cache_at: datetime | None = None
CACHE_TTL_MIN = 30


async def fetch_live_news(limit: int = 10) -> list[dict]:
    """Fetch and return normalized news items."""
    global _cache, _cache_at

    if _cache and _cache_at and (datetime.utcnow() - _cache_at).seconds < CACHE_TTL_MIN * 60:
        return _cache[:limit]

    if not settings.newsapi_key:
        from app.services.news_analyzer import DEMO_NEWS
        return DEMO_NEWS[:limit]

    try:
        result = await _fetch_newsapi(limit)
        _cache = result
        _cache_at = datetime.utcnow()
        return result
    except Exception as e:
        logger.warning("NewsAPI fetch failed: %s", e)
        from app.services.news_analyzer import DEMO_NEWS
        return DEMO_NEWS[:limit]


async def _fetch_newsapi(limit: int) -> list[dict]:
    from_date = (datetime.utcnow() - timedelta(days=2)).strftime("%Y-%m-%d")
    params = {
        "q": FX_KEYWORDS,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": min(limit, 20),
        "from": from_date,
        "apiKey": settings.newsapi_key,
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get("https://newsapi.org/v2/everything", params=params)
        resp.raise_for_status()
        data = resp.json()

    items = []
    for art in data.get("articles", []):
        title = art.get("title", "")
        if not title or title == "[Removed]":
            continue
        items.append({
            "headline": title,
            "source": art.get("source", {}).get("name", ""),
            "published": art.get("publishedAt", ""),
            "url": art.get("url", ""),
            "currency_impact": {},   # filled by Gemini analysis
            "classification": "pending",
            "summary": art.get("description", "") or title,
        })
    return items
