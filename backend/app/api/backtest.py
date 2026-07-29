from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List

from app.config import settings
from app.services.backtester import run_backtest, BacktestResult, Trade


class TradeOut(BaseModel):
    pair: str
    entry_price: float
    exit_price: float
    direction: str
    entry_date: str
    exit_date: str
    pips: float
    return_pct: float


class BacktestResultOut(BaseModel):
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
    trades: List[TradeOut]


router = APIRouter(prefix="/backtest", tags=["backtest"])


@router.get("/{pair:path}", response_model=BacktestResultOut)
async def get_backtest(
    pair: str,
    years: int = Query(5, ge=1, le=10, description="Backtest period in years"),
    score_threshold: int = Query(65, ge=50, le=95),
    hold_bars: int = Query(5, ge=1, le=20),
    stop_loss_pips: float = Query(50, ge=5, le=200),
    take_profit_pips: float = Query(100, ge=10, le=500),
):
    """Run a walk-forward backtest for a currency pair."""
    pair = pair.upper().replace("-", "/")
    if pair not in settings.fx_pairs:
        raise HTTPException(404, f"Pair {pair} not supported")

    result = await run_backtest(pair, years=years)

    trades_out = [
        TradeOut(
            pair=t.pair,
            entry_price=t.entry_price,
            exit_price=t.exit_price,
            direction=t.direction,
            entry_date=t.entry_date,
            exit_date=t.exit_date,
            pips=t.pips,
            return_pct=t.return_pct,
        )
        for t in result.trades
    ]

    return BacktestResultOut(
        pair=result.pair,
        start_date=result.start_date,
        end_date=result.end_date,
        total_trades=result.total_trades,
        wins=result.wins,
        losses=result.losses,
        win_rate=result.win_rate,
        avg_profit_pips=result.avg_profit_pips,
        avg_loss_pips=result.avg_loss_pips,
        profit_factor=result.profit_factor,
        max_consecutive_losses=result.max_consecutive_losses,
        max_drawdown_pct=result.max_drawdown_pct,
        sharpe_ratio=result.sharpe_ratio,
        total_return_pct=result.total_return_pct,
        trades=trades_out,
    )
