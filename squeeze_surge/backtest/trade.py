"""Trade dataclass — represents a single round-trip trade."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Trade:
    """A single entry → exit trade.

    Call :meth:`close` to finalise exit fields and calculate PnL.
    """

    symbol: str
    direction: str  # 'long' or 'short'
    entry_price: float
    entry_time: datetime
    shares: int
    stop_loss: float
    trail_stop_pct: float

    exit_price: float = 0.0
    exit_time: datetime | None = None
    exit_reason: str = ""
    pnl: float = 0.0
    pnl_pct: float = 0.0

    def close(self, exit_price: float, exit_time: datetime, reason: str) -> None:
        """Finalise the trade with exit details and compute PnL."""
        self.exit_price = exit_price
        self.exit_time = exit_time
        self.exit_reason = reason

        if self.direction == "long":
            self.pnl = (exit_price - self.entry_price) * self.shares
            self.pnl_pct = (exit_price - self.entry_price) / self.entry_price
        else:  # short
            self.pnl = (self.entry_price - exit_price) * self.shares
            self.pnl_pct = (self.entry_price - exit_price) / self.entry_price
