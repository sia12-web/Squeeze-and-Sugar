"""Alpaca Data API v2 client for fetching historical bars."""

import time
from datetime import datetime

import pandas as pd
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

from squeeze_surge.config import config

TIMEFRAME_MAP = {
    "1Day": TimeFrame.Day,
    "1Hour": TimeFrame.Hour,
}


class AlpacaClient:
    """Wraps Alpaca's StockHistoricalDataClient for OHLCV bar retrieval."""

    def __init__(self, api_key: str | None = None, secret_key: str | None = None):
        self._client = StockHistoricalDataClient(
            api_key=api_key or config.alpaca_api_key,
            secret_key=secret_key or config.alpaca_secret_key,
        )

    def get_bars(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> pd.DataFrame:
        """Fetch OHLCV bars from Alpaca Data API v2.

        Args:
            symbol: Ticker symbol (e.g. "AAPL").
            timeframe: One of "1Day" or "1Hour".
            start: Start datetime (inclusive).
            end: End datetime (exclusive).

        Returns:
            DataFrame with columns [time, open, high, low, close, volume].
        """
        tf = TIMEFRAME_MAP.get(timeframe)
        if tf is None:
            raise ValueError(f"Unsupported timeframe: {timeframe}. Use one of {list(TIMEFRAME_MAP)}")

        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=tf,
            start=start,
            end=end,
            feed="iex",
        )

        bars_response = self._client.get_stock_bars(request)

        # Alpaca returns a dict keyed by symbol
        bars = bars_response[symbol]

        if not bars:
            return pd.DataFrame(columns=["time", "open", "high", "low", "close", "volume"])

        df = pd.DataFrame([b.model_dump() for b in bars])

        # Normalise columns
        df = df.rename(columns={"timestamp": "time"})
        df = df[["time", "open", "high", "low", "close", "volume"]]

        return df
