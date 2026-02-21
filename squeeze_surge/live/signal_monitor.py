import time
import json
import logging
import schedule
import pandas as pd
from pathlib import Path
from squeeze_surge.config import config
from squeeze_surge.strategy.strategy_engine import StrategyEngine
from squeeze_surge.live.candle_fetcher import CandleFetcher

logger = logging.getLogger(__name__)

class SignalMonitor:
    """Orchestrates polling, signal generation, and callbacks/alerts."""

    def __init__(self, symbols: list[str], optimized_params: dict, trade_modes: dict,
                 poll_interval_seconds: int = 300,
                 order_executor=None, notifier=None):
        self.symbols = symbols
        self.optimized_params = optimized_params
        self.trade_modes = trade_modes
        self.poll_interval = poll_interval_seconds
        self.order_executor = order_executor
        self.notifier = notifier
        self.fetcher = CandleFetcher(optimized_params)
        self.log_path = config.data_dir / "signal_log.jsonl"

    def _job(self):
        """Single poll iteration for all symbols."""
        logger.info("Polling Alpaca for signals...")
        
        for symbol in self.symbols:
            # 1. Fetch data
            df = self.fetcher.fetch_latest(symbol)
            if df.empty or len(df) < 2:
                continue
                
            # 2. Setup StrategyEngine with symbol-specific params
            symbol_opt = self.optimized_params.get(symbol, {})
            best_params = symbol_opt.get("best_params", {})
            
            # Extract strategy-specific params
            min_squeeze = best_params.get("min_squeeze_bars", 3)
            vol_thresh = best_params.get("volume_ratio_threshold", 1.2)
            
            # Indicator overrides
            symbol_cfg = {
                symbol: {
                    "bb_period": best_params.get("bb_period", 20),
                    "bb_std": best_params.get("bb_std", 2.0),
                    "kc_period": best_params.get("kc_period", 20),
                    "kc_atr_mult": best_params.get("kc_atr_mult", 1.5),
                    "momentum_period": best_params.get("momentum_period", 12),
                }
            }
            
            engine = StrategyEngine(
                symbol_configs=symbol_cfg,
                min_squeeze_bars=min_squeeze,
                volume_ratio_threshold=vol_thresh
            )
            
            # 3. Generate Signals
            df_sig = engine.run(symbol, "1Hour", df)
            
            # 4. Check the LATEST bar for a signal
            last_bar = df_sig.iloc[-1]
            signal = int(last_bar.get("signal", 0))
            
            if signal != 0:
                self._handle_signal(symbol, signal, last_bar)

    def _handle_signal(self, symbol, signal, last_bar):
        """Execute trade logic and notify Telegram."""
        mode = self.trade_modes.get(symbol, "paper")
        direction = "long" if signal == 1 else "short"
        entry_price = last_bar["close"]
        stop_loss = last_bar["stop_loss"]
        trail_pct = last_bar["trail_stop_pct"]
        
        # Simple position sizing for paper: mock 1% risk on $10k
        from squeeze_surge.strategy.position_sizer import PositionSizer
        sizer = PositionSizer()
        try:
            shares = sizer.calculate(10000, 0.01, entry_price, stop_loss)
        except:
            shares = 10
            
        logger.info("NEW SIGNAL: %s %s @ %s", symbol, direction.upper(), entry_price)
        
        # 1. Log to JSONL (Phase 7 requirement)
        log_entry = {
            "timestamp": last_bar["time"].isoformat() if hasattr(last_bar["time"], "isoformat") else str(last_bar["time"]),
            "symbol": symbol,
            "direction": direction,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "trail_pct": trail_pct,
            "mode": mode
        }
        with open(self.log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        # 2. Record (Always Paper per Phase 7 requirements)
        if self.order_executor:
            self.order_executor.record_paper_trade(
                symbol, signal, entry_price, stop_loss, trail_pct, shares
            )
            
        # Notify
        if self.notifier:
            self.notifier.send_signal(symbol, direction, entry_price, stop_loss, trail_pct, mode)

    def run(self):
        """Start the infinite polling loop."""
        # Run once immediately on start
        self._job()
        
        schedule.every(self.poll_interval).seconds.do(self._job)
        
        logger.info("Signal Monitor running. Polling every %d seconds.", self.poll_interval)
        while True:
            schedule.run_pending()
            time.sleep(1)
