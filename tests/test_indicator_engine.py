"""Tests for IndicatorEngine."""

import pandas as pd

from squeeze_surge.indicators.indicator_engine import IndicatorEngine, INDICATOR_COLUMNS


def _make_ohlcv(n: int = 60) -> pd.DataFrame:
    close = [100 + i * 0.5 for i in range(n)]
    return pd.DataFrame(
        {
            "open": [c - 0.1 for c in close],
            "high": [c + 2.0 for c in close],
            "low": [c - 2.0 for c in close],
            "close": close,
            "volume": [1000] * n,
        }
    )


def test_run_adds_all_columns():
    """IndicatorEngine.run() must add all 12 indicator columns."""
    engine = IndicatorEngine()
    df = engine.run("AAPL", "1Day", _make_ohlcv())
    for col in INDICATOR_COLUMNS:
        assert col in df.columns, f"Missing indicator column: {col}"
