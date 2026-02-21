"""Tests for DataStore."""

import pandas as pd
import pytest

from squeeze_surge.data.data_store import DataStore


@pytest.fixture
def store(tmp_path):
    """DataStore backed by a temporary directory."""
    return DataStore(data_dir=tmp_path)


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "time": pd.date_range("2024-01-01", periods=5, freq="D"),
        "open": [100.0, 101.0, 102.0, 103.0, 104.0],
        "high": [101.0, 102.0, 103.0, 104.0, 105.0],
        "low": [99.0, 100.0, 101.0, 102.0, 103.0],
        "close": [100.5, 101.5, 102.5, 103.5, 104.5],
        "volume": [1_000_000, 1_100_000, 1_200_000, 1_300_000, 1_400_000],
    })


class TestSaveAndLoadRoundtrip:
    def test_roundtrip(self, store, sample_df):
        store.save("AAPL", "1Day", sample_df)
        loaded = store.load("AAPL", "1Day")

        pd.testing.assert_frame_equal(loaded, sample_df)


class TestExistsFalseWhenMissing:
    def test_not_exists(self, store):
        assert store.exists("UNKNOWN", "1Day") is False

    def test_exists_after_save(self, store, sample_df):
        assert store.exists("AAPL", "1Day") is False
        store.save("AAPL", "1Day", sample_df)
        assert store.exists("AAPL", "1Day") is True
