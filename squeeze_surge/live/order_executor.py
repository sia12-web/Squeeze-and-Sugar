"""Paper trade execution recorder."""

import json
import logging
import threading
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class OrderExecutor:
    """Records paper trades to a local JSON file."""

    def __init__(self, paper_save_path: Path):
        self.save_path = paper_save_path
        self._lock = threading.Lock()
        
    def record_paper_trade(self, symbol: str, signal: int, entry_price: float, 
                           stop_loss: float, trail_stop_pct: float, shares: int):
        """Append a paper trade entry to the JSON file using thread-safe locking."""
        direction = "long" if signal == 1 else "short"
        
        entry = {
            "symbol": symbol,
            "direction": direction,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "trail_stop_pct": trail_stop_pct,
            "shares": shares,
            "timestamp": datetime.now().isoformat(),
            "mode": "paper"
        }
        
        with self._lock:
            try:
                trades = []
                if self.save_path.exists():
                    with open(self.save_path, "r") as f:
                        trades = json.load(f)
                
                trades.append(entry)
                
                with open(self.save_path, "w") as f:
                    json.dump(trades, f, indent=2)
                
                logger.info("Recorded paper trade for %s: %s at %s", symbol, direction, entry_price)
            except Exception as e:
                logger.error("Failed to record paper trade for %s: %s", symbol, e)
