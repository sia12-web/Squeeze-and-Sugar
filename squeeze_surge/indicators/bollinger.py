"""Bollinger Bands indicator."""

import pandas as pd

REQUIRED_COLUMNS = ["open", "high", "low", "close", "volume"]


class BollingerBands:
    """Calculates Bollinger Bands (SMA ± N standard deviations).

    Adds columns: bb_upper, bb_middle, bb_lower, bb_width
    """

    def __init__(self, period: int = 20, std_dev: float = 2.0) -> None:
        self.period = period
        self.std_dev = std_dev

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add Bollinger Band columns to *df* and return it."""
        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        df = df.copy()
        df["bb_middle"] = df["close"].rolling(window=self.period).mean()
        rolling_std = df["close"].rolling(window=self.period).std()
        df["bb_upper"] = df["bb_middle"] + self.std_dev * rolling_std
        df["bb_lower"] = df["bb_middle"] - self.std_dev * rolling_std
        df["bb_width"] = df["bb_upper"] - df["bb_lower"]
        return df
