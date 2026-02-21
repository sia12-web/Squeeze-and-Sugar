"""Tests for trade mode logic."""

import json
from pathlib import Path
from squeeze_surge.live.trade_mode import get_trade_modes

def test_all_symbols_return_paper(tmp_path):
    """Assert all symbols return 'paper' regardless of validation status in JSON."""
    results_path = tmp_path / "optimization_results.json"
    
    # Mock results: AAPL passed, MSFT failed
    mock_data = {
        "AAPL": {"passed_validation": True},
        "MSFT": {"passed_validation": False}
    }
    
    with open(results_path, "w") as f:
        json.dump(mock_data, f)
        
    modes = get_trade_modes(results_path)
    
    assert modes["AAPL"] == "paper"
    assert modes["MSFT"] == "paper"
    assert len(modes) == 2
