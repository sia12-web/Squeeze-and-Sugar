"""Tests for FilterCounter."""

from squeeze_surge.diagnostics.filter_counter import FilterCounter, STAGE_KEYS


def test_squeeze_active_stage_present():
    """Assert 'squeeze_active' is in STAGE_KEYS and 'squeeze_release' is gone."""
    assert "squeeze_active" in STAGE_KEYS
    assert "squeeze_release" not in STAGE_KEYS
    assert "breakout_during_squeeze" in STAGE_KEYS


def test_returns_all_stage_keys():
    """Output dict should have all expected stage keys."""
    fc = FilterCounter()
    # Run on real AAPL 1Hour data (already fetched)
    result = fc.run("AAPL", "1Hour")
    assert set(result.keys()) == set(STAGE_KEYS)


def test_each_stage_lte_previous():
    """Counts should be monotonically decreasing through the filter stages."""
    fc = FilterCounter()
    result = fc.run("AAPL", "1Hour")

    ordered = [result[k] for k in STAGE_KEYS]
    for i in range(1, len(ordered)):
        assert ordered[i] <= ordered[i - 1], (
            f"{STAGE_KEYS[i]} ({ordered[i]}) > {STAGE_KEYS[i-1]} ({ordered[i-1]})"
        )
