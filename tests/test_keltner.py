"""Tests for KeltnerChannels indicator."""

import pandas as pd
import pytest

from squeeze_surge.indicators.keltner import KeltnerChannels


def _make_ohlcv(n: int = 50) -> pd.DataFrame:
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


def test_kc_upper_above_lower():
    """kc_upper must be > kc_lower for all non-NaN rows."""
    df = KeltnerChannels().calculate(_make_ohlcv())
    valid = df.dropna(subset=["kc_upper", "kc_lower"])
    assert not valid.empty
    assert (valid["kc_upper"] > valid["kc_lower"]).all()


def test_missing_columns_raises():
    df = pd.DataFrame({"close": [1, 2, 3]})
    with pytest.raises(ValueError, match="Missing required columns"):
        KeltnerChannels().calculate(df)
