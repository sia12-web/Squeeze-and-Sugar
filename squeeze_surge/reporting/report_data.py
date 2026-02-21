"""Reporting data collection — aggregates results for all symbols."""

import json
import logging
from pathlib import Path

import pandas as pd
from squeeze_surge.config import config
from squeeze_surge.data.data_store import DataStore
from squeeze_surge.backtest.backtest_engine import BacktestEngine
from squeeze_surge.indicators.indicator_engine import IndicatorEngine
from squeeze_surge.strategy.signal_generator import SignalGenerator
from squeeze_surge.optimization.optimization_result import OptimizationResult

logger = logging.getLogger(__name__)


class ReportData:
    """Collects metrics, equity curves, and optimization stats for the dashboard."""

    def __init__(self, timeframe: str = "1Hour"):
        self.timeframe = timeframe
        self.data_dir = config.data_dir

    def collect(self, symbols: list[str] | None = None) -> dict:
        """Run backtests using optimized params and assemble full report data."""
        symbols = symbols or config.watchlist
        opt_path = self.data_dir / "optimization_results.json"
        diag_path = self.data_dir / "diagnostics.json"

        # Load optimization results
        opt_results = {}
        if opt_path.exists():
            with open(opt_path) as f:
                opt_results = json.load(f)

        # Load diagnostics
        diagnostics = {}
        if diag_path.exists():
            with open(diag_path) as f:
                diagnostics = json.load(f)

        symbol_reports = {}
        all_trades = []
        combined_equity = []

        for symbol in symbols:
            logger.info("Collecting report data for %s...", symbol)
            
            # 1. Get parameters (optimized or default)
            opt_entry = opt_results.get(symbol, {})
            passed_validation = opt_entry.get("passed_validation", False)
            params = opt_entry.get("best_params", {
                "bb_period": 20, "bb_std": 2.0,
                "kc_period": 20, "kc_atr_mult": 1.5,
                "momentum_period": 12, "min_squeeze_bars": 3,
                "volume_ratio_threshold": 1.2
            })

            # 2. Run Backtest on FULL data
            store = DataStore()
            df_ohlcv = store.load(symbol, self.timeframe)
            
            # Re-run indicator + signal pipeline
            symbol_cfg = {
                symbol: {
                    "bb_period": params["bb_period"],
                    "bb_std": params["bb_std"],
                    "kc_period": params["kc_period"],
                    "kc_atr_mult": params["kc_atr_mult"],
                    "momentum_period": params["momentum_period"],
                    "volume_ratio_period": 20,
                }
            }
            ie = IndicatorEngine(symbol_configs=symbol_cfg)
            df_ind = ie.run(symbol, self.timeframe, df_ohlcv)
            
            sg = SignalGenerator(
                min_squeeze_bars=params["min_squeeze_bars"],
                volume_ratio_threshold=params.get("volume_ratio_threshold", 1.2)
            )
            df_sig = sg.generate(symbol, df_ind)
            
            bt = BacktestEngine(initial_balance=10_000, risk_pct=0.01)
            result = bt.run(symbol, df_sig, timeframe=self.timeframe)

            # 3. Compile symbol report
            symbol_reports[symbol] = {
                "symbol": symbol,
                "passed_validation": passed_validation,
                "params": params,
                "metrics": {
                    "total_trades": result.total_trades,
                    "win_rate": result.win_rate,
                    "sharpe": result.sharpe,
                    "max_drawdown": result.max_drawdown,
                    "profit_factor": result.profit_factor,
                    "return_pct": result.return_pct,
                    "final_balance": result.final_balance,
                },
                "equity_curve": [(t.isoformat() if hasattr(t, "isoformat") else str(t), b) for t, b in result.equity_curve],
                "trades": [self._trade_to_dict(t) for t in result.trades],
                "diagnostics": diagnostics.get(symbol, {}),
            }
            
            all_trades.extend(result.trades)

        # 4. Global KPIs
        validated = [s for s, r in symbol_reports.items() if r["passed_validation"]]
        total_trades = sum(r["metrics"]["total_trades"] for r in symbol_reports.values())
        avg_wr = (sum(r["metrics"]["win_rate"] for r in symbol_reports.values() if r["metrics"]["total_trades"] > 0) / 
                  len([r for r in symbol_reports.values() if r["metrics"]["total_trades"] > 0])) if total_trades > 0 else 0
        
        best_sym = ""
        best_sharpe = -999.0
        for s, r in symbol_reports.items():
            if r["metrics"]["sharpe"] > best_sharpe:
                best_sharpe = r["metrics"]["sharpe"]
                best_sym = s

        return {
            "summary": {
                "validated_symbols": validated,
                "total_trades": total_trades,
                "avg_win_rate": avg_wr,
                "best_symbol": best_sym,
            },
            "symbols": symbol_reports,
            "all_trades": [self._trade_to_dict(t) for t in all_trades],
        }

    @staticmethod
    def _trade_to_dict(trade) -> dict:
        return {
            "symbol": trade.symbol,
            "direction": trade.direction,
            "entry_time": trade.entry_time.isoformat() if trade.entry_time else "",
            "entry_price": trade.entry_price,
            "exit_time": trade.exit_time.isoformat() if trade.exit_time else "",
            "exit_price": trade.exit_price,
            "pnl": trade.pnl,
            "pnl_pct": trade.pnl_pct,
            "exit_reason": trade.exit_reason,
            "shares": trade.shares,
        }
