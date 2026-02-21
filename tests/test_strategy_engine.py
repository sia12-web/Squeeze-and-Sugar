"""Tests for StrategyEngine."""

import numpy as np
import pandas as pd

from squeeze_surge.strategy.strategy_engine import StrategyEngine


def _make_realistic_ohlcv(n: int = 200) -> pd.DataFrame:
    """Generate a realistic-ish OHLCV series with some volatility clustering."""
    rng = np.random.default_rng(42)
    close = [150.0]
    for _ in range(n - 1):
        close.append(close[-1] + rng.normal(0, 1.5))

    close_arr = np.array(close)
    high = close_arr + rng.uniform(0.5, 3.0, n)
    low = close_arr - rng.uniform(0.5, 3.0, n)
    opn = close_arr + rng.normal(0, 0.5, n)
    volume = rng.integers(500_000, 5_000_000, n)

    return pd.DataFrame(
        {
            "open": opn,
            "high": high,
            "low": low,
            "close": close_arr,
            "volume": volume,
        }
    )


def test_run_returns_signal_column():
    """StrategyEngine.run() must produce a signal column with values in {-1, 0, 1}."""
    engine = StrategyEngine()
    df = engine.run("AAPL", "1Day", _make_realistic_ohlcv(300))
    assert "signal" in df.columns
    assert set(df["signal"].unique()).issubset({-1, 0, 1})
