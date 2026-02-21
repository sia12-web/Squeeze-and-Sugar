"""Tests for Optimizer."""

from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

from squeeze_surge.optimization.optimizer import Optimizer
from squeeze_surge.backtest.backtest_result import BacktestResult


def _make_ohlcv(n: int = 200) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    close = [150.0]
    for _ in range(n - 1):
        close.append(close[-1] + rng.normal(0, 1.5))
    close_arr = np.array(close)
    return pd.DataFrame({
        "time": pd.date_range("2022-01-03", periods=n, freq="B"),
        "open": close_arr + rng.normal(0, 0.5, n),
        "high": close_arr + rng.uniform(0.5, 3.0, n),
        "low": close_arr - rng.uniform(0.5, 3.0, n),
        "close": close_arr,
        "volume": rng.integers(500_000, 5_000_000, n),
    })


def test_split_is_chronological():
    """IS end date must be before OOS start date."""
    df = _make_ohlcv(200)
    split_idx = int(len(df) * 0.7)
    df_is = df.iloc[:split_idx]
    df_oos = df.iloc[split_idx:]
    assert df_is["time"].iloc[-1] < df_oos["time"].iloc[0]


def test_fails_validation_on_low_sharpe():
    """Sharpe=0.1 should fail both primary and fallback gates."""
    low_sharpe_result = BacktestResult(
        symbol="TEST", total_trades=15, win_rate=0.5,
        sharpe=0.1, max_drawdown=0.1, profit_factor=1.5,
        final_balance=10_100, return_pct=1.0, trades=[],
    )

    with patch.object(Optimizer, "_backtest", return_value=low_sharpe_result):
        with patch("squeeze_surge.optimization.optimizer.DataStore") as MockStore:
            MockStore.return_value.load.return_value = _make_ohlcv(200)
            opt = Optimizer("TEST")
            result = opt.run()
            assert not result.passed_validation


def test_min_oos_trades_is_10():
    """9 trades should fail the minimum-trades gate (primary/fallback = 10)."""
    few_trades_result = BacktestResult(
        symbol="TEST", total_trades=9, win_rate=1.0,
        sharpe=1.0, max_drawdown=0.05, profit_factor=3.0,
        final_balance=10_500, return_pct=5.0, trades=[],
    )

    with patch.object(Optimizer, "_backtest", return_value=few_trades_result):
        with patch("squeeze_surge.optimization.optimizer.DataStore") as MockStore:
            MockStore.return_value.load.return_value = _make_ohlcv(200)
            opt = Optimizer("TEST")
            result = opt.run()
            assert not result.passed_validation


def test_default_timeframe_is_1hour():
    opt = Optimizer("TEST")
    assert opt.timeframe == "1Hour"
