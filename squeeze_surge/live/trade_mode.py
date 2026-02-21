"""Determines trade mode for symbols."""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def get_trade_modes(results_path: Path) -> dict[str, str]:
    """Returns 'paper' for all symbols regardless of validation.
    
    Squeeze and Surge is currently paper-only until AAPL validates 
    over a statistically significant live sample (e.g., 20+ trades).
    """
    modes = {}
    
    # Load optimization results to see what symbols are in the watchlist
    if results_path.exists():
        with open(results_path) as f:
            data = json.load(f)
            for symbol in data.keys():
                # TODO: Implement promotion logic (e.g., if passed_validation and live_trades >= 20)
                modes[symbol] = "paper"
    
    return modes
