"""
Backtesting engine — walks historical bars and simulates signal-driven trades.

Metrics:
  - Win rate
  - Average profit (pips)
  - Average loss (pips)
  - Profit factor
  - Max consecutive losses
  - Max drawdown
  - Sharpe ratio (simplified)
"""

from __future__ import annotations
import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import numpy as np
import pandas as pd

from app.services.technical_analysis import compute_technical_score
from app.services.fundamental_analysis import compute_fundamental_score
from app.services.scoring_engine import build_signal
from app.services.data_fetcher import price_fetcher
from app.config import settings


@dataclass
class Trade:
    pair: str
    entry_price: float
    exit_price: float
    direction: str   # "BUY" | "SELL"
    entry_date: str
    exit_date: str
    pips: float      # positive = profit
    return_pct: float


@dataclass
class BacktestResult:
    pair: str
    start_date: str
    end_date: str
    total_trades: int
    wins: int
    losses: int
    win_rate: float
    avg_profit_pips: float
    avg_loss_pips: float
    profit_factor: float
    max_consecutive_losses: int
    max_drawdown_pct: float
    sharpe_ratio: float
    total_return_pct: float
    trades: list[Trade] = field(default_factory=list)


def _pip_value(pair: str) -> float:
    """Return pip size for a currency pair."""
    if "JPY" in pair:
        return 0.01
    return 0.0001


def _compute_pips(pair: str, entry: float, exit_p: float, direction: str) -> float:
    pip = _pip_value(pair)
    raw = (exit_p - entry) if direction == "BUY" else (entry - exit_p)
    return raw / pip


def backtest_pair(
    df: pd.DataFrame,
    pair: str,
    score_threshold: int = 65,
    hold_bars: int = 5,       # hold for N daily bars before exit
    stop_loss_pips: float = 50,
    take_profit_pips: float = 100,
) -> BacktestResult:
    """
    Walk-forward backtest on daily OHLCV data.
    Entry: score >= threshold
    Exit:  take-profit OR stop-loss OR hold_bars elapsed
    """
    pip = _pip_value(pair)
    fund = compute_fundamental_score(pair)

    trades: list[Trade] = []
    i = 200   # start after enough history for indicators

    while i < len(df) - hold_bars - 1:
        window = df.iloc[: i + 1]
        try:
            tech = compute_technical_score(window)
        except Exception:
            i += 1
            continue

        signal = build_signal(pair, float(window["close"].iloc[-1]), tech, fund)

        if signal.total_score >= score_threshold and signal.direction.value in ("BUY", "SELL"):
            entry_idx = i + 1
            entry_price = float(df["open"].iloc[entry_idx])
            direction = signal.direction.value
            entry_date = str(df.index[entry_idx])

            exit_idx = None
            exit_price = entry_price
            for j in range(1, hold_bars + 2):
                if entry_idx + j >= len(df):
                    break
                bar = df.iloc[entry_idx + j]
                pips_high = _compute_pips(pair, entry_price, float(bar["high"]), direction)
                pips_low = _compute_pips(pair, entry_price, float(bar["low"]), direction)

                if pips_high >= take_profit_pips:
                    exit_price = entry_price + take_profit_pips * pip * (1 if direction == "BUY" else -1)
                    exit_idx = entry_idx + j
                    break
                if pips_low <= -stop_loss_pips:
                    exit_price = entry_price - stop_loss_pips * pip * (1 if direction == "BUY" else -1)
                    exit_idx = entry_idx + j
                    break

            if exit_idx is None:
                exit_idx = min(entry_idx + hold_bars, len(df) - 1)
                exit_price = float(df["close"].iloc[exit_idx])

            pips = _compute_pips(pair, entry_price, exit_price, direction)
            trades.append(
                Trade(
                    pair=pair,
                    entry_price=entry_price,
                    exit_price=exit_price,
                    direction=direction,
                    entry_date=entry_date,
                    exit_date=str(df.index[exit_idx]),
                    pips=round(pips, 1),
                    return_pct=round((exit_price / entry_price - 1) * 100, 4),
                )
            )
            i = exit_idx + 1
        else:
            i += 1

    # ── Metrics ──────────────────────────────────────────────────────────────
    if not trades:
        return BacktestResult(
            pair=pair,
            start_date=str(df.index[200]),
            end_date=str(df.index[-1]),
            total_trades=0,
            wins=0,
            losses=0,
            win_rate=0.0,
            avg_profit_pips=0.0,
            avg_loss_pips=0.0,
            profit_factor=0.0,
            max_consecutive_losses=0,
            max_drawdown_pct=0.0,
            sharpe_ratio=0.0,
            total_return_pct=0.0,
        )

    wins = [t for t in trades if t.pips > 0]
    losses = [t for t in trades if t.pips <= 0]
    win_rate = len(wins) / len(trades) * 100

    avg_profit = np.mean([t.pips for t in wins]) if wins else 0.0
    avg_loss = abs(np.mean([t.pips for t in losses])) if losses else 0.0
    gross_profit = sum(t.pips for t in wins)
    gross_loss = abs(sum(t.pips for t in losses))
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float("inf")

    # Max consecutive losses
    max_consec = cur_consec = 0
    for t in trades:
        if t.pips <= 0:
            cur_consec += 1
            max_consec = max(max_consec, cur_consec)
        else:
            cur_consec = 0

    # Max drawdown (cumulative pip curve)
    cum = np.cumsum([t.pips for t in trades])
    peak = np.maximum.accumulate(cum)
    drawdown = (peak - cum) / (np.abs(peak) + 1e-9) * 100
    max_dd = float(np.max(drawdown))

    # Sharpe (daily pip returns)
    returns = np.array([t.pips for t in trades])
    sharpe = (np.mean(returns) / (np.std(returns) + 1e-9)) * np.sqrt(252 / max(1, len(trades)))

    total_return = float(sum(t.return_pct for t in trades))

    return BacktestResult(
        pair=pair,
        start_date=str(df.index[200]),
        end_date=str(df.index[-1]),
        total_trades=len(trades),
        wins=len(wins),
        losses=len(losses),
        win_rate=round(win_rate, 2),
        avg_profit_pips=round(avg_profit, 1),
        avg_loss_pips=round(avg_loss, 1),
        profit_factor=round(profit_factor, 2),
        max_consecutive_losses=max_consec,
        max_drawdown_pct=round(max_dd, 2),
        sharpe_ratio=round(sharpe, 3),
        total_return_pct=round(total_return, 4),
        trades=trades[-50:],   # return last 50 trades for display
    )


async def run_backtest(pair: str, years: int = 5) -> BacktestResult:
    bars = years * 252
    df = await price_fetcher.fetch_ohlcv(pair, count=bars)
    return backtest_pair(df, pair)
