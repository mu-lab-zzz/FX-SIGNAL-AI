"""
Currency Strength Map.

For each currency, aggregate its performance vs. all other major currencies
to derive a relative strength score (-100 to +100) and star rating (1-5).
"""

from __future__ import annotations
import asyncio
from typing import Optional
import pandas as pd

from app.config import settings
from app.models.currency import CurrencyStrength, CurrencyStrengthMap
from app.services.data_fetcher import price_fetcher
from app.services.fundamental_analysis import CB_STANCE, INTEREST_RATES


def _score_to_stars(score: float) -> int:
    if score >= 60:
        return 5
    elif score >= 30:
        return 4
    elif score >= 0:
        return 3
    elif score >= -30:
        return 2
    return 1


def _score_to_trend(current: float, prev: float) -> str:
    diff = current - prev
    if diff > 5:
        return "rising"
    elif diff < -5:
        return "falling"
    return "stable"


async def compute_currency_strength(currencies: Optional[list[str]] = None) -> CurrencyStrengthMap:
    """
    Compute per-currency strength by averaging:
      - Interest rate advantage (50%)
      - CB stance (30%)
      - 5-day price momentum vs basket (20%)
    """
    if currencies is None:
        currencies = settings.currencies

    # Fetch price data for all major pairs to get momentum
    pairs_to_fetch = []
    for base in currencies:
        for quote in currencies:
            if base != quote:
                pairs_to_fetch.append(f"{base}/{quote}")

    # Compute momentum from available pairs (use canonical pairs only)
    canonical_pairs = [
        ("USD", "JPY"), ("EUR", "USD"), ("GBP", "USD"),
        ("AUD", "USD"), ("EUR", "JPY"), ("AUD", "JPY"),
        ("NZD", "JPY"), ("GBP", "JPY"), ("USD", "CHF"),
        ("EUR", "GBP"), ("NZD", "USD"),
    ]

    momentum: dict[str, list[float]] = {c: [] for c in currencies}

    for base, quote in canonical_pairs:
        if base not in currencies or quote not in currencies:
            continue
        try:
            df = await price_fetcher.fetch_ohlcv(f"{base}/{quote}", count=10)
            if len(df) >= 6:
                ret_5d = (df["close"].iloc[-1] / df["close"].iloc[-6] - 1) * 100
                momentum[base].append(ret_5d)
                momentum[quote].append(-ret_5d)
        except Exception:
            pass

    avg_momentum: dict[str, float] = {
        c: (sum(v) / len(v) if v else 0.0)
        for c, v in momentum.items()
    }

    # Max interest rate for normalisation
    max_rate = max(INTEREST_RATES.values()) or 1.0
    max_stance = 1.0  # CB_STANCE range is -1..+1

    strengths = []
    for ccy in currencies:
        rate = INTEREST_RATES.get(ccy, 0.0)
        stance = CB_STANCE.get(ccy, 0.0)
        mom = avg_momentum.get(ccy, 0.0)

        # Normalise to -100..+100
        rate_norm = (rate / max_rate) * 100 - 50     # high rate → positive
        stance_norm = stance * 100                     # -100..+100
        mom_norm = max(-100, min(100, mom * 10))       # 1% move → 10 pts

        score = (
            0.50 * rate_norm +
            0.30 * stance_norm +
            0.20 * mom_norm
        )

        strengths.append(
            CurrencyStrength(
                currency=ccy,
                score=round(score, 2),
                stars=_score_to_stars(score),
                trend="rising" if mom > 0.1 else ("falling" if mom < -0.1 else "stable"),
                vs_pairs={},
            )
        )

    # Sort strongest first
    strengths.sort(key=lambda x: x.score, reverse=True)

    from datetime import datetime
    return CurrencyStrengthMap(
        generated_at=datetime.utcnow().isoformat() + "Z",
        strengths=strengths,
    )
