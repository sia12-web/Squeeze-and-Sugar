"""Keltner Channels indicator."""

import pandas as pd

REQUIRED_COLUMNS = ["open", "high", "low", "close", "volume"]


class KeltnerChannels:
    """Calculates Keltner Channels (EMA ± ATR multiplier).

    Adds columns: kc_upper, kc_middle, kc_lower
    """

    def __init__(self, period: int = 20, atr_mult: float = 1.5) -> None:
        self.period = period
        self.atr_mult = atr_mult

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add Keltner Channel columns to *df* and return it."""
        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        df = df.copy()

        # True Range
        prev_close = df["close"].shift(1)
        tr = pd.concat(
            [
                df["high"] - df["low"],
                (df["high"] - prev_close).abs(),
                (df["low"] - prev_close).abs(),
            ],
            axis=1,
        ).max(axis=1)

        atr = tr.rolling(window=self.period).mean()

        # Middle = EMA (standard TTM Squeeze uses EMA)
        df["kc_middle"] = df["close"].ewm(span=self.period, adjust=False).mean()
        df["kc_upper"] = df["kc_middle"] + self.atr_mult * atr
        df["kc_lower"] = df["kc_middle"] - self.atr_mult * atr
        return df
