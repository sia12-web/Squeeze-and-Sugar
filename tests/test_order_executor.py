"""Tests for OrderExecutor."""

import json
from pathlib import Path
from squeeze_surge.live.order_executor import OrderExecutor

def test_paper_trade_appended(tmp_path):
    """Call record_paper_trade(), assert entry in data/paper_trades.json."""
    save_path = tmp_path / "paper_trades.json"
    executor = OrderExecutor(save_path)
    
    executor.record_paper_trade("AAPL", 1, 180.0, 175.0, 0.05, 10)
    
    assert save_path.exists()
    with open(save_path) as f:
        data = json.load(f)
        assert len(data) == 1
        assert data[0]["symbol"] == "AAPL"
        assert data[0]["direction"] == "long"
        assert data[0]["entry_price"] == 180.0
        assert data[0]["mode"] == "paper"

    # Second trade
    executor.record_paper_trade("NVDA", -1, 500.0, 510.0, 0.03, 5)
    with open(save_path) as f:
        data = json.load(f)
        assert len(data) == 2
        assert data[1]["symbol"] == "NVDA"
        assert data[1]["direction"] == "short"
