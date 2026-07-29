"""
Master scoring engine.
Combines technical (60 pts) + fundamental (40 pts) → total 0-100.
Determines direction, strength, checklist, and exit signals.
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional

from app.models.signal import (
    FXSignal,
    SignalDirection,
    SignalStrength,
    AlertItem,
    ExitSignal,
    TechnicalScoreDetail,
    FundamentalScoreDetail,
)
from app.config import settings


def _classify_strength(score: float) -> SignalStrength:
    if score >= settings.strong_buy_threshold:
        return SignalStrength.STRONG
    elif score >= settings.watch_threshold:
        return SignalStrength.WATCH
    return SignalStrength.IGNORE


def _classify_direction(technical: TechnicalScoreDetail, fundamental: FundamentalScoreDetail) -> SignalDirection:
    """
    Direction = base currency BUY if combined score is above neutral (50).
    If technical and fundamental conflict strongly, stay NEUTRAL.
    """
    tech_max = 60.0
    fund_max = 40.0
    tech_mid = tech_max / 2
    fund_mid = fund_max / 2

    tech_bullish = technical.total > tech_mid
    fund_bullish = fundamental.total > fund_mid

    if tech_bullish and fund_bullish:
        return SignalDirection.BUY
    elif not tech_bullish and not fund_bullish:
        return SignalDirection.SELL
    return SignalDirection.NEUTRAL


def _build_checklist(technical: TechnicalScoreDetail, fundamental: FundamentalScoreDetail) -> list[str]:
    items = []

    # Technical checks
    if technical.trend_score >= 15:
        items.append("✅ " + technical.trend_detail)
    elif technical.trend_score <= 5:
        items.append("❌ " + technical.trend_detail)

    if technical.macd_score >= 10:
        items.append("✅ " + technical.macd_detail)
    elif technical.macd_score <= 4:
        items.append("❌ " + technical.macd_detail)

    if technical.rsi_score >= 8:
        items.append("✅ " + technical.rsi_detail)

    if technical.bollinger_score >= 7:
        items.append("✅ " + technical.bollinger_detail)

    # Fundamental checks
    if fundamental.interest_rate_score >= 10:
        items.append("✅ " + fundamental.interest_rate_detail)
    elif fundamental.interest_rate_score <= 4:
        items.append("❌ " + fundamental.interest_rate_detail)

    if fundamental.central_bank_score >= 7:
        items.append("✅ " + fundamental.central_bank_detail)
    elif fundamental.central_bank_score <= 3:
        items.append("❌ " + fundamental.central_bank_detail)

    if fundamental.economic_score >= 7:
        items.append("✅ " + fundamental.economic_detail)

    if fundamental.risk_score >= 4:
        items.append("✅ " + fundamental.risk_detail)

    return items


def _build_alerts(pair: str, technical: TechnicalScoreDetail, fundamental: FundamentalScoreDetail) -> list[AlertItem]:
    alerts = []

    if technical.atr_score == 0:
        alerts.append(AlertItem(level="warning", message=f"⚠ {pair}: ボラティリティ不足 — エントリー見送り推奨"))

    if technical.atr_score == 3:
        alerts.append(AlertItem(level="info", message=f"⚠ {pair}: ATR急上昇中 — ポジションサイズ縮小推奨"))

    if technical.rsi_score <= 3 and "過熱" in technical.rsi_detail:
        alerts.append(AlertItem(level="warning", message=f"⚠ RSI過熱域 ({technical.rsi_detail})"))

    if technical.trend_score <= 5 and technical.macd_score <= 4:
        alerts.append(AlertItem(level="danger", message=f"⚠ {pair}: トレンド崩壊シグナル — ポジション縮小検討"))

    return alerts


def _build_summary(
    pair: str,
    score: float,
    direction: SignalDirection,
    strength: SignalStrength,
    technical: TechnicalScoreDetail,
    fundamental: FundamentalScoreDetail,
) -> str:
    emoji = "🟢" if strength == SignalStrength.STRONG else ("🟡" if strength == SignalStrength.WATCH else "⚪")
    dir_label = "買い候補" if direction == SignalDirection.BUY else ("売り候補" if direction == SignalDirection.SELL else "中立")
    return (
        f"{pair} スコア: {score:.0f}/100  {emoji} {dir_label}\n"
        f"テクニカル: {technical.total:.0f}/60 | "
        f"ファンダ: {fundamental.total:.0f}/40"
    )


def build_signal(
    pair: str,
    current_price: float,
    technical: TechnicalScoreDetail,
    fundamental: FundamentalScoreDetail,
    news_adjustment: float = 0.0,
) -> FXSignal:
    """
    Compose final FXSignal from sub-scores.
    news_adjustment: -3..+3 pts applied to fundamental total.
    """
    adj_fundamental = FundamentalScoreDetail(
        **{
            **fundamental.model_dump(),
            "total": max(0.0, min(40.0, fundamental.total + news_adjustment)),
        }
    )
    total_score = max(0.0, min(100.0, technical.total + adj_fundamental.total))
    direction = _classify_direction(technical, adj_fundamental)
    strength = _classify_strength(total_score)

    return FXSignal(
        pair=pair,
        timestamp=datetime.utcnow(),
        current_price=current_price,
        direction=direction,
        strength=strength,
        total_score=round(total_score, 2),
        technical=technical,
        fundamental=adj_fundamental,
        checklist=_build_checklist(technical, adj_fundamental),
        alerts=_build_alerts(pair, technical, adj_fundamental),
        summary=_build_summary(pair, total_score, direction, strength, technical, adj_fundamental),
    )


def check_exit_signal(pair: str, holding_direction: str, technical: TechnicalScoreDetail, fundamental: FundamentalScoreDetail) -> ExitSignal:
    """
    Generate exit/reversal warning for an open position.
    For a BUY (long base): exit if trend breaks down + MACD bearish + rate narrows.
    """
    danger = False
    reasons = []

    if holding_direction.upper() == "BUY":
        if technical.trend_score <= 5:
            reasons.append("トレンド崩壊(EMA割れ)")
            danger = True
        if technical.macd_score <= 4:
            reasons.append("MACD下降転換")
            danger = True
        if fundamental.interest_rate_score <= 5:
            reasons.append("金利差縮小")
            danger = True
    else:  # SELL
        if technical.trend_score >= 15:
            reasons.append("上昇トレンド回帰")
            danger = True
        if technical.macd_score >= 10:
            reasons.append("MACD上昇転換")
            danger = True

    triggered = len(reasons) >= 2
    return ExitSignal(
        pair=pair,
        direction=holding_direction,
        triggered=triggered,
        reason=" / ".join(reasons) if reasons else "異常なし",
        severity="danger" if danger and triggered else ("warning" if reasons else "info"),
    )
