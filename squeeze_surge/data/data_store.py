"""Parquet-based data storage for OHLCV bars."""

from pathlib import Path

import pandas as pd

from squeeze_surge.config import config


class DataStore:
    """Saves and loads DataFrames as parquet files under data/."""

    def __init__(self, data_dir: Path | None = None):
        self.data_dir = data_dir or config.data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, symbol: str, timeframe: str) -> Path:
        return self.data_dir / f"{symbol}_{timeframe}.parquet"

    def save(self, symbol: str, timeframe: str, df: pd.DataFrame) -> Path:
        """Save DataFrame to parquet. Returns the file path."""
        path = self._path(symbol, timeframe)
        df.to_parquet(path, index=False, engine="pyarrow")
        return path

    def load(self, symbol: str, timeframe: str) -> pd.DataFrame:
        """Load DataFrame from parquet."""
        path = self._path(symbol, timeframe)
        if not path.exists():
            raise FileNotFoundError(f"No data file found: {path}")
        return pd.read_parquet(path, engine="pyarrow")

    def exists(self, symbol: str, timeframe: str) -> bool:
        """Check whether a parquet file exists for the given symbol/timeframe."""
        return self._path(symbol, timeframe).exists()
