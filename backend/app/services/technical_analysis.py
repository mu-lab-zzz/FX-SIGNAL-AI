"""
Technical analysis scoring (max 60 pts).

① Trend  : EMA20/50/200           → 0-20 pts
② MACD   : crossover + histogram  → 0-15 pts
③ RSI    : directional zone        → 0-10 pts
④ BB     : bandwalk / squeeze      → 0-10 pts
⑤ ATR    : volatility gate         → 0-5  pts
"""

import pandas as pd
from app.models.signal import TechnicalScoreDetail
from app.services.indicators import ema, rsi, macd, bollinger_bands, atr


def score_trend(df: pd.DataFrame) -> tuple[float, str]:
    close = df["close"]
    ema20 = ema(close, 20)
    ema50 = ema(close, 50)
    ema200 = ema(close, 200)

    c = close.iloc[-1]
    e20 = ema20.iloc[-1]
    e50 = ema50.iloc[-1]
    e200 = ema200.iloc[-1]
    e20_prev = ema20.iloc[-2]
    e50_prev = ema50.iloc[-2]

    score = 0.0
    notes = []

    if c > e50:
        score += 8
        notes.append("価格>EMA50")
    elif c < e50:
        score -= 8

    if e50 > e200:
        score += 8
        notes.append("EMA50>EMA200(強気)")
    elif e50 < e200:
        score -= 4

    if e20 > e50 and e20_prev <= e50_prev:
        score += 4
        notes.append("EMA20がEMA50を上抜け")
    elif e20 < e50 and e20_prev >= e50_prev:
        score -= 4
        notes.append("EMA20がEMA50を下抜け(下落)")

    score = max(0.0, min(20.0, score + 10))
    detail = " / ".join(notes) if notes else "トレンド不明瞭"
    return score, detail


def score_macd(df: pd.DataFrame) -> tuple[float, str]:
    macd_line, signal_line, histogram = macd(df["close"])

    m = macd_line.iloc[-1]
    m_prev = macd_line.iloc[-2]
    s = signal_line.iloc[-1]
    s_prev = signal_line.iloc[-2]
    h = histogram.iloc[-1]
    h_prev = histogram.iloc[-2]

    score = 0.0
    notes = []

    if m > s and m_prev <= s_prev:
        score += 7
        notes.append("MACDクロス(上昇転換)")
    elif m < s and m_prev >= s_prev:
        score -= 7
        notes.append("MACDクロス(下降転換)")
    elif m > s:
        score += 4
        notes.append("MACD>シグナル")
    else:
        score -= 4

    if abs(h) > abs(h_prev):
        score += 4
        notes.append("ヒストグラム拡大")

    if m > 0:
        score += 4
        notes.append("0ライン上")
    else:
        score -= 2

    score = max(0.0, min(15.0, score + 7))
    detail = " / ".join(notes) if notes else "MACD中立"
    return score, detail


def score_rsi(df: pd.DataFrame) -> tuple[float, str]:
    rsi_series = rsi(df["close"])
    r = rsi_series.iloc[-1]
    r_prev = rsi_series.iloc[-5]

    score = 0.0
    notes = []
    direction_up = r > r_prev

    if 40 <= r <= 60:
        if direction_up:
            score = 10
            notes.append(f"RSI={r:.1f} 正常上昇ゾーン")
        else:
            score = -5
            notes.append(f"RSI={r:.1f} 正常下降ゾーン")
    elif r > 60:
        score = 3
        notes.append(f"RSI={r:.1f} 高水準(過熱注意)")
    elif r < 40:
        score = -3
        notes.append(f"RSI={r:.1f} 低水準")

    score = max(0.0, min(10.0, score + 5))
    detail = notes[0] if notes else f"RSI={r:.1f}"
    return score, detail


def score_bollinger(df: pd.DataFrame) -> tuple[float, str]:
    upper, mid, lower, width = bollinger_bands(df["close"])

    c = df["close"].iloc[-1]
    u = upper.iloc[-1]
    l = lower.iloc[-1]
    m = mid.iloc[-1]
    w = width.iloc[-1]
    w_prev = width.iloc[-10]

    score = 0.0
    notes = []

    if w < w_prev * 0.8:
        score += 5
        notes.append("スクイーズ解除(ブレイク期待)")

    if c > u:
        score += 5
        notes.append("バンドウォーク(上昇)")
    elif c < l:
        score -= 5
        notes.append("バンドウォーク(下落)")
    elif c > m:
        score += 3
        notes.append("中心線上")
    else:
        score -= 2

    score = max(0.0, min(10.0, score + 5))
    detail = " / ".join(notes) if notes else "BB中立"
    return score, detail


def score_atr(df: pd.DataFrame) -> tuple[float, str]:
    atr_series = atr(df["high"], df["low"], df["close"])
    atr_val = atr_series.iloc[-1]
    atr_avg = atr_series.tail(30).mean()

    ratio = atr_val / atr_avg if atr_avg > 0 else 1.0

    if ratio < 0.5:
        score = 0.0
        detail = f"ATR低(ボラ不足 {atr_val:.4f})"
    elif 0.5 <= ratio <= 1.5:
        score = 5.0
        detail = f"ATR正常({atr_val:.4f})"
    else:
        score = 3.0
        detail = f"ATR急上昇(急変注意 {atr_val:.4f})"

    return score, detail


def compute_technical_score(df: pd.DataFrame) -> TechnicalScoreDetail:
    trend_score, trend_detail = score_trend(df)
    macd_score, macd_detail = score_macd(df)
    rsi_score, rsi_detail = score_rsi(df)
    bb_score, bb_detail = score_bollinger(df)
    atr_score, atr_detail = score_atr(df)

    total = trend_score + macd_score + rsi_score + bb_score + atr_score

    return TechnicalScoreDetail(
        trend_score=round(trend_score, 2),
        macd_score=round(macd_score, 2),
        rsi_score=round(rsi_score, 2),
        bollinger_score=round(bb_score, 2),
        atr_score=round(atr_score, 2),
        total=round(total, 2),
        trend_detail=trend_detail,
        macd_detail=macd_detail,
        rsi_detail=rsi_detail,
        bollinger_detail=bb_detail,
        atr_detail=atr_detail,
    )
