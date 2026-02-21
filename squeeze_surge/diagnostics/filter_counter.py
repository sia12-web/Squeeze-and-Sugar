"""Filter counter — counts bars passing each signal stage for diagnosing signal rarity."""

from __future__ import annotations

import json
import logging
from datetime import time as dtime
from pathlib import Path

import pandas as pd
import pytz

from squeeze_surge.data.data_store import DataStore
from squeeze_surge.indicators.indicator_engine import IndicatorEngine
from squeeze_surge.strategy.signal_generator import VOLUME_RATIO_THRESHOLD

logger = logging.getLogger(__name__)

ET = pytz.timezone("America/New_York")
MARKET_OPEN = dtime(9, 30)
MARKET_CLOSE = dtime(16, 0)

STAGE_KEYS = [
    "total",
    "market_hours",
    "squeeze_on",
    "squeeze_active",
    "breakout_during_squeeze",
    "momentum_confirmed",
    "volume_confirmed",
    "final_signals",
]


class FilterCounter:
    """Counts how many bars pass each stage of the signal filter.

    Useful for diagnosing why signal frequency is low.
    """

    def run(self, symbol: str, timeframe: str = "1Hour") -> dict[str, int]:
        store = DataStore()
        df = store.load(symbol, timeframe)

        # Strip to OHLCV then recompute indicators with defaults
        ohlcv_cols = ["time", "open", "high", "low", "close", "volume"]
        df = df[[c for c in ohlcv_cols if c in df.columns]].copy()

        ie = IndicatorEngine()
        df = ie.run(symbol, timeframe, df)

        counts: dict[str, int] = {}

        # Total bars
        counts["total"] = len(df)

        # Market hours filter (1Hour only)
        if timeframe == "1Hour":
            mask_hours = df["time"].apply(self._in_market_hours)
            df_mh = df[mask_hours].copy()
        else:
            df_mh = df.copy()
        counts["market_hours"] = len(df_mh)

        # Squeeze on
        counts["squeeze_on"] = int(df_mh["squeeze_on"].sum())

        # Squeeze active (squeeze_on == True AND squeeze_bars >= 3)
        enough_bars = df_mh["squeeze_bars"] >= 3
        squeeze_active = df_mh["squeeze_on"] & enough_bars
        counts["squeeze_active"] = int(squeeze_active.sum())

        # Breakout during squeeze (close > bb_upper for longs OR close < bb_lower for shorts)
        breakout = (
            squeeze_active
            & ((df_mh["close"] > df_mh["bb_upper"]) | (df_mh["close"] < df_mh["bb_lower"]))
        )
        counts["breakout_during_squeeze"] = int(breakout.sum())

        # Momentum confirmed
        mom_long = (df_mh["momentum"] > 0) & (df_mh["momentum_delta"] > 0)
        mom_short = (df_mh["momentum"] < 0) & (df_mh["momentum_delta"] < 0)
        momentum_ok = breakout & (mom_long | mom_short)
        counts["momentum_confirmed"] = int(momentum_ok.sum())

        # Volume confirmed
        volume_ok = momentum_ok & (df_mh["volume_ratio"] > VOLUME_RATIO_THRESHOLD)
        counts["volume_confirmed"] = int(volume_ok.sum())

        # Final signals = volume confirmed (all conditions met)
        counts["final_signals"] = counts["volume_confirmed"]

        return counts

    @staticmethod
    def _in_market_hours(ts) -> bool:
        try:
            if hasattr(ts, "tzinfo") and ts.tzinfo is not None:
                et_time = ts.astimezone(ET).time()
            else:
                et_time = ET.localize(ts).time()
            return MARKET_OPEN <= et_time < MARKET_CLOSE
        except Exception:
            return True

    def run_all(
        self,
        symbols: list[str],
        timeframe: str = "1Hour",
        output_path: Path | None = None,
    ) -> dict[str, dict[str, int]]:
        """Run diagnostics for all symbols and optionally save to JSON."""
        results: dict[str, dict[str, int]] = {}
        for sym in symbols:
            results[sym] = self.run(sym, timeframe)

        # Print table
        header = f"{'Symbol':<8}" + "".join(f"{k:>18}" for k in STAGE_KEYS)
        logger.info(header)
        logger.info("-" * len(header))
        for sym, counts in results.items():
            row = f"{sym:<8}" + "".join(f"{counts[k]:>18}" for k in STAGE_KEYS)
            logger.info(row)

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(results, f, indent=2)

        return results
