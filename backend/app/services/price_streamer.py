"""
WebSocket price streamer.
Broadcasts live OHLCV + signal scores to all connected clients every N seconds.
"""

from __future__ import annotations
import asyncio
import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import WebSocket

from app.config import settings
from app.services.data_fetcher import price_fetcher
from app.services.technical_analysis import compute_technical_score
from app.services.fundamental_analysis import compute_fundamental_score
from app.services.scoring_engine import build_signal

logger = logging.getLogger(__name__)

REFRESH_INTERVAL = 30  # seconds between price refreshes


class ConnectionManager:
    def __init__(self):
        self._active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self._active.append(ws)
        logger.info("WS connect  total=%d", len(self._active))

    def disconnect(self, ws: WebSocket):
        self._active.remove(ws)
        logger.info("WS disconnect total=%d", len(self._active))

    async def broadcast(self, payload: dict):
        dead = []
        text = json.dumps(payload, default=str)
        for ws in self._active:
            try:
                await ws.send_text(text)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._active.remove(ws)

    @property
    def count(self) -> int:
        return len(self._active)


manager = ConnectionManager()


async def _build_tick(pair: str) -> Optional[dict]:
    try:
        df = await price_fetcher.fetch_ohlcv(pair, count=300)
        if len(df) < 50:
            return None
        tech = compute_technical_score(df)
        fund = compute_fundamental_score(pair)
        price = float(df["close"].iloc[-1])
        prev  = float(df["close"].iloc[-2])
        signal = build_signal(pair, price, tech, fund)
        return {
            "type": "tick",
            "pair": pair,
            "price": price,
            "change_pct": round((price / prev - 1) * 100, 4),
            "score": signal.total_score,
            "direction": signal.direction.value,
            "strength": signal.strength.value,
            "ts": datetime.utcnow().isoformat() + "Z",
        }
    except Exception as e:
        logger.warning("tick error %s: %s", pair, e)
        return None


async def stream_loop():
    """Background task: push ticks to all connected WebSocket clients."""
    from app.services.alert_engine import alert_engine
    while True:
        ticks = []
        for pair in settings.fx_pairs:
            tick = await _build_tick(pair)
            if tick:
                ticks.append(tick)

        if ticks:
            if manager.count > 0:
                await manager.broadcast({"type": "batch", "ticks": ticks})
            await alert_engine.evaluate(ticks)

        await asyncio.sleep(REFRESH_INTERVAL)
