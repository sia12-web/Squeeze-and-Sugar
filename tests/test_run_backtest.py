"""Tests for run_backtest convenience function."""

from squeeze_surge.backtest.run_backtest import run_backtest
from squeeze_surge.backtest.backtest_result import BacktestResult


def test_returns_backtest_result():
    """Full pipeline on real AAPL 1Day parquet → BacktestResult with all fields."""
    result = run_backtest("AAPL", timeframe="1Day")

    assert isinstance(result, BacktestResult)
    assert result.symbol == "AAPL"
    assert result.total_trades >= 0
    assert 0.0 <= result.win_rate <= 1.0
    assert result.final_balance > 0
    assert isinstance(result.trades, list)
    assert hasattr(result, "sharpe")
    assert hasattr(result, "max_drawdown")
    assert hasattr(result, "profit_factor")
    assert hasattr(result, "return_pct")
