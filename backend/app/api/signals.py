from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.config import settings
from app.models.signal import FXSignal, ExitSignal
from app.services.data_fetcher import price_fetcher
from app.services.technical_analysis import compute_technical_score
from app.services.fundamental_analysis import compute_fundamental_score
from app.services.news_analyzer import (
    get_recent_news,
    analyze_news_impact,
    news_score_to_fundamental_adjustment,
)
from app.services.scoring_engine import build_signal, check_exit_signal

router = APIRouter(prefix="/signals", tags=["signals"])


@router.get("/{pair:path}", response_model=FXSignal)
async def get_signal(pair: str, timeframe: str = Query("D", description="D | H4 | H1")):
    """Compute and return a full FX signal for a currency pair."""
    pair = pair.upper().replace("-", "/")
    if pair not in settings.fx_pairs:
        raise HTTPException(404, f"Pair {pair} not supported. Supported: {settings.fx_pairs}")

    df = await price_fetcher.fetch_ohlcv(pair, timeframe=timeframe, count=300)
    if len(df) < 50:
        raise HTTPException(422, "Insufficient price data")

    technical = compute_technical_score(df)
    fundamental = compute_fundamental_score(pair)

    # News impact
    news_items = get_recent_news(limit=5)
    headlines = [n["headline"] for n in news_items]
    base, quote = pair.split("/")
    impact = await analyze_news_impact(headlines, [base, quote])
    news_adj = news_score_to_fundamental_adjustment(impact, base, quote)

    current_price = float(df["close"].iloc[-1])
    signal = build_signal(pair, current_price, technical, fundamental, news_adj)
    return signal


@router.get("/{pair:path}/exit", response_model=ExitSignal)
async def get_exit_signal(
    pair: str,
    direction: str = Query(..., description="BUY or SELL"),
):
    """Check whether an open position should be closed."""
    pair = pair.upper().replace("-", "/")
    df = await price_fetcher.fetch_ohlcv(pair, count=300)
    technical = compute_technical_score(df)
    fundamental = compute_fundamental_score(pair)
    return check_exit_signal(pair, direction, technical, fundamental)
