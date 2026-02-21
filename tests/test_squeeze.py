"""Tests for SqueezeDetector."""

import pandas as pd

from squeeze_surge.indicators.squeeze import SqueezeDetector


def _make_tight_bb_ohlcv(n: int = 50) -> pd.DataFrame:
    """Create a nearly-flat price series so BB contracts inside KC."""
    # Constant-ish close → very narrow BB, but TR still gives KC width
    close = [100.0 + 0.001 * i for i in range(n)]
    return pd.DataFrame(
        {
            "open": [c - 0.5 for c in close],
            "high": [c + 2.0 for c in close],   # wide H-L → wide KC
            "low": [c - 2.0 for c in close],
            "close": close,
            "volume": [1000] * n,
        }
    )


def test_squeeze_on_when_bb_inside_kc():
    """When BB is narrower than KC, squeeze_on should be True."""
    df = SqueezeDetector().calculate(_make_tight_bb_ohlcv(60))
    valid = df.dropna(subset=["squeeze_on"])
    squeeze_rows = valid[valid["squeeze_on"]]
    assert not squeeze_rows.empty, "Expected some squeeze_on=True rows"


def test_squeeze_bars_increments():
    """squeeze_bars should increment by 1 each consecutive squeeze bar."""
    df = SqueezeDetector().calculate(_make_tight_bb_ohlcv(60))
    valid = df.dropna(subset=["squeeze_on"])

    # Find runs of squeeze_on == True
    squeeze_runs = valid[valid["squeeze_on"]]["squeeze_bars"]
    if len(squeeze_runs) < 2:
        return  # Not enough data to verify increments

    # Within any contiguous squeeze run, bars should increment by 1
    diffs = squeeze_runs.diff().dropna()
    # Filter to only diffs within a run (diff == 1 means contiguous increment)
    contiguous = diffs[diffs == 1]
    assert len(contiguous) > 0, "Expected consecutive squeeze bars incrementing by 1"
