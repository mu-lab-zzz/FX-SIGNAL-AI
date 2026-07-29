"""
AI-powered news/CB-statement analyzer using Claude.
Classifies impact on each currency: -3 (very bearish) to +3 (very bullish).
"""

from __future__ import annotations
import json
from typing import Optional
import anthropic

from app.config import settings


DEMO_NEWS = [
    {
        "headline": "Fed Chair Powell: Rate cuts not imminent, inflation remains concern",
        "source": "Reuters",
        "published": "2024-01-15T14:00:00Z",
        "currency_impact": {"USD": 2, "JPY": -1, "EUR": -1},
        "classification": "hawkish_usd",
        "summary": "FRB議長: 利下げは時期尚早、インフレ注視継続",
    },
    {
        "headline": "BOJ Governor Ueda: Ultra-loose policy to continue, no urgency to hike",
        "source": "Bloomberg",
        "published": "2024-01-14T09:00:00Z",
        "currency_impact": {"JPY": -2, "USD": 1},
        "classification": "dovish_jpy",
        "summary": "日銀・植田総裁: 超緩和維持、利上げ急がず",
    },
    {
        "headline": "US Non-Farm Payrolls beat forecasts: +256K vs +160K expected",
        "source": "BLS",
        "published": "2024-01-12T13:30:00Z",
        "currency_impact": {"USD": 3, "JPY": -2, "EUR": -1, "AUD": -1},
        "classification": "bullish_usd",
        "summary": "米雇用統計：予想大幅上振れ、ドル強含み",
    },
    {
        "headline": "ECB holds rates, signals possible June cut amid slowing growth",
        "source": "ECB",
        "published": "2024-01-11T12:45:00Z",
        "currency_impact": {"EUR": -2, "USD": 1, "GBP": 0},
        "classification": "dovish_eur",
        "summary": "ECB金利据え置き、6月利下げ示唆でユーロ下落",
    },
]


async def analyze_news_impact(headlines: list[str], currencies: list[str]) -> dict:
    """
    Call Claude to classify currency impact of news headlines.
    Returns dict: { currency: score (-3 to +3) }
    Falls back to demo data when API key is absent.
    """
    if not settings.anthropic_api_key:
        return _demo_impact(currencies)

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    prompt = (
        "You are an expert FX analyst. Given these news headlines, "
        "score the impact on each currency from -3 (very bearish) to +3 (very bullish). "
        "Return ONLY a JSON object with currency codes as keys.\n\n"
        f"Headlines:\n{chr(10).join(f'- {h}' for h in headlines)}\n\n"
        f"Currencies to score: {', '.join(currencies)}\n\n"
        "Return ONLY valid JSON. Example: {\"USD\": 2, \"JPY\": -1}"
    )

    message = await client.messages.create(
        model="claude-sonnet-5",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )
    text = message.content[0].text.strip()
    # Extract JSON from response
    start = text.find("{")
    end = text.rfind("}") + 1
    return json.loads(text[start:end])


def get_recent_news(limit: int = 10) -> list[dict]:
    """Return recent news items (demo). Replace with live news API."""
    return DEMO_NEWS[:limit]


def _demo_impact(currencies: list[str]) -> dict:
    """Aggregate demo news impact scores."""
    totals: dict[str, float] = {c: 0.0 for c in currencies}
    for item in DEMO_NEWS:
        for ccy, score in item.get("currency_impact", {}).items():
            if ccy in totals:
                totals[ccy] += score
    return totals


def news_score_to_fundamental_adjustment(impact: dict[str, float], base: str, quote: str) -> float:
    """Convert raw impact scores to a -3..+3 fundamental adjustment for the pair."""
    base_impact = impact.get(base, 0.0)
    quote_impact = impact.get(quote, 0.0)
    return max(-3.0, min(3.0, base_impact - quote_impact))
