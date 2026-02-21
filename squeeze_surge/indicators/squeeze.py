"""TTM Squeeze detector."""

import pandas as pd

from squeeze_surge.indicators.bollinger import BollingerBands
from squeeze_surge.indicators.keltner import KeltnerChannels


class SqueezeDetector:
    """Detects TTM Squeeze: Bollinger Bands entirely inside Keltner Channels.

    Adds columns: squeeze_on (bool), squeeze_bars (int)
    """

    def __init__(
        self,
        bb_period: int = 20,
        bb_std: float = 2.0,
        kc_period: int = 20,
        kc_atr_mult: float = 1.5,
    ) -> None:
        self.bb = BollingerBands(period=bb_period, std_dev=bb_std)
        self.kc = KeltnerChannels(period=kc_period, atr_mult=kc_atr_mult)

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add squeeze columns to *df* and return it.

        squeeze_on: True when BB is entirely inside KC (bands pinching).
        squeeze_bars: consecutive bars the squeeze has been active (resets on release).
        """
        # Ensure BB and KC columns exist
        if "bb_upper" not in df.columns:
            df = self.bb.calculate(df)
        if "kc_upper" not in df.columns:
            df = self.kc.calculate(df)

        df = df.copy()

        # Squeeze is ON when BB sits inside KC
        df["squeeze_on"] = (df["bb_upper"] < df["kc_upper"]) & (
            df["bb_lower"] > df["kc_lower"]
        )

        # Count consecutive squeeze bars (reset when squeeze_on is False)
        squeeze_group = (~df["squeeze_on"]).cumsum()
        df["squeeze_bars"] = (
            df.groupby(squeeze_group)["squeeze_on"]
            .cumcount()
        )
        # When squeeze is off, squeeze_bars should be 0
        df.loc[~df["squeeze_on"], "squeeze_bars"] = 0

        return df
