"""
Economic calendar service.
Fetches upcoming/recent high-impact events and computes per-currency
economic surprise scores used by fundamental_analysis.py.

Live source: Trading Economics API (optional).
Fallback: curated demo data updated here.
"""

from __future__ import annotations
import httpx
from datetime import datetime, timedelta
from app.config import settings


# ── Demo events (replace with live fetch) ─────────────────────────────────────
DEMO_EVENTS: list[dict] = [
    {"name": "Non-Farm Payrolls",   "currency": "USD", "impact": "high",
     "actual": 256.0, "forecast": 160.0, "previous": 199.0,
     "scheduled_at": "2024-01-12T13:30:00Z"},
    {"name": "CPI (YoY)",           "currency": "USD", "impact": "high",
     "actual": 3.4,  "forecast": 3.2,   "previous": 3.1,
     "scheduled_at": "2024-01-11T13:30:00Z"},
    {"name": "GDP (QoQ)",           "currency": "EUR", "impact": "high",
     "actual": 0.1,  "forecast": 0.2,   "previous": 0.1,
     "scheduled_at": "2024-01-10T10:00:00Z"},
    {"name": "BOJ Rate Decision",   "currency": "JPY", "impact": "high",
     "actual": 0.1,  "forecast": 0.1,   "previous": 0.1,
     "scheduled_at": "2024-01-23T03:00:00Z"},
    {"name": "CPI (YoY)",           "currency": "GBP", "impact": "high",
     "actual": 3.9,  "forecast": 3.8,   "previous": 4.6,
     "scheduled_at": "2024-01-17T07:00:00Z"},
    {"name": "Employment Change",   "currency": "AUD", "impact": "high",
     "actual": -65.1,"forecast": 17.6,  "previous": 61.5,
     "scheduled_at": "2024-01-18T00:30:00Z"},
    {"name": "PMI Manufacturing",   "currency": "USD", "impact": "medium",
     "actual": 50.3, "forecast": 49.5,  "previous": 49.4,
     "scheduled_at": "2024-01-16T14:45:00Z"},
    {"name": "Retail Sales (MoM)",  "currency": "USD", "impact": "high",
     "actual": 0.6,  "forecast": 0.4,   "previous": 0.3,
     "scheduled_at": "2024-01-17T13:30:00Z"},
]


async def fetch_events(days_back: int = 7, days_forward: int = 3) -> list[dict]:
    """
    Return economic events. Tries Trading Economics API first, falls back to demo.
    """
    if settings.trading_economics_api_key:
        try:
            return await _fetch_trading_economics(days_back, days_forward)
        except Exception:
            pass
    return DEMO_EVENTS


async def _fetch_trading_economics(days_back: int, days_forward: int) -> list[dict]:
    now = datetime.utcnow()
    start = (now - timedelta(days=days_back)).strftime("%Y-%m-%d")
    end   = (now + timedelta(days=days_forward)).strftime("%Y-%m-%d")
    url = (
        f"https://api.tradingeconomics.com/calendar"
        f"?c={settings.trading_economics_api_key}"
        f"&d1={start}&d2={end}&importance=2,3"
    )
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        raw = resp.json()

    events = []
    for item in raw:
        actual   = item.get("Actual")
        forecast = item.get("Forecast")
        previous = item.get("Previous")
        events.append({
            "name": item.get("Event", ""),
            "currency": item.get("Currency", ""),
            "impact": "high" if item.get("Importance") == 3 else "medium",
            "actual":   float(actual)   if actual   is not None else None,
            "forecast": float(forecast) if forecast is not None else None,
            "previous": float(previous) if previous is not None else None,
            "scheduled_at": item.get("Date", ""),
        })
    return events


def compute_surprise_scores(events: list[dict]) -> dict[str, float]:
    """
    Aggregate economic surprise index per currency.
    surprise = (actual - forecast) / abs(previous or 1)
    Range clipped to -1..+1 per event, averaged per currency.
    """
    buckets: dict[str, list[float]] = {}
    for ev in events:
        ccy     = ev.get("currency", "")
        actual  = ev.get("actual")
        forecast = ev.get("forecast")
        if actual is None or forecast is None:
            continue
        previous = ev.get("previous") or 1.0
        norm = abs(previous) if abs(previous) > 0.001 else 1.0
        surprise = max(-1.0, min(1.0, (actual - forecast) / norm))
        buckets.setdefault(ccy, []).append(surprise)

    return {
        ccy: round(sum(v) / len(v), 4)
        for ccy, v in buckets.items()
        if v
    }
