from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.price_streamer import manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/prices")
async def prices_ws(websocket: WebSocket):
    """
    WebSocket endpoint.
    Client receives JSON: { type: "batch", ticks: [ { pair, price, change_pct, score, ... } ] }
    """
    await manager.connect(websocket)
    try:
        while True:
            # Keep alive — client can send pings
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
