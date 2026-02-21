"""Tests for startup check logic."""

from unittest.mock import patch, MagicMock
from pathlib import Path
from squeeze_surge.live.startup_check import run_startup_check

def test_fails_if_parquet_missing(tmp_path):
    """Mock missing 1Hour file, assert returns False."""
    # We need to patch config.data_dir to point to our tmp_path
    with patch("squeeze_surge.live.startup_check.config") as mock_config:
        mock_config.data_dir = tmp_path
        
        # Scenario 1: Missing optimization_results.json
        assert run_startup_check() is False
        
        # Create it
        (tmp_path / "optimization_results.json").write_text("{}")
        
        # Scenario 2: Missing 1Hour directory/parquet
        assert run_startup_check() is False
        
        # Create directory but no files
        (tmp_path / "1Hour").mkdir()
        assert run_startup_check() is False
        
        # Create file
        (tmp_path / "1Hour" / "AAPL.parquet").write_text("data")
        
        # Scenario 3: Alpaca connectivity test
        with patch("squeeze_surge.live.startup_check.AlpacaClient") as MockClient:
            client = MockClient.return_value
            # Empty DF fails
            client.fetch_ohlcv.return_value = MagicMock(empty=True)
            assert run_startup_check() is False
            
            # Non-empty DF but missing API keys
            client.fetch_ohlcv.return_value = MagicMock(empty=False)
            mock_config.alpaca_api_key = None
            assert run_startup_check() is False
            
            # All set
            mock_config.alpaca_api_key = "key"
            mock_config.alpaca_secret_key = "secret"
            assert run_startup_check() is True
