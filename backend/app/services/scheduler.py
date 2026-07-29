"""
Background scheduler — runs periodic jobs:
  - Every 1h  : refresh economic surprise scores
  - Every 6h  : refresh CB stance via Gemini
  - Every 30s : handled by price_streamer.stream_loop (not here)
"""

from __future__ import annotations
import asyncio
import logging
from datetime import datetime

from app.services.economic_calendar import fetch_events, compute_surprise_scores
from app.services.cb_analyzer import analyze_cb_statements
from app.services import fundamental_analysis as fa

logger = logging.getLogger(__name__)


async def _refresh_economic_data():
    try:
        events = await fetch_events()
        scores = compute_surprise_scores(events)
        fa.ECON_SURPRISE.update(scores)
        logger.info("Economic surprise updated: %s", scores)
    except Exception as e:
        logger.warning("Economic refresh failed: %s", e)


async def _refresh_cb_stance():
    try:
        stances = await analyze_cb_statements()
        fa.CB_STANCE.update(stances)
        logger.info("CB stance updated: %s", stances)
    except Exception as e:
        logger.warning("CB stance refresh failed: %s", e)


async def start_scheduler():
    """Long-running coroutine that fires periodic refresh jobs."""
    # Initial run on startup
    await _refresh_economic_data()
    await _refresh_cb_stance()

    tick = 0
    while True:
        await asyncio.sleep(3600)   # every hour
        tick += 1
        await _refresh_economic_data()
        if tick % 6 == 0:           # every 6 hours
            await _refresh_cb_stance()
