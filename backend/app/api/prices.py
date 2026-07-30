from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List
from datetime import datetime

from app.config import settings
from app.services.data_fetcher import price_fetcher

router = APIRouter(prefix="/prices", tags=["prices"])


class OhlcvBar(BaseModel):
    t: str      # ISO timestamp
    o: float
    h: float
    l: float
    c: float
    v: float


class OhlcvResponse(BaseModel):
    pair: str
    timeframe: str
    bars: List[OhlcvBar]


@router.get("/{pair:path}", response_model=OhlcvResponse)
async def get_ohlcv(
    pair: str,
    timeframe: str = Query("D", description="D | H4 | H1"),
    count: int = Query(120, ge=30, le=500),
):
    pair = pair.upper().replace("-", "/")
    if pair not in settings.fx_pairs:
        raise HTTPException(404, f"Pair {pair} not supported")

    df = await price_fetcher.fetch_ohlcv(pair, timeframe=timeframe, count=count)

    bars = [
        OhlcvBar(
            t=str(idx),
            o=round(float(row["open"]),  6),
            h=round(float(row["high"]),  6),
            l=round(float(row["low"]),   6),
            c=round(float(row["close"]), 6),
            v=round(float(row["volume"]), 2),
        )
        for idx, row in df.iterrows()
    ]
    return OhlcvResponse(pair=pair, timeframe=timeframe, bars=bars)
