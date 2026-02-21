"""Tests for the data pipeline."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pandas as pd
import pytest

from squeeze_surge.data.data_store import DataStore
from squeeze_surge.pipeline import run_pipeline


def _fake_df(n: int = 10) -> pd.DataFrame:
    return pd.DataFrame({
        "time": pd.date_range("2024-01-01", periods=n, freq="D"),
        "open": range(n),
        "high": range(n),
        "low": range(n),
        "close": range(n),
        "volume": range(n),
    })


class TestRunPipelineCreatesAllFiles:
    def test_creates_all_parquet_files(self, tmp_path):
        symbols = ["TEST1", "TEST2"]
        timeframes = ["1Day", "1Hour"]

        mock_client = MagicMock()
        mock_client.get_bars.return_value = _fake_df(10)

        store = DataStore(data_dir=tmp_path)

        results = run_pipeline(
            symbols=symbols,
            timeframes=timeframes,
            years=1,
            client=mock_client,
            store=store,
        )

        # Should have 2 symbols × 2 timeframes = 4 files
        parquet_files = list(tmp_path.glob("*.parquet"))
        assert len(parquet_files) == 4

        # Check all keys present
        expected_keys = {"TEST1_1Day", "TEST1_1Hour", "TEST2_1Day", "TEST2_1Hour"}
        assert set(results.keys()) == expected_keys

        # All should have 10 rows
        for key, count in results.items():
            assert count == 10

        # Verify files are loadable
        for symbol in symbols:
            for tf in timeframes:
                assert store.exists(symbol, tf)
                df = store.load(symbol, tf)
                assert len(df) == 10
