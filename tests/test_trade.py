"""Tests for Trade dataclass."""

from datetime import datetime, timezone

from squeeze_surge.backtest.trade import Trade


def _make_trade(direction: str = "long", entry: float = 100.0, shares: int = 10) -> Trade:
    return Trade(
        symbol="TEST",
        direction=direction,
        entry_price=entry,
        entry_time=datetime(2025, 1, 1, tzinfo=timezone.utc),
        shares=shares,
        stop_loss=95.0 if direction == "long" else 105.0,
        trail_stop_pct=0.05,
    )


def test_long_pnl_positive_on_profit():
    t = _make_trade("long", entry=100.0, shares=10)
    t.close(110.0, datetime(2025, 1, 5, tzinfo=timezone.utc), "trail_stop")
    assert t.pnl > 0
    assert t.pnl == 100.0  # (110-100) × 10
    assert t.pnl_pct > 0


def test_short_pnl_positive_on_profit():
    t = _make_trade("short", entry=100.0, shares=10)
    t.close(90.0, datetime(2025, 1, 5, tzinfo=timezone.utc), "trail_stop")
    assert t.pnl > 0
    assert t.pnl == 100.0  # (100-90) × 10
    assert t.pnl_pct > 0
