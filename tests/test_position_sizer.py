"""Tests for PositionSizer."""

import pytest

from squeeze_surge.strategy.position_sizer import PositionSizer


def test_risk_1pct_of_balance():
    """shares × risk_per_share should approximately equal 1% of balance."""
    sizer = PositionSizer()
    balance = 10_000.0
    risk_pct = 0.01
    entry = 150.0
    stop = 148.0  # risk per share = $2

    shares = sizer.calculate(balance, risk_pct, entry, stop)
    risk_amount = shares * abs(entry - stop)

    # floor(100 / 2) = 50 shares → $100 risk
    assert shares == 50
    assert risk_amount == pytest.approx(100.0, abs=2.0)
