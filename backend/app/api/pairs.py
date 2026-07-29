from fastapi import APIRouter
from datetime import datetime

from app.config import settings
from app.models.signal import PairRanking, RankingResponse, SignalDirection, SignalStrength
from app.models.currency import CurrencyStrengthMap
from app.services.data_fetcher import price_fetcher
from app.services.technical_analysis import compute_technical_score
from app.services.fundamental_analysis import compute_fundamental_score
from app.services.news_analyzer import get_recent_news
from app.services.currency_strength import compute_currency_strength
from app.services.scoring_engine import build_signal

router = APIRouter(prefix="/pairs", tags=["pairs"])


@router.get("/ranking", response_model=RankingResponse)
async def get_ranking():
    """
    Compute and rank all configured FX pairs by total score.
    Returns morning-brief style ranking.
    """
    rankings: list[PairRanking] = []

    for pair in settings.fx_pairs:
        try:
            df = await price_fetcher.fetch_ohlcv(pair, count=300)
            if len(df) < 50:
                continue

            technical = compute_technical_score(df)
            fundamental = compute_fundamental_score(pair)
            current_price = float(df["close"].iloc[-1])
            prev_price = float(df["close"].iloc[-2]) if len(df) >= 2 else current_price
            change_24h = round((current_price / prev_price - 1) * 100, 4)

            signal = build_signal(pair, current_price, technical, fundamental)
            rankings.append(
                PairRanking(
                    rank=0,  # filled below
                    pair=pair,
                    score=signal.total_score,
                    direction=signal.direction,
                    strength=signal.strength,
                    change_24h=change_24h,
                    summary=signal.summary,
                )
            )
        except Exception as e:
            # Skip pair on error (don't crash the whole ranking)
            continue

    # Sort by score desc, assign ranks
    rankings.sort(key=lambda r: r.score, reverse=True)
    for i, r in enumerate(rankings):
        r.rank = i + 1

    return RankingResponse(generated_at=datetime.utcnow(), rankings=rankings)


@router.get("/strength", response_model=CurrencyStrengthMap)
async def get_currency_strength():
    """Return the currency strength map for all major currencies."""
    return await compute_currency_strength()
