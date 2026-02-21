"""Momentum indicator."""

import pandas as pd

REQUIRED_COLUMNS = ["open", "high", "low", "close", "volume"]


class Momentum:
    """Simple momentum and its first derivative.

    Adds columns: momentum, momentum_delta
    """

    def __init__(self, period: int = 12) -> None:
        self.period = period

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add momentum columns to *df* and return it."""
        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        df = df.copy()
        df["momentum"] = df["close"] - df["close"].shift(self.period)
        df["momentum_delta"] = df["momentum"] - df["momentum"].shift(1)
        return df
