"""Tests for CandleFetcher."""

import pandas as pd
import pytz
from datetime import datetime
from unittest.mock import patch, MagicMock
from squeeze_surge.live.candle_fetcher import CandleFetcher

def test_market_hours_filter_applied():
    """Mock Alpaca response with pre-market bars, assert filtered out."""
    # 08:30 is pre-market, 10:30 is market hours
    tz = pytz.timezone("America/New_York")
    
    # Use naive datetimes for construction and localize them
    times = [
        datetime(2023, 1, 1, 8, 30), 
        datetime(2023, 1, 1, 10, 30),
        datetime(2023, 1, 1, 16, 30)
    ]
    
    mock_df = pd.DataFrame({
        "time": times,
        "open": [100, 101, 102],
        "high": [105, 106, 107],
        "low": [95, 96, 97],
        "close": [100, 101, 102],
        "volume": [1000, 1100, 1200]
    })
    
    with patch("squeeze_surge.live.candle_fetcher.AlpacaClient") as MockClient:
        instance = MockClient.return_value
        instance.fetch_ohlcv.return_value = mock_df
        
        fetcher = CandleFetcher(optimized_params={})
        result = fetcher.fetch_latest("AAPL")
        
        # Should only contain 10:30 ET
        assert len(result) == 1
        # Check that it's the 10:30 one
        # Note: Depending on how _filter_market_hours handles localization, we check hours
        # In our implementation it converts to ET then checks time
        # 10:30 is the second row
        assert result.iloc[0]["open"] == 101
