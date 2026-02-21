"""Signal generator — fires entries on squeeze release with momentum + volume confirmation."""

import numpy as np
import pandas as pd

REQUIRED_INDICATOR_COLUMNS = [
    "squeeze_on",
    "squeeze_bars",
    "momentum",
    "momentum_delta",
    "volume_ratio",
    "bb_upper",
    "bb_lower",
    "close",
    "high",
    "low",
]

MIN_SQUEEZE_BARS = 3
VOLUME_RATIO_THRESHOLD = 1.2
ATR_STOP_MULT = 2.0
TRAIL_STOP_PCT = 0.05  # 5 %


class SignalGenerator:
    """Generates long / short entry signals during active squeeze on BB breakout.

    Entry rules (ENTRY_MODE = 'continuation')
    -----------------------------------------
    LONG:  squeeze_on == True
           AND squeeze_bars >= min_squeeze_bars
           AND close > bb_upper (breakout while squeeze active)
           AND momentum > 0
           AND momentum_delta > 0 (acceleration)
           AND volume_ratio > threshold

    SHORT: mirror with close < bb_lower, momentum < 0, momentum_delta < 0

    Columns added
    -------------
    signal          : int  (1 = long, -1 = short, 0 = none)
    signal_type     : str  ('long', 'short', '')
    entry_price     : float (close of signal bar, NaN if no signal)
    stop_loss       : float (entry ∓ ATR×2, NaN if no signal)
    trail_stop_pct  : float (0.05 on signal bars, NaN otherwise)
    exit_signal     : int  (1 = exit, 0 = hold)
    """

    ENTRY_MODE = "continuation"

    def __init__(
        self,
        min_squeeze_bars: int = MIN_SQUEEZE_BARS,
        volume_ratio_threshold: float = VOLUME_RATIO_THRESHOLD,
    ) -> None:
        self.min_squeeze_bars = min_squeeze_bars
        self.volume_ratio_threshold = volume_ratio_threshold

    def generate(self, symbol: str, df: pd.DataFrame) -> pd.DataFrame:
        missing = [c for c in REQUIRED_INDICATOR_COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        df = df.copy()

        # --- ATR (reuse true-range logic from Keltner) ---
        prev_close = df["close"].shift(1)
        tr = pd.concat(
            [
                df["high"] - df["low"],
                (df["high"] - prev_close).abs(),
                (df["low"] - prev_close).abs(),
            ],
            axis=1,
        ).max(axis=1)
        atr = tr.rolling(window=20).mean()

        # --- Squeeze active detection ---
        # We enter MULTIPLE times during a squeeze if conditions hold? 
        # No, BacktestEngine handles "one position at a time".
        squeeze_active = df["squeeze_on"] == True
        enough_bars = df["squeeze_bars"] >= self.min_squeeze_bars

        # --- Confirmation filters ---
        long_cond = (
            squeeze_active
            & enough_bars
            & (df["close"] > df["bb_upper"])
            & (df["momentum"] > 0)
            & (df["momentum_delta"] > 0)
            & (df["volume_ratio"] > self.volume_ratio_threshold)
        )

        short_cond = (
            squeeze_active
            & enough_bars
            & (df["close"] < df["bb_lower"])
            & (df["momentum"] < 0)
            & (df["momentum_delta"] < 0)
            & (df["volume_ratio"] > self.volume_ratio_threshold)
        )

        # --- Build signal columns ---
        df["signal"] = 0
        df.loc[long_cond, "signal"] = 1
        df.loc[short_cond, "signal"] = -1

        df["signal_type"] = ""
        df.loc[long_cond, "signal_type"] = "long"
        df.loc[short_cond, "signal_type"] = "short"

        df["entry_price"] = np.nan
        df.loc[df["signal"] != 0, "entry_price"] = df.loc[
            df["signal"] != 0, "close"
        ]

        df["stop_loss"] = np.nan
        long_mask = df["signal"] == 1
        short_mask = df["signal"] == -1
        df.loc[long_mask, "stop_loss"] = (
            df.loc[long_mask, "entry_price"] - ATR_STOP_MULT * atr[long_mask]
        )
        df.loc[short_mask, "stop_loss"] = (
            df.loc[short_mask, "entry_price"] + ATR_STOP_MULT * atr[short_mask]
        )

        df["trail_stop_pct"] = np.nan
        df.loc[df["signal"] != 0, "trail_stop_pct"] = TRAIL_STOP_PCT

        # --- Exit signals ---
        # Exit when momentum_delta turns negative for 2 consecutive bars after entry
        df["exit_signal"] = 0
        neg_mom_delta = df["momentum_delta"] < 0
        consec_neg = neg_mom_delta & neg_mom_delta.shift(1).fillna(False)

        # Only mark exits after the most recent signal
        signal_indices = df.index[df["signal"] != 0].tolist()
        for sig_idx in signal_indices:
            after_entry = df.index > sig_idx
            exit_candidates = df.index[after_entry & consec_neg]
            if len(exit_candidates) > 0:
                df.loc[exit_candidates[0], "exit_signal"] = 1

        # --- Validation: stop_loss sanity ---
        longs_with_stop = df[long_mask & df["stop_loss"].notna()]
        if not longs_with_stop.empty and (
            longs_with_stop["stop_loss"] >= longs_with_stop["entry_price"]
        ).any():
            raise ValueError("stop_loss must be < entry_price for long signals")

        shorts_with_stop = df[short_mask & df["stop_loss"].notna()]
        if not shorts_with_stop.empty and (
            shorts_with_stop["stop_loss"] <= shorts_with_stop["entry_price"]
        ).any():
            raise ValueError("stop_loss must be > entry_price for short signals")

        return df
