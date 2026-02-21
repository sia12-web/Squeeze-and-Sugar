"""Tests for BollingerBands indicator."""

import pandas as pd
import pytest

from squeeze_surge.indicators.bollinger import BollingerBands


def _make_ohlcv(n: int = 50) -> pd.DataFrame:
    """Generate a simple rising OHLCV DataFrame."""
    close = [100 + i * 0.5 for i in range(n)]
    return pd.DataFrame(
        {
            "open": [c - 0.1 for c in close],
            "high": [c + 1.0 for c in close],
            "low": [c - 1.0 for c in close],
            "close": close,
            "volume": [1000] * n,
        }
    )


def test_bb_width_positive():
    """bb_width must be > 0 for all non-NaN rows."""
    df = BollingerBands().calculate(_make_ohlcv())
    valid = df.dropna(subset=["bb_width"])
    assert not valid.empty
    assert (valid["bb_width"] > 0).all()


def test_missing_columns_raises():
    df = pd.DataFrame({"close": [1, 2, 3]})
    with pytest.raises(ValueError, match="Missing required columns"):
        BollingerBands().calculate(df)
