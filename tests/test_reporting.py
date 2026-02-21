"""Tests for the reporting module."""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from squeeze_surge.reporting.report_data import ReportData
from squeeze_surge.reporting.chart_builder import ChartBuilder
from squeeze_surge.reporting.html_renderer import HTMLRenderer
from squeeze_surge.backtest.backtest_result import BacktestResult


def test_collect_returns_all_symbols():
    """Mock backtest, assert all 10 symbols in output."""
    symbols = ["AAPL", "MSFT", "TSLA", "NVDA", "AMZN", "META", "GOOGL", "AMD", "SPY", "QQQ"]
    
    mock_result = BacktestResult(
        symbol="TEST", total_trades=5, win_rate=0.6, sharpe=2.0,
        max_drawdown=0.1, profit_factor=2.0, final_balance=11000,
        return_pct=10.0, trades=[], equity_curve=[("2023-01-01", 10000), ("2023-01-02", 11000)]
    )

    with patch("squeeze_surge.reporting.report_data.DataStore"), \
         patch("squeeze_surge.reporting.report_data.IndicatorEngine"), \
         patch("squeeze_surge.reporting.report_data.SignalGenerator"), \
         patch("squeeze_surge.reporting.report_data.BacktestEngine.run", return_value=mock_result), \
         patch("squeeze_surge.reporting.report_data.config") as mock_config:
        
        mock_config.watchlist = symbols
        mock_config.data_dir = Path("data")
        
        rd = ReportData()
        output = rd.collect(symbols=symbols)
        
        assert len(output["symbols"]) == 10
        assert "AAPL" in output["symbols"]
        assert "QQQ" in output["symbols"]
        assert output["summary"]["total_trades"] == 50  # 10 symbols * 5 trades


def test_equity_curve_has_x_and_y():
    """Assert dict has 'x' and 'y' keys equal length."""
    equity_data = [("2023-01-01", 10000), ("2023-01-02", 10500)]
    cb = ChartBuilder()
    result = cb.equity_curve(equity_data)
    
    assert "x" in result
    assert "y" in result
    assert len(result["x"]) == len(result["y"]) == 2
    assert result["y"][0] == 10000


def test_squeeze_funnel_has_all_stages():
    """Assert all filter stages present in funnel chart data."""
    diagnostics = {
        "total": 1000, "market_hours": 800, "squeeze_active": 100,
        "breakout_during_squeeze": 20, "momentum_confirmed": 10,
        "volume_confirmed": 5, "final_signals": 5
    }
    result = ChartBuilder.squeeze_funnel(diagnostics)
    
    assert len(result["x"]) == 7
    assert "Squeeze Active" in result["x"]
    assert result["y"][0] == 1000


def test_render_produces_valid_html():
    """Assert output starts with <!DOCTYPE html>."""
    renderer = HTMLRenderer()
    mock_data = {
        "summary": {"validated_symbols": [], "total_trades": 0, "avg_win_rate": 0, "best_symbol": ""},
        "symbols": {},
        "all_trades": []
    }
    html = renderer.render(mock_data)
    assert html.strip().startswith("<!DOCTYPE html>")


def test_render_contains_aapl():
    """Assert 'AAPL' appears in rendered HTML."""
    renderer = HTMLRenderer()
    mock_data = {
        "summary": {"validated_symbols": ["AAPL"], "total_trades": 10, "avg_win_rate": 0.6, "best_symbol": "AAPL"},
        "symbols": {
            "AAPL": {
                "symbol": "AAPL", "passed_validation": True, "params": {},
                "metrics": {"sharpe": 2.0, "win_rate": 0.6, "profit_factor": 2.0, "return_pct": 10.0, "total_trades": 10, "final_balance": 11000},
                "equity_curve": [], "trades": [], "diagnostics": {}
            }
        },
        "all_trades": []
    }
    html = renderer.render(mock_data)
    assert "AAPL" in html
    assert "VALIDATED" in html
