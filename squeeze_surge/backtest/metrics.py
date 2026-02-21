"""Performance metrics for backtesting."""

from __future__ import annotations

import numpy as np

from squeeze_surge.backtest.trade import Trade


def sharpe_ratio(daily_returns: np.ndarray | list[float]) -> float:
    """Annualised Sharpe ratio (risk-free rate = 0).

    Sharpe = mean(daily_returns) / std(daily_returns) × √252
    """
    dr = np.asarray(daily_returns, dtype=float)
    if len(dr) < 2 or np.std(dr) == 0:
        return 0.0
    return float(np.mean(dr) / np.std(dr) * np.sqrt(252))


def max_drawdown(equity_curve: np.ndarray | list[float]) -> float:
    """Maximum drawdown as a positive fraction (0-1).

    Example: [100, 120, 80] → 0.333 (33.3% drop from 120 peak).
    """
    eq = np.asarray(equity_curve, dtype=float)
    if len(eq) < 2:
        return 0.0
    running_max = np.maximum.accumulate(eq)
    drawdowns = (running_max - eq) / running_max
    return float(np.max(drawdowns))


def profit_factor(trades: list[Trade]) -> float:
    """Gross profit / gross loss.  Returns inf if no losing trades."""
    gross_profit = sum(t.pnl for t in trades if t.pnl > 0)
    gross_loss = abs(sum(t.pnl for t in trades if t.pnl < 0))
    if gross_loss == 0:
        return float("inf") if gross_profit > 0 else 0.0
    return gross_profit / gross_loss


def win_rate(trades: list[Trade]) -> float:
    """Fraction of trades with positive PnL (0-1)."""
    if not trades:
        return 0.0
    winners = sum(1 for t in trades if t.pnl > 0)
    return winners / len(trades)
