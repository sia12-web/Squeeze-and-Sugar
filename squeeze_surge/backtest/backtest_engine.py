"""Bar-by-bar backtesting engine with trailing stop execution and market hours filtering."""

from __future__ import annotations

from datetime import time as dtime

import numpy as np
import pandas as pd
import pytz

from squeeze_surge.backtest.trade import Trade
from squeeze_surge.backtest.backtest_result import BacktestResult
from squeeze_surge.backtest import metrics
from squeeze_surge.strategy.position_sizer import PositionSizer

ET = pytz.timezone("America/New_York")
MARKET_OPEN = dtime(9, 30)
MARKET_CLOSE = dtime(16, 0)
ETF_LONG_ONLY = {"SPY", "QQQ"}

REQUIRED_COLUMNS = [
    "signal",
    "entry_price",
    "stop_loss",
    "trail_stop_pct",
    "exit_signal",
    "close",
    "high",
    "low",
]


class BacktestEngine:
    """Simulates trade execution bar-by-bar.

    Features
    --------
    - Trailing stop: tracks highest price (using *high*) since entry,
      exits when close < peak × (1 − trail_stop_pct).
    - Stop-loss-before-trail priority: if both trigger on the same bar,
      stop_loss wins (conservative).
    - Market hours filter: for 1Hour data, only process bars between
      09:30–16:00 ET.
    - SPY / QQQ long-only: short signals are skipped for ETFs.
    - One position at a time per symbol.
    """

    def __init__(self, initial_balance: float = 10_000, risk_pct: float = 0.01) -> None:
        self.initial_balance = initial_balance
        self.risk_pct = risk_pct
        self.sizer = PositionSizer()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(self, symbol: str, df: pd.DataFrame, timeframe: str = "1Day") -> BacktestResult:
        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        df = df.copy().reset_index(drop=True)

        balance = self.initial_balance
        equity_curve: list[float] = [balance]
        equity_data: list[tuple[any, float]] = [(df["time"].iloc[0], balance)]
        trades: list[Trade] = []
        position: Trade | None = None
        highest_price: float = 0.0
        consec_neg_mom_delta = 0

        for row in df.itertuples():
            idx = row.Index

            # --- Market hours filter (1Hour only) ---
            if timeframe == "1Hour" and not self._in_market_hours(row):
                equity_curve.append(balance)
                equity_data.append((row.time, balance))
                continue

            # --- If we have an open position, check exits ---
            if position is not None:
                exit_price, exit_reason = self._check_exits(
                    position, row, highest_price
                )

                # Track consecutive negative momentum_delta for momentum exit
                mom_delta = getattr(row, "momentum_delta", None)
                if mom_delta is not None and mom_delta < 0:
                    consec_neg_mom_delta += 1
                else:
                    consec_neg_mom_delta = 0

                if exit_reason == "":
                    # Check momentum exit: 2 consecutive negative bars
                    if consec_neg_mom_delta >= 2:
                        exit_price = row.close
                        exit_reason = "momentum_exit"

                if exit_reason:
                    bar_time = getattr(row, "time", None)
                    position.close(exit_price, bar_time, exit_reason)
                    balance += position.pnl
                    trades.append(position)
                    position = None
                    highest_price = 0.0
                    consec_neg_mom_delta = 0
                else:
                    # Update trailing peak
                    highest_price = max(highest_price, row.high)

                equity_curve.append(balance)
                equity_data.append((row.time, balance))
                continue

            # --- No position: look for entry signal ---
            signal = int(row.signal)
            if signal == 0:
                equity_curve.append(balance)
                equity_data.append((row.time, balance))
                continue

            # ETF long-only rule
            if signal == -1 and symbol in ETF_LONG_ONLY:
                equity_curve.append(balance)
                equity_data.append((row.time, balance))
                continue

            entry_price = row.close
            stop_loss = row.stop_loss
            trail_pct = row.trail_stop_pct

            if pd.isna(stop_loss) or pd.isna(trail_pct):
                equity_curve.append(balance)
                equity_data.append((row.time, balance))
                continue

            # Position sizing
            try:
                shares = self.sizer.calculate(balance, self.risk_pct, entry_price, stop_loss)
            except ValueError:
                equity_curve.append(balance)
                equity_data.append((row.time, balance))
                continue

            if shares <= 0:
                equity_curve.append(balance)
                equity_data.append((row.time, balance))
                continue

            direction = "long" if signal == 1 else "short"
            bar_time = getattr(row, "time", None)

            position = Trade(
                symbol=symbol,
                direction=direction,
                entry_price=entry_price,
                entry_time=bar_time,
                shares=shares,
                stop_loss=stop_loss,
                trail_stop_pct=trail_pct,
            )
            highest_price = row.high
            consec_neg_mom_delta = 0
            equity_curve.append(balance)
            equity_data.append((row.time, balance))

        # --- End of data: close any open position ---
        if position is not None:
            last_row = df.iloc[-1]
            bar_time = last_row.get("time", None)
            position.close(last_row["close"], bar_time, "end_of_data")
            balance += position.pnl
            trades.append(position)
            equity_curve.append(balance)
            equity_data.append((bar_time, balance))

        # --- Compute metrics ---
        eq = np.array(equity_curve)
        daily_returns = np.diff(eq) / eq[:-1] if len(eq) > 1 else np.array([])
        # Filter out zero-change days for cleaner Sharpe
        daily_returns = daily_returns[daily_returns != 0] if len(daily_returns) > 0 else daily_returns

        return BacktestResult(
            symbol=symbol,
            total_trades=len(trades),
            win_rate=metrics.win_rate(trades),
            sharpe=metrics.sharpe_ratio(daily_returns),
            max_drawdown=metrics.max_drawdown(eq),
            profit_factor=metrics.profit_factor(trades),
            final_balance=round(balance, 2),
            return_pct=round((balance - self.initial_balance) / self.initial_balance * 100, 2),
            trades=trades,
            equity_curve=equity_data,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _in_market_hours(row) -> bool:
        """Return True if the bar falls within regular market hours (ET)."""
        ts = getattr(row, "time", None)
        if ts is None:
            return True
        try:
            if hasattr(ts, "tzinfo") and ts.tzinfo is not None:
                et_time = ts.astimezone(ET).time()
            else:
                et_time = ET.localize(ts).time()
            return MARKET_OPEN <= et_time < MARKET_CLOSE
        except Exception:
            return True

    @staticmethod
    def _check_exits(
        position: Trade, row, highest_price: float
    ) -> tuple[float, str]:
        """Check stop-loss and trailing-stop conditions.

        Returns (exit_price, exit_reason).  Empty reason = no exit.
        Stop-loss takes priority over trailing stop.
        """
        close = row.close
        low = row.low

        # --- Fixed stop loss ---
        if position.direction == "long" and low <= position.stop_loss:
            return position.stop_loss, "stop_loss"
        if position.direction == "short" and row.high >= position.stop_loss:
            return position.stop_loss, "stop_loss"

        # --- Trailing stop ---
        peak = max(highest_price, row.high)
        if position.direction == "long":
            trail_level = peak * (1 - position.trail_stop_pct)
            if close < trail_level:
                return close, "trail_stop"
        else:  # short — track lowest price
            trough = min(highest_price, row.low) if highest_price > 0 else row.low
            trail_level = trough * (1 + position.trail_stop_pct)
            if close > trail_level:
                return close, "trail_stop"

        return 0.0, ""
