"""Tests for BacktestEngine."""

from datetime import datetime, timezone

import numpy as np
import pandas as pd
import pytz

from squeeze_surge.backtest.backtest_engine import BacktestEngine


ET = pytz.timezone("America/New_York")


def _base_signal_df(n: int = 60) -> pd.DataFrame:
    """Minimal DataFrame with all required backtest columns, no signals."""
    close = [100.0 + i * 0.5 for i in range(n)]
    return pd.DataFrame(
        {
            "time": pd.date_range("2025-01-02 09:30", periods=n, freq="h", tz="America/New_York").tz_convert("UTC"),
            "open": [c - 0.1 for c in close],
            "high": [c + 1.0 for c in close],
            "low": [c - 1.0 for c in close],
            "close": close,
            "volume": [1000] * n,
            "signal": [0] * n,
            "signal_type": [""] * n,
            "entry_price": [np.nan] * n,
            "stop_loss": [np.nan] * n,
            "trail_stop_pct": [np.nan] * n,
            "exit_signal": [0] * n,
            "momentum_delta": [1.0] * n,
            "bb_upper": [c + 3.0 for c in close],
            "bb_lower": [c - 3.0 for c in close],
        }
    )


def test_trailing_stop_triggers_correctly():
    """Price rises then drops >5% from peak → exit_reason='trail_stop'."""
    df = _base_signal_df(40)

    # Entry signal on bar 5
    df.loc[5, "signal"] = 1
    df.loc[5, "entry_price"] = df.loc[5, "close"]
    df.loc[5, "stop_loss"] = df.loc[5, "close"] - 10.0
    df.loc[5, "trail_stop_pct"] = 0.05

    # Price rises from bars 6-15
    for i in range(6, 16):
        df.loc[i, "close"] = 120.0 + i * 0.5
        df.loc[i, "high"] = 121.0 + i * 0.5
        df.loc[i, "low"] = 119.0 + i * 0.5
        df.loc[i, "momentum_delta"] = 1.0

    peak_high = df.loc[15, "high"]  # ~128.5

    # Bar 16+: price crashes >5% below peak
    for i in range(16, 20):
        crash_price = peak_high * 0.93  # 7% below peak
        df.loc[i, "close"] = crash_price
        df.loc[i, "high"] = crash_price + 0.1
        df.loc[i, "low"] = crash_price - 0.1
        df.loc[i, "momentum_delta"] = 1.0  # Keep positive so only trail triggers

    engine = BacktestEngine(initial_balance=10_000)
    result = engine.run("TEST", df, timeframe="1Day")

    assert result.total_trades >= 1
    trail_trades = [t for t in result.trades if t.exit_reason == "trail_stop"]
    assert len(trail_trades) >= 1, f"Expected trail_stop exit, got reasons: {[t.exit_reason for t in result.trades]}"


def test_market_hours_filter_skips_premarket():
    """A signal at 07:00 ET should NOT be processed in 1Hour mode."""
    df = _base_signal_df(10)

    # Set ALL bar times to 07:00 ET on different days (all pre-market)
    premarket = pd.to_datetime(
        [f"2025-01-{2+i:02d} 07:00" for i in range(10)]
    ).tz_localize("America/New_York").tz_convert("UTC")
    df["time"] = premarket

    # Put a signal on bar 3
    df.loc[3, "signal"] = 1
    df.loc[3, "entry_price"] = 101.0
    df.loc[3, "stop_loss"] = 99.0
    df.loc[3, "trail_stop_pct"] = 0.05

    engine = BacktestEngine()
    result = engine.run("TEST", df, timeframe="1Hour")

    assert result.total_trades == 0, "Pre-market signal should be skipped"


def test_one_trade_at_a_time():
    """Engine should never open a second position while one is active."""
    df = _base_signal_df(40)

    # Two signals close together
    for i in [5, 8]:
        df.loc[i, "signal"] = 1
        df.loc[i, "entry_price"] = df.loc[i, "close"]
        df.loc[i, "stop_loss"] = df.loc[i, "close"] - 10.0
        df.loc[i, "trail_stop_pct"] = 0.05

    engine = BacktestEngine()
    result = engine.run("TEST", df, timeframe="1Day")

    # Should have at most 1 trade (second signal ignored while first is open)
    # The first trade may close via end_of_data, but never two simultaneous
    assert result.total_trades <= 2  # at most sequential, never overlapping
    # Verify no overlapping entry times
    if result.total_trades == 2:
        t1, t2 = result.trades
        assert t1.exit_time is not None
        assert t1.exit_time <= t2.entry_time
