"""Tests for AlpacaClient."""

import os
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from squeeze_surge.data.alpaca_client import AlpacaClient


class FakeBar:
    """Mimics an Alpaca Bar object with model_dump()."""

    def __init__(self, data: dict):
        self._data = data

    def model_dump(self) -> dict:
        return self._data


def _make_fake_bars(symbol: str, n: int = 3) -> dict:
    """Build a fake Alpaca bars response dict."""
    bars = []
    for i in range(n):
        bars.append(FakeBar({
            "timestamp": datetime(2024, 1, 1 + i, tzinfo=timezone.utc),
            "open": 100.0 + i,
            "high": 101.0 + i,
            "low": 99.0 + i,
            "close": 100.5 + i,
            "volume": 1_000_000 + i * 1000,
            "trade_count": 500,
            "vwap": 100.2 + i,
        }))
    return {symbol: bars}


class TestGetBarsReturnsCorrectColumns:
    """test_get_bars_returns_correct_columns — mock Alpaca, assert columns."""

    @patch("squeeze_surge.data.alpaca_client.StockHistoricalDataClient")
    def test_columns(self, MockClientClass):
        mock_instance = MockClientClass.return_value
        mock_instance.get_stock_bars.return_value = _make_fake_bars("AAPL", 3)

        client = AlpacaClient(api_key="fake", secret_key="fake")
        df = client.get_bars(
            "AAPL",
            "1Day",
            datetime(2024, 1, 1, tzinfo=timezone.utc),
            datetime(2024, 1, 4, tzinfo=timezone.utc),
        )

        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ["time", "open", "high", "low", "close", "volume"]
        assert len(df) == 3


@pytest.mark.skipif(
    not os.path.exists(os.path.join(os.path.dirname(__file__), "..", ".env")),
    reason="No .env file with Alpaca credentials",
)
class TestGetBarsAaplLive:
    """test_get_bars_aapl_live — real API call, skip without .env."""

    def test_live_fetch(self):
        client = AlpacaClient()
        end = datetime.now(timezone.utc)
        start = end - pd.Timedelta(days=7)

        df = client.get_bars("AAPL", "1Day", start, end)

        assert len(df) > 0
        assert not df.isnull().any().any()
        assert list(df.columns) == ["time", "open", "high", "low", "close", "volume"]
