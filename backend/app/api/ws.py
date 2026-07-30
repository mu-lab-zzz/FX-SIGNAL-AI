"""
WebSocket endpoint.
- Price ticks : broadcast to all connected clients
- Alerts      : sent only to the authenticated user whose threshold is met
"""

import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional

from app.services.price_streamer import manager
from app.services.alert_engine import alert_engine, AlertSubscriber
from app.services.auth import decode_token, get_user_by_id

logger = logging.getLogger(__name__)
router = APIRouter(tags=["websocket"])


@router.websocket("/ws/prices")
async def prices_ws(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
):
    """
    Connect with optional ?token=<jwt> to enable per-user alerts.
    Without a token: price ticks only.
    With a valid token: price ticks + personal alerts based on saved settings.
    """
    await manager.connect(websocket)

    sub_id: Optional[str] = None

    # ── Resolve user from token and register with alert engine ────────────────
    if token:
        payload = decode_token(token)
        if payload:
            user_id = payload.get("sub")
            user = await get_user_by_id(int(user_id)) if user_id else None
            if user:
                import json as _json
                pairs = _json.loads(user.get("alert_pairs") or "[]")
                min_score = float(user.get("alert_min_score", 80.0))
                sub_id = f"ws_{user_id}"

                async def _send_alert(alert: dict):
                    try:
                        await websocket.send_text(json.dumps(alert, default=str))
                    except Exception:
                        pass

                alert_engine.subscribe(
                    AlertSubscriber(
                        id=sub_id,
                        callback=_send_alert,
                        pairs=pairs,
                        min_score=min_score,
                    )
                )
                logger.info("WS user %s subscribed alerts pairs=%s score>=%s",
                            user_id, pairs or "all", min_score)

    # ── Keep alive loop ───────────────────────────────────────────────────────
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)
        if sub_id:
            alert_engine.unsubscribe(sub_id)
