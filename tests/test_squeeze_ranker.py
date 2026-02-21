"""Tests for SqueezeRanker."""

import pandas as pd

from squeeze_surge.strategy.squeeze_ranker import SqueezeRanker


def _make_squeeze_df(squeeze_bars_end: int, n: int = 60) -> pd.DataFrame:
    """Build a DataFrame with indicator columns and a squeeze run ending at the last bar."""
    close = [100 + i * 0.5 for i in range(n)]
    df = pd.DataFrame(
        {
            "open": [c - 0.1 for c in close],
            "high": [c + 2.0 for c in close],
            "low": [c - 2.0 for c in close],
            "close": close,
            "volume": [1000] * n,
        }
    )

    # Simulate indicator columns
    df["squeeze_on"] = False
    df["squeeze_bars"] = 0
    df["momentum"] = 5.0
    df["volume_ratio"] = 1.2

    # Put a squeeze run at the tail
    for i in range(1, squeeze_bars_end + 1):
        idx = n - squeeze_bars_end - 1 + i
        if idx < n:
            df.loc[idx, "squeeze_on"] = True
            df.loc[idx, "squeeze_bars"] = i

    return df


def test_longer_squeeze_scores_higher():
    ranker = SqueezeRanker()
    score_10 = ranker.rank("TEST", _make_squeeze_df(10))["squeeze_score"]
    score_3 = ranker.rank("TEST", _make_squeeze_df(3))["squeeze_score"]
    assert score_10 > score_3, f"10-bar squeeze ({score_10}) should outscore 3-bar ({score_3})"
