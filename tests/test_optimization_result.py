"""Tests for OptimizationResult serialisation."""

from squeeze_surge.optimization.optimization_result import OptimizationResult


def test_json_roundtrip():
    """Serialise → deserialise should produce an equal result."""
    orig = OptimizationResult(
        symbol="AAPL",
        best_params={"bb_period": 20, "bb_std": 2.0, "kc_period": 15},
        in_sample_sharpe=1.5,
        out_of_sample_sharpe=0.8,
        out_of_sample_win_rate=0.55,
        out_of_sample_profit_factor=2.1,
        total_trades=12,
        passed_validation=True,
    )
    json_str = orig.to_json()
    restored = OptimizationResult.from_json(json_str)

    assert restored.symbol == orig.symbol
    assert restored.best_params == orig.best_params
    assert restored.in_sample_sharpe == orig.in_sample_sharpe
    assert restored.out_of_sample_sharpe == orig.out_of_sample_sharpe
    assert restored.passed_validation == orig.passed_validation
