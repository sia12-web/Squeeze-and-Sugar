"""Backtest result dataclass."""

from __future__ import annotations

from dataclasses import dataclass, field

from squeeze_surge.backtest.trade import Trade


@dataclass
class BacktestResult:
    """Container for backtest output."""

    symbol: str
    total_trades: int
    win_rate: float
    sharpe: float
    max_drawdown: float
    profit_factor: float
    final_balance: float
    return_pct: float
    trades: list[Trade] = field(default_factory=list)
    equity_curve: list[tuple[any, float]] = field(default_factory=list)
