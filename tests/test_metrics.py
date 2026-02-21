"""Tests for performance metrics."""

import numpy as np

from squeeze_surge.backtest.metrics import sharpe_ratio, max_drawdown
from squeeze_surge.backtest.trade import Trade


def test_sharpe_positive_for_consistent_gains():
    daily_returns = [0.01, 0.005, 0.008, 0.012, 0.003, 0.007, 0.006]
    assert sharpe_ratio(daily_returns) > 0


def test_max_drawdown_correct():
    equity = [100, 120, 80, 90]
    dd = max_drawdown(equity)
    assert abs(dd - (40 / 120)) < 1e-6  # 33.33%
