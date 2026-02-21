"""Convenience runner — loads data, runs strategy + backtest for one symbol."""

from __future__ import annotations

from squeeze_surge.data.data_store import DataStore
from squeeze_surge.strategy.strategy_engine import StrategyEngine
from squeeze_surge.backtest.backtest_engine import BacktestEngine
from squeeze_surge.backtest.backtest_result import BacktestResult


def run_backtest(
    symbol: str,
    timeframe: str = "1Day",
    initial_balance: float = 10_000,
    risk_pct: float = 0.01,
) -> BacktestResult:
    """Load parquet → indicators → signals → backtest for *symbol*.

    Returns a :class:`BacktestResult` with trade list and summary metrics.
    """
    store = DataStore()
    df = store.load(symbol, timeframe)

    strategy = StrategyEngine()
    df = strategy.run(symbol, timeframe, df)

    engine = BacktestEngine(initial_balance=initial_balance, risk_pct=risk_pct)
    return engine.run(symbol, df, timeframe=timeframe)
