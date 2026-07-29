"""
Central bank statement analyzer.
Uses Gemini to classify recent CB statements as hawkish/dovish/neutral
and updates the in-memory CB stance cache used by fundamental_analysis.py.
"""

from __future__ import annotations
import json
import logging
import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# ── Demo statements (refreshed by scheduler via real news feed) ────────────────
DEMO_STATEMENTS: list[dict] = [
    {"bank": "FRB",  "currency": "USD",
     "text": "Inflation remains elevated. We are prepared to raise rates further if appropriate. The labor market is extremely tight."},
    {"bank": "日銀",  "currency": "JPY",
     "text": "We will maintain ultra-loose monetary policy. We see no need to raise rates at this time. YCC will continue."},
    {"bank": "ECB",  "currency": "EUR",
     "text": "Interest rates are at levels that are making a substantial contribution to the timely return of inflation to target."},
    {"bank": "BOE",  "currency": "GBP",
     "text": "Policy needs to remain restrictive for an extended period. We continue to monitor inflation persistence carefully."},
    {"bank": "RBA",  "currency": "AUD",
     "text": "Some further tightening of monetary policy may be required. We are data-dependent."},
]

_GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

# In-memory cache: { "USD": 0.5, "JPY": -0.8, ... }
_stance_cache: dict[str, float] = {}


async def analyze_cb_statements(statements: list[dict] | None = None) -> dict[str, float]:
    """
    For each CB statement, call Gemini to score -1 (dovish) to +1 (hawkish).
    Updates and returns the stance cache.
    Falls back to static values when Gemini is unavailable.
    """
    stmts = statements or DEMO_STATEMENTS

    if not settings.gemini_api_key:
        return _static_fallback()

    results: dict[str, float] = {}
    async with httpx.AsyncClient(timeout=15.0) as client:
        for stmt in stmts:
            score = await _score_statement(client, stmt["text"])
            results[stmt["currency"]] = score
            logger.info("CB stance %s (%s): %.2f", stmt["bank"], stmt["currency"], score)

    _stance_cache.update(results)
    return results


async def _score_statement(client: httpx.AsyncClient, text: str) -> float:
    prompt = (
        "You are an expert central bank analyst. "
        "Score the following central bank statement from -1.0 (very dovish) to +1.0 (very hawkish). "
        "Return ONLY a single float number between -1.0 and 1.0.\n\n"
        f"Statement: {text}"
    )
    url = f"{_GEMINI_BASE}/{settings.gemini_model}:generateContent?key={settings.gemini_api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 16, "temperature": 0.0},
    }
    try:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        return max(-1.0, min(1.0, float(raw)))
    except Exception as e:
        logger.warning("Gemini CB score failed: %s", e)
        return 0.0


def _static_fallback() -> dict[str, float]:
    from app.services.fundamental_analysis import CB_STANCE
    return dict(CB_STANCE)


def get_cached_stance() -> dict[str, float]:
    if not _stance_cache:
        return _static_fallback()
    return dict(_stance_cache)
