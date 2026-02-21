"""Fetches latest bars and applies indicators."""

import logging
import pandas as pd
import pytz
from datetime import time as dtime
from squeeze_surge.data.alpaca_client import AlpacaClient
from squeeze_surge.indicators.indicator_engine import IndicatorEngine

logger = logging.getLogger(__name__)

ET = pytz.timezone("America/New_York")
MARKET_OPEN = dtime(9, 30)
MARKET_CLOSE = dtime(16, 0)

class CandleFetcher:
    """Handles real-time data fetching and processing."""

    def __init__(self, optimized_params: dict):
        self.client = AlpacaClient()
        self.optimized_params = optimized_params

    def fetch_latest(self, symbol: str, timeframe: str = "1Hour", bars: int = 100) -> pd.DataFrame:
        """Fetch bars, apply indicators, and filter by market hours."""
        try:
            # 1. Fetch raw bars
            df = self.client.fetch_ohlcv(symbol, timeframe, bars=bars)
            if df.empty:
                return pd.DataFrame()

            # 2. Get params for this symbol
            symbol_opt = self.optimized_params.get(symbol, {})
            # Use optimized if available, else defaults
            params = {
                "bb_period": symbol_opt.get("best_params", {}).get("bb_period", 20),
                "bb_std": symbol_opt.get("best_params", {}).get("bb_std", 2.0),
                "kc_period": symbol_opt.get("best_params", {}).get("kc_period", 20),
                "kc_atr_mult": symbol_opt.get("best_params", {}).get("kc_atr_mult", 1.5),
                "momentum_period": symbol_opt.get("best_params", {}).get("momentum_period", 12),
                "volume_ratio_period": 20
            }

            # 3. Apply indicators
            ie = IndicatorEngine(symbol_configs={symbol: params})
            df_ind = ie.run(symbol, timeframe, df)

            # 4. Filter to market hours (conservative - only trade when market is open)
            df_filtered = self._filter_market_hours(df_ind)
            return df_filtered

        except Exception as e:
            logger.error("Failed to fetch/process data for %s: %s", symbol, e)
            return pd.DataFrame()

    def _filter_market_hours(self, df: pd.DataFrame) -> pd.DataFrame:
        """Keep only rows within 09:30-16:00 ET."""
        if df.empty:
            return df
            
        def is_open(ts):
            if hasattr(ts, "tzinfo") and ts.tzinfo is not None:
                et_time = ts.astimezone(ET).time()
            else:
                et_time = ET.localize(ts).time()
            return MARKET_OPEN <= et_time < MARKET_CLOSE

        mask = df["time"].apply(is_open)
        return df[mask].copy()
