"""
Currency-specific fundamental scoring (max 40 pts).

① Interest rate differential : 0-15 pts
② Central bank stance        : 0-10 pts
③ Economic indicators        : 0-10 pts
④ Risk environment           : 0-5  pts
"""

from __future__ import annotations
from typing import Optional
import httpx

from app.config import settings
from app.models.signal import FundamentalScoreDetail
from app.models.currency import InterestRateData, CentralBankStance


# ── Static reference data (updated manually / via admin API) ──────────────────

INTEREST_RATES: dict[str, float] = {
    "USD": 5.50,   # Fed Funds upper bound
    "JPY": 0.10,   # BOJ target
    "EUR": 4.50,   # ECB deposit rate
    "GBP": 5.25,   # BOE bank rate
    "AUD": 4.35,   # RBA cash rate
    "NZD": 5.50,   # RBNZ OCR
    "CHF": 1.75,   # SNB policy rate
    "CAD": 5.00,   # BOC overnight rate
}

# Stance: +1 hawkish, 0 neutral, -1 dovish
CB_STANCE: dict[str, float] = {
    "USD": 0.5,    # FRB: higher-for-longer rhetoric
    "JPY": -0.8,   # BOJ: ultra-dovish
    "EUR": 0.2,
    "GBP": 0.3,
    "AUD": 0.0,
    "NZD": 0.3,
    "CHF": -0.3,
    "CAD": 0.0,
}

CB_NAMES: dict[str, str] = {
    "USD": "FRB (連邦準備制度)",
    "JPY": "日本銀行 (BOJ)",
    "EUR": "欧州中央銀行 (ECB)",
    "GBP": "イングランド銀行 (BOE)",
    "AUD": "豪州準備銀行 (RBA)",
    "NZD": "ニュージーランド準備銀行 (RBNZ)",
    "CHF": "スイス国立銀行 (SNB)",
    "CAD": "カナダ銀行 (BOC)",
}

# Recent economic surprise composite (base → refreshed from calendar API)
ECON_SURPRISE: dict[str, float] = {
    "USD": 0.4,    # -1 to +1
    "JPY": -0.2,
    "EUR": 0.1,
    "GBP": 0.2,
    "AUD": -0.1,
    "NZD": -0.2,
    "CHF": 0.0,
    "CAD": 0.1,
}


def _interest_rate_score(base: str, quote: str) -> tuple[float, str]:
    """Score interest rate differential. Positive = base currency advantaged."""
    r_base = INTEREST_RATES.get(base, 2.0)
    r_quote = INTEREST_RATES.get(quote, 2.0)
    diff = r_base - r_quote

    # Map diff to 0-15 range. Largest spread ~5.4% (USD vs JPY) → 15 pts.
    MAX_DIFF = 6.0
    raw = (diff / MAX_DIFF) * 15
    score = max(0.0, min(15.0, raw + 7.5))

    detail = (
        f"{base} 金利 {r_base:.2f}% vs {quote} {r_quote:.2f}% "
        f"(差: {diff:+.2f}%)"
    )
    return round(score, 2), detail


def _central_bank_score(base: str, quote: str) -> tuple[float, str]:
    """
    Score = stance differential (base - quote).
    Range -2 to +2 → mapped to 0-10.
    """
    s_base = CB_STANCE.get(base, 0.0)
    s_quote = CB_STANCE.get(quote, 0.0)
    diff = s_base - s_quote   # -2 to +2

    score = max(0.0, min(10.0, (diff + 2) / 4 * 10))

    base_label = "タカ派" if s_base > 0.3 else ("ハト派" if s_base < -0.3 else "中立")
    quote_label = "タカ派" if s_quote > 0.3 else ("ハト派" if s_quote < -0.3 else "中立")
    cb_base = CB_NAMES.get(base, base)
    cb_quote = CB_NAMES.get(quote, quote)
    detail = f"{cb_base}: {base_label} / {cb_quote}: {quote_label}"
    return round(score, 2), detail


def _economic_score(base: str, quote: str) -> tuple[float, str]:
    """Economic surprise index differential → 0-10 pts."""
    s_base = ECON_SURPRISE.get(base, 0.0)
    s_quote = ECON_SURPRISE.get(quote, 0.0)
    diff = s_base - s_quote   # -2 to +2

    score = max(0.0, min(10.0, (diff + 2) / 4 * 10))
    polarity = "上振れ" if diff > 0.1 else ("下振れ" if diff < -0.1 else "中立")
    detail = f"経済サプライズ {base}: {s_base:+.2f} / {quote}: {s_quote:+.2f} → {polarity}"
    return round(score, 2), detail


def _risk_environment_score(base: str, quote: str) -> tuple[float, str]:
    """
    Risk-on/off proxy based on VIX proxy (hardcoded for demo;
    replace with live VIX feed in production).

    Risk-on  → AUD, NZD, EM currencies rally
    Risk-off → JPY, USD, CHF rally
    """
    RISK_ON_CCY = {"AUD", "NZD", "CAD"}
    RISK_OFF_CCY = {"JPY", "USD", "CHF"}

    # Simulated risk regime: 0 = risk-off, 1 = risk-on
    risk_on = True   # Replace with: fetch_vix() < 20

    score = 5.0
    detail = ""
    if risk_on:
        if base in RISK_ON_CCY and quote in RISK_OFF_CCY:
            score = 5.0
            detail = "リスクオン: リスク通貨買い有利"
        elif base in RISK_OFF_CCY and quote in RISK_ON_CCY:
            score = 0.0
            detail = "リスクオン: 安全通貨売り不利"
        else:
            score = 2.5
            detail = "リスクオン: 中立"
    else:
        if base in RISK_OFF_CCY and quote in RISK_ON_CCY:
            score = 5.0
            detail = "リスクオフ: 安全通貨買い有利"
        elif base in RISK_ON_CCY and quote in RISK_OFF_CCY:
            score = 0.0
            detail = "リスクオフ: リスク通貨売り不利"
        else:
            score = 2.5
            detail = "リスクオフ: 中立"

    return round(score, 2), detail


def compute_fundamental_score(pair: str) -> FundamentalScoreDetail:
    base, quote = pair.split("/")

    ir_score, ir_detail = _interest_rate_score(base, quote)
    cb_score, cb_detail = _central_bank_score(base, quote)
    ec_score, ec_detail = _economic_score(base, quote)
    risk_score, risk_detail = _risk_environment_score(base, quote)

    total = ir_score + cb_score + ec_score + risk_score

    return FundamentalScoreDetail(
        interest_rate_score=ir_score,
        central_bank_score=cb_score,
        economic_score=ec_score,
        risk_score=risk_score,
        total=round(total, 2),
        interest_rate_detail=ir_detail,
        central_bank_detail=cb_detail,
        economic_detail=ec_detail,
        risk_detail=risk_detail,
    )


def get_interest_rate_data() -> list[InterestRateData]:
    return [
        InterestRateData(
            currency=ccy,
            central_bank=CB_NAMES.get(ccy, ccy),
            current_rate=rate,
            previous_rate=rate - 0.25,
            next_meeting="2024-01-31",
            trend="hawkish" if CB_STANCE.get(ccy, 0) > 0 else (
                "dovish" if CB_STANCE.get(ccy, 0) < 0 else "neutral"
            ),
        )
        for ccy, rate in INTEREST_RATES.items()
    ]
