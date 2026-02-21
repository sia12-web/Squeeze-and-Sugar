"""Indicator engine — applies all indicators to an OHLCV DataFrame."""

import pandas as pd

from squeeze_surge.indicators.bollinger import BollingerBands
from squeeze_surge.indicators.keltner import KeltnerChannels
from squeeze_surge.indicators.squeeze import SqueezeDetector
from squeeze_surge.indicators.momentum import Momentum
from squeeze_surge.indicators.volume_ratio import VolumeRatio
from squeeze_surge.indicators.symbol_configs import SYMBOL_CONFIGS

REQUIRED_COLUMNS = ["open", "high", "low", "close", "volume"]

INDICATOR_COLUMNS = [
    "bb_upper",
    "bb_middle",
    "bb_lower",
    "bb_width",
    "kc_upper",
    "kc_middle",
    "kc_lower",
    "squeeze_on",
    "squeeze_bars",
    "momentum",
    "momentum_delta",
    "volume_ratio",
]


class IndicatorEngine:
    """Orchestrates all indicator calculations for a given symbol.

    Parameters
    ----------
    symbol_configs : dict, optional
        Per-symbol parameter overrides.  Falls back to ``SYMBOL_CONFIGS``.
    """

    def __init__(self, symbol_configs: dict | None = None) -> None:
        self.symbol_configs = symbol_configs or SYMBOL_CONFIGS

    def run(self, symbol: str, timeframe: str, df: pd.DataFrame) -> pd.DataFrame:
        """Apply all 5 indicators and return the enriched DataFrame.

        Parameters
        ----------
        symbol : str
            Ticker symbol (e.g. ``"AAPL"``).
        timeframe : str
            Timeframe label (``"1Day"`` or ``"1Hour"``).  Currently unused but
            reserved for future per-timeframe parameter tuning.
        df : pd.DataFrame
            Raw OHLCV DataFrame.

        Returns
        -------
        pd.DataFrame
            DataFrame with all 12 indicator columns appended.
        """
        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        cfg = self.symbol_configs.get(symbol, self.symbol_configs.get("SPY", {}))

        # 1. Bollinger Bands
        bb = BollingerBands(
            period=cfg.get("bb_period", 20),
            std_dev=cfg.get("bb_std", 2.0),
        )
        df = bb.calculate(df)

        # 2. Keltner Channels
        kc = KeltnerChannels(
            period=cfg.get("kc_period", 20),
            atr_mult=cfg.get("kc_atr_mult", 1.5),
        )
        df = kc.calculate(df)

        # 3. Squeeze Detection (uses existing BB/KC columns)
        sq = SqueezeDetector(
            bb_period=cfg.get("bb_period", 20),
            bb_std=cfg.get("bb_std", 2.0),
            kc_period=cfg.get("kc_period", 20),
            kc_atr_mult=cfg.get("kc_atr_mult", 1.5),
        )
        df = sq.calculate(df)

        # 4. Momentum
        mom = Momentum(period=cfg.get("momentum_period", 12))
        df = mom.calculate(df)

        # 5. Volume Ratio
        vr = VolumeRatio(period=cfg.get("volume_ratio_period", 20))
        df = vr.calculate(df)

        return df
