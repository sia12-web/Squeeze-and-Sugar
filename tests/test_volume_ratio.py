"""Tests for VolumeRatio indicator."""

import pandas as pd

from squeeze_surge.indicators.volume_ratio import VolumeRatio


def test_volume_ratio_above_one_on_surge():
    """A bar with 3× average volume should have volume_ratio > 1.5."""
    n = 30
    volumes = [1000] * n
    # Spike on the last bar
    volumes[-1] = 3000

    close = [100 + i * 0.1 for i in range(n)]
    df = pd.DataFrame(
        {
            "open": [c - 0.1 for c in close],
            "high": [c + 0.5 for c in close],
            "low": [c - 0.5 for c in close],
            "close": close,
            "volume": volumes,
        }
    )

    df = VolumeRatio(period=20).calculate(df)
    last_ratio = df.iloc[-1]["volume_ratio"]
    assert last_ratio > 1.5, f"Expected volume_ratio > 1.5, got {last_ratio}"
