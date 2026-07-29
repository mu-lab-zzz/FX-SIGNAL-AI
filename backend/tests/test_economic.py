"""Economic calendar and CB analyzer tests."""
import pytest
from app.services.economic_calendar import DEMO_EVENTS, compute_surprise_scores
from app.services.cb_analyzer import _static_fallback


def test_surprise_scores_range():
    scores = compute_surprise_scores(DEMO_EVENTS)
    for ccy, score in scores.items():
        assert -1.0 <= score <= 1.0, f"{ccy}: {score} out of range"


def test_surprise_scores_keys():
    scores = compute_surprise_scores(DEMO_EVENTS)
    assert "USD" in scores
    assert "EUR" in scores


def test_static_cb_fallback():
    stances = _static_fallback()
    assert "USD" in stances
    assert "JPY" in stances
    for ccy, v in stances.items():
        assert -1.0 <= v <= 1.0, f"{ccy}: {v}"
