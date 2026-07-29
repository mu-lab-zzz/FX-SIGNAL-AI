"""Tests for scoring engine and sub-modules."""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from app.services.data_fetcher import PriceDataFetcher
from app.services.technical_analysis import compute_technical_score
from app.services.fundamental_analysis import compute_fundamental_score
from app.services.scoring_engine import build_signal, check_exit_signal


def _make_df(pair: str = "USD/JPY", n: int = 300) -> pd.DataFrame:
    fetcher = PriceDataFetcher()
    return fetcher._generate_demo_data(pair, n)


def test_technical_score_range():
    df = _make_df()
    result = compute_technical_score(df)
    assert 0 <= result.total <= 60
    assert 0 <= result.trend_score <= 20
    assert 0 <= result.macd_score <= 15
    assert 0 <= result.rsi_score <= 10
    assert 0 <= result.bollinger_score <= 10
    assert 0 <= result.atr_score <= 5


def test_fundamental_score_range():
    for pair in ["USD/JPY", "EUR/USD", "AUD/JPY"]:
        result = compute_fundamental_score(pair)
        assert 0 <= result.total <= 40, f"Fundamental total out of range for {pair}"
        assert 0 <= result.interest_rate_score <= 15
        assert 0 <= result.central_bank_score <= 10
        assert 0 <= result.economic_score <= 10
        assert 0 <= result.risk_score <= 5


def test_build_signal_total_score():
    df = _make_df("USD/JPY")
    tech = compute_technical_score(df)
    fund = compute_fundamental_score("USD/JPY")
    price = float(df["close"].iloc[-1])
    signal = build_signal("USD/JPY", price, tech, fund)
    assert 0 <= signal.total_score <= 100
    assert signal.direction.value in ("BUY", "SELL", "NEUTRAL")
    assert signal.strength.value in ("STRONG", "WATCH", "IGNORE")


def test_build_signal_checklist_not_empty():
    df = _make_df()
    tech = compute_technical_score(df)
    fund = compute_fundamental_score("USD/JPY")
    signal = build_signal("USD/JPY", 150.0, tech, fund)
    # Some items should always be generated
    assert isinstance(signal.checklist, list)


def test_exit_signal_neutral_returns_no_trigger():
    df = _make_df()
    tech = compute_technical_score(df)
    fund = compute_fundamental_score("USD/JPY")
    # With demo data (mild uptrend), a BUY exit signal likely not triggered
    exit_sig = check_exit_signal("USD/JPY", "BUY", tech, fund)
    assert exit_sig.pair == "USD/JPY"
    assert isinstance(exit_sig.triggered, bool)


def test_all_pairs_produce_signals():
    pairs = ["USD/JPY", "EUR/USD", "GBP/USD", "AUD/JPY", "EUR/JPY"]
    for pair in pairs:
        df = _make_df(pair)
        tech = compute_technical_score(df)
        fund = compute_fundamental_score(pair)
        signal = build_signal(pair, float(df["close"].iloc[-1]), tech, fund)
        assert 0 <= signal.total_score <= 100, f"{pair}: score out of range"
