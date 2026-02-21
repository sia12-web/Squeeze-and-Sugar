"""Tests for Momentum indicator."""

import pandas as pd

from squeeze_surge.indicators.momentum import Momentum


def _make_uptrend(n: int = 50) -> pd.DataFrame:
    close = [100 + i * 2.0 for i in range(n)]
    return pd.DataFrame(
        {
            "open": [c - 0.1 for c in close],
            "high": [c + 1.0 for c in close],
            "low": [c - 1.0 for c in close],
            "close": close,
            "volume": [1000] * n,
        }
    )


def _make_accelerating(n: int = 50) -> pd.DataFrame:
    """Quadratic price series — momentum itself increases each bar."""
    close = [100 + i ** 2 * 0.1 for i in range(n)]
    return pd.DataFrame(
        {
            "open": [c - 0.1 for c in close],
            "high": [c + 1.0 for c in close],
            "low": [c - 1.0 for c in close],
            "close": close,
            "volume": [1000] * n,
        }
    )


def test_momentum_positive_in_uptrend():
    """In a steady uptrend, momentum should be > 0."""
    df = Momentum(period=12).calculate(_make_uptrend())
    valid = df.dropna(subset=["momentum"])
    assert (valid["momentum"] > 0).all()


def test_momentum_delta_direction():
    """In an accelerating price series, momentum_delta should be > 0."""
    df = Momentum(period=12).calculate(_make_accelerating())
    valid = df.dropna(subset=["momentum_delta"])
    # Allow a tiny tolerance for floating-point edge cases at the start
    assert (valid["momentum_delta"] >= -1e-10).all()
    assert (valid["momentum_delta"] > 0).any()
