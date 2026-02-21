"""Volume Ratio indicator."""

import pandas as pd

REQUIRED_COLUMNS = ["open", "high", "low", "close", "volume"]


class VolumeRatio:
    """Current volume relative to rolling average.

    Adds column: volume_ratio (values > 1.5 indicate a volume surge)
    """

    def __init__(self, period: int = 20) -> None:
        self.period = period

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add volume_ratio column to *df* and return it."""
        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        df = df.copy()
        avg_volume = df["volume"].rolling(window=self.period).mean()
        df["volume_ratio"] = df["volume"] / avg_volume
        return df
