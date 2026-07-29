"""
Alert engine — detects high-score signals and queues push notifications.
Subscribers register via /api/v1/alerts/subscribe endpoint.
"""

from __future__ import annotations
import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Awaitable

from app.config import settings

logger = logging.getLogger(__name__)

AlertCallback = Callable[[dict], Awaitable[None]]


@dataclass
class AlertSubscriber:
    id: str
    callback: AlertCallback
    pairs: list[str] = field(default_factory=list)   # empty = all pairs
    min_score: float = 80.0


class AlertEngine:
    def __init__(self):
        self._subscribers: dict[str, AlertSubscriber] = {}
        self._sent_this_session: set[str] = set()  # deduplicate within session

    def subscribe(self, sub: AlertSubscriber):
        self._subscribers[sub.id] = sub
        logger.info("Alert subscribe id=%s pairs=%s", sub.id, sub.pairs or "all")

    def unsubscribe(self, sub_id: str):
        self._subscribers.pop(sub_id, None)

    async def evaluate(self, ticks: list[dict]):
        """Called by stream_loop after each price refresh batch."""
        for tick in ticks:
            score = tick.get("score", 0)
            pair  = tick.get("pair", "")
            direction = tick.get("direction", "")
            key = f"{pair}:{direction}:{int(score // 5) * 5}"  # bucket to 5-pt granularity

            if key in self._sent_this_session:
                continue

            for sub in self._subscribers.values():
                if sub.pairs and pair not in sub.pairs:
                    continue
                if score >= sub.min_score:
                    alert = {
                        "type": "alert",
                        "pair": pair,
                        "score": score,
                        "direction": direction,
                        "strength": tick.get("strength"),
                        "price": tick.get("price"),
                        "ts": datetime.utcnow().isoformat() + "Z",
                        "message": (
                            f"{pair}  スコア {score:.0f}/100  "
                            f"{'🟢 強い買い候補' if direction == 'BUY' else '🔴 強い売り候補'}"
                        ),
                    }
                    try:
                        await sub.callback(alert)
                        self._sent_this_session.add(key)
                    except Exception as e:
                        logger.warning("Alert callback error: %s", e)


alert_engine = AlertEngine()
