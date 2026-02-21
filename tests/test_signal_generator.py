"""Tests for SignalGenerator."""

import numpy as np
import pandas as pd
import pytest

from squeeze_surge.strategy.signal_generator import SignalGenerator, VOLUME_RATIO_THRESHOLD


def _base_df(n: int = 60) -> pd.DataFrame:
    """Create a base OHLCV+indicator DataFrame with no signals firing."""
    close = [100.0 + i * 0.5 for i in range(n)]
    df = pd.DataFrame(
        {
            "open": [c - 0.1 for c in close],
            "high": [c + 2.0 for c in close],
            "low": [c - 2.0 for c in close],
            "close": close,
            "volume": [1000] * n,
        }
    )
    df["bb_upper"] = [c + 3.0 for c in close]
    df["bb_lower"] = [c - 3.0 for c in close]
    df["bb_middle"] = close
    df["bb_width"] = 6.0
    df["kc_upper"] = [c + 5.0 for c in close]
    df["kc_lower"] = [c - 5.0 for c in close]
    df["kc_middle"] = close
    df["squeeze_on"] = False
    df["squeeze_bars"] = 0
    df["momentum"] = 0.0
    df["momentum_delta"] = 0.0
    df["volume_ratio"] = 1.0
    df["time"] = pd.date_range("2023-01-01", periods=n, freq="min")
    return df


def _setup_long_signal(df: pd.DataFrame, bar_idx: int, squeeze_bars: int = 5,
                       volume_ratio: float = 2.0, squeeze_on_target: bool = True) -> pd.DataFrame:
    """Set up conditions for a long signal at *bar_idx*."""
    df = df.copy()
    # Squeeze active for preceding bars and target bar
    for i in range(1, squeeze_bars + 1):
        idx = bar_idx - squeeze_bars + i
        if 0 <= idx < len(df):
            df.loc[idx, "squeeze_on"] = True
            df.loc[idx, "squeeze_bars"] = i

    # Squeeze active on bar_idx? (Phase 5C logic)
    df.loc[bar_idx, "squeeze_on"] = squeeze_on_target
    if squeeze_on_target:
        df.loc[bar_idx, "squeeze_bars"] = squeeze_bars

    # Close breaks above bb_upper
    df.loc[bar_idx, "close"] = df.loc[bar_idx, "bb_upper"] + 1.0

    # Positive momentum + acceleration
    df.loc[bar_idx, "momentum"] = 5.0
    df.loc[bar_idx, "momentum_delta"] = 1.0

    # Volume surge
    df.loc[bar_idx, "volume_ratio"] = volume_ratio

    return df


def test_entry_mode_is_continuation():
    assert SignalGenerator.ENTRY_MODE == "continuation"


def test_long_signal_during_active_squeeze():
    """LONG should fire when price breaks up while squeeze is active."""
    df = _setup_long_signal(_base_df(), bar_idx=40, squeeze_bars=4, squeeze_on_target=True)
    result = SignalGenerator(min_squeeze_bars=3).generate("TEST", df)
    assert result.loc[40, "signal"] == 1


def test_no_signal_when_squeeze_off():
    """No signal if squeeze_on is False, even if price breaks out."""
    df = _setup_long_signal(_base_df(), bar_idx=40, squeeze_bars=4, squeeze_on_target=False)
    result = SignalGenerator(min_squeeze_bars=3).generate("TEST", df)
    assert result.loc[40, "signal"] == 0


def test_no_signal_below_min_squeeze_bars():
    """No signal if squeeze has not lasted long enough."""
    df = _setup_long_signal(_base_df(), bar_idx=40, squeeze_bars=2, squeeze_on_target=True)
    result = SignalGenerator(min_squeeze_bars=3).generate("TEST", df)
    assert result.loc[40, "signal"] == 0


def test_stop_loss_below_entry_for_long():
    df = _setup_long_signal(_base_df(), bar_idx=40)
    result = SignalGenerator().generate("TEST", df)
    longs = result[result["signal"] == 1]
    assert not longs.empty
    valid = longs.dropna(subset=["stop_loss", "entry_price"])
    assert (valid["stop_loss"] < valid["entry_price"]).all()


def test_volume_threshold_is_1_2():
    # This checks the module constant, but SignalGenerator now takes it in __init__
    from squeeze_surge.strategy.signal_generator import VOLUME_RATIO_THRESHOLD
    assert VOLUME_RATIO_THRESHOLD == 1.2
