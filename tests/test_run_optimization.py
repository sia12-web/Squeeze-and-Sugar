"""Tests for run_all_symbols."""

import json
from pathlib import Path
from unittest.mock import patch

from squeeze_surge.optimization.run_optimization import run_all_symbols
from squeeze_surge.optimization.optimization_result import OptimizationResult


def test_output_file_created(tmp_path):
    """Mocked optimization should create the JSON output file."""
    mock_result_dict = OptimizationResult(
        symbol="TEST", best_params={"bb_period": 20},
        in_sample_sharpe=1.0, out_of_sample_sharpe=0.5,
        out_of_sample_win_rate=0.5, out_of_sample_profit_factor=2.0,
        total_trades=10, passed_validation=True,
    ).to_dict()

    output_path = tmp_path / "optimization_results.json"

    with patch(
        "squeeze_surge.optimization.run_optimization._optimize_symbol",
        return_value=mock_result_dict,
    ):
        results = run_all_symbols(
            symbols=["TEST"],
            output_path=output_path,
            parallel=False,
            run_diagnostics_first=False,
        )

    assert output_path.exists()
    with open(output_path) as f:
        data = json.load(f)
    assert "TEST" in data
    assert data["TEST"]["passed_validation"] is True
