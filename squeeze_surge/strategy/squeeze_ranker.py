"""Squeeze quality ranker — scores how much energy is stored in a squeeze."""

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = [
    "squeeze_on",
    "squeeze_bars",
    "momentum",
    "volume_ratio",
    "close",
]


class SqueezeRanker:
    """Scores squeeze quality for dashboard / ranking display.

    Score = squeeze_bars × 10
          + avg volume_ratio during squeeze × 5
          + normalised |momentum| (0-10)
    """

    def rank(self, symbol: str, df: pd.DataFrame) -> dict:
        """Return a quality-score dict for the most recent squeeze state."""
        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        last = df.iloc[-1]

        # Current squeeze length (from the last row)
        sq_bars = int(last["squeeze_bars"])

        # Average volume_ratio during the current/most-recent squeeze run
        if last["squeeze_on"]:
            run = df.tail(max(sq_bars, 1))
        else:
            # Look back to the most recent squeeze run
            sq_mask = df["squeeze_on"]
            if sq_mask.any():
                last_sq_end = sq_mask[::-1].idxmax()
                sq_len = int(df.loc[last_sq_end, "squeeze_bars"]) or 1
                run = df.loc[last_sq_end - sq_len + 1 : last_sq_end]
                sq_bars = sq_len
            else:
                run = df.tail(1)

        vol_ratio_avg = float(run["volume_ratio"].mean()) if not run.empty else 1.0

        # Normalise |momentum| to 0-10 using the column's own range
        mom_abs = df["momentum"].dropna().abs()
        if mom_abs.max() > 0:
            mom_norm = float(abs(last["momentum"]) / mom_abs.max() * 10)
        else:
            mom_norm = 0.0

        squeeze_score = sq_bars * 10 + vol_ratio_avg * 5 + mom_norm

        return {
            "symbol": symbol,
            "squeeze_score": round(squeeze_score, 2),
            "squeeze_bars": sq_bars,
            "squeeze_on": bool(last["squeeze_on"]),
            "last_close": float(last["close"]),
        }
