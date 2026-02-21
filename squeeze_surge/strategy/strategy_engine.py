"""Strategy engine — orchestrates indicator calculation, ranking, and signal generation."""

import pandas as pd

from squeeze_surge.indicators.indicator_engine import IndicatorEngine
from squeeze_surge.strategy.squeeze_ranker import SqueezeRanker
from squeeze_surge.strategy.signal_generator import SignalGenerator


class StrategyEngine:
    """Top-level orchestrator: indicators → ranker → signals.

    Usage::

        engine = StrategyEngine()
        df = engine.run("AAPL", "1Day", raw_df)
    """

    def __init__(self, symbol_configs: dict | None = None, min_squeeze_bars: int = 3, 
                 volume_ratio_threshold: float = 1.2) -> None:
        self.indicator_engine = IndicatorEngine(symbol_configs=symbol_configs)
        self.ranker = SqueezeRanker()
        self.signal_gen = SignalGenerator(
            min_squeeze_bars=min_squeeze_bars,
            volume_ratio_threshold=volume_ratio_threshold
        )

    def run(
        self, symbol: str, timeframe: str, df: pd.DataFrame
    ) -> pd.DataFrame:
        """Apply indicators then generate signals. Returns enriched DataFrame."""
        # 1. Compute all indicator columns
        df = self.indicator_engine.run(symbol, timeframe, df)

        # 2. Generate entry / exit signals
        df = self.signal_gen.generate(symbol, df)

        return df

    def rank(self, symbol: str, df: pd.DataFrame) -> dict:
        """Return squeeze quality score dict (call after indicators are computed)."""
        return self.ranker.rank(symbol, df)
