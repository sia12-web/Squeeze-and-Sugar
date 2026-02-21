"""Single-symbol grid-search optimiser with IS/OOS validation."""

from __future__ import annotations

import logging

import pandas as pd

from squeeze_surge.data.data_store import DataStore
from squeeze_surge.indicators.indicator_engine import IndicatorEngine
from squeeze_surge.strategy.signal_generator import SignalGenerator
from squeeze_surge.backtest.backtest_engine import BacktestEngine
from squeeze_surge.optimization.param_grid import generate_combos
from squeeze_surge.optimization.optimization_result import OptimizationResult

logger = logging.getLogger(__name__)

# Validation gates
PRIMARY_SHARPE_GATE = 0.5
PRIMARY_WIN_RATE_GATE = 0.45
PRIMARY_MIN_TRADES = 10

FALLBACK_SHARPE_GATE = 0.25
FALLBACK_WIN_RATE_GATE = 0.40
FALLBACK_MIN_TRADES = 10


class Optimizer:
    """Grid-search over indicator parameters for a single symbol.

    Uses a chronological train/test (IS/OOS) split.
    """

    def __init__(
        self,
        symbol: str,
        timeframe: str = "1Hour",
        data_split: float = 0.7,
    ) -> None:
        self.symbol = symbol
        self.timeframe = timeframe
        self.data_split = data_split

    def run(self) -> OptimizationResult:
        # Load raw OHLCV
        store = DataStore()
        df_raw = store.load(self.symbol, self.timeframe)

        # Keep only core OHLCV columns to avoid stale indicator leftovers
        ohlcv_cols = ["time", "open", "high", "low", "close", "volume"]
        df_raw = df_raw[[c for c in ohlcv_cols if c in df_raw.columns]].copy()

        # Chronological IS / OOS split
        split_idx = int(len(df_raw) * self.data_split)
        df_is = df_raw.iloc[:split_idx].copy().reset_index(drop=True)
        df_oos = df_raw.iloc[split_idx:].copy().reset_index(drop=True)

        combos = generate_combos()
        best_sharpe = -999.0
        best_params: dict = {}
        best_is_result = None

        logger.info(
            "%s: searching %d param combos (IS=%d bars, OOS=%d bars)",
            self.symbol, len(combos), len(df_is), len(df_oos),
        )

        for combo in combos:
            try:
                sharpe = self._evaluate(self.symbol, df_is, combo, self.timeframe)
                if sharpe > best_sharpe:
                    best_sharpe = sharpe
                    best_params = combo.copy()
            except Exception:
                continue

        if not best_params:
            logger.warning("%s: no valid param combo found", self.symbol)
            return OptimizationResult(symbol=self.symbol)

        # Validate on OOS
        oos_result = self._backtest(self.symbol, df_oos, best_params, self.timeframe)

        passed = (
            oos_result.sharpe >= PRIMARY_SHARPE_GATE
            and oos_result.win_rate >= PRIMARY_WIN_RATE_GATE
            and oos_result.total_trades >= PRIMARY_MIN_TRADES
        )

        # Fallback gate
        if not passed:
            passed = (
                oos_result.sharpe >= FALLBACK_SHARPE_GATE
                and oos_result.win_rate >= FALLBACK_WIN_RATE_GATE
                and oos_result.total_trades >= FALLBACK_MIN_TRADES
            )

        logger.info(
            "%s: best IS Sharpe=%.2f | OOS Sharpe=%.2f WR=%.1f%% trades=%d → %s",
            self.symbol, best_sharpe, oos_result.sharpe,
            oos_result.win_rate * 100, oos_result.total_trades,
            "PASS" if passed else "FAIL",
        )

        return OptimizationResult(
            symbol=self.symbol,
            best_params=best_params,
            in_sample_sharpe=round(best_sharpe, 4),
            out_of_sample_sharpe=round(oos_result.sharpe, 4),
            out_of_sample_win_rate=round(oos_result.win_rate, 4),
            out_of_sample_profit_factor=round(oos_result.profit_factor, 4),
            total_trades=oos_result.total_trades,
            passed_validation=passed,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _evaluate(symbol: str, df: pd.DataFrame, params: dict, timeframe: str = "1Hour") -> float:
        """Run indicator + signal + backtest pipeline and return Sharpe.
        
        Requires at least 10 trades to be considered valid for IS optimization.
        """
        result = Optimizer._backtest(symbol, df, params, timeframe)
        if result.total_trades < 10:
            return -999.0
        return result.sharpe

    @staticmethod
    def _backtest(symbol: str, df: pd.DataFrame, params: dict, timeframe: str = "1Hour"):
        """Full pipeline for a param combo on a data slice."""
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
        df_ind = ie.run(symbol, timeframe, df.copy())

        sg = SignalGenerator(
            min_squeeze_bars=params["min_squeeze_bars"],
            volume_ratio_threshold=params.get("volume_ratio_threshold", 1.2),
        )
        df_sig = sg.generate(symbol, df_ind)

        bt = BacktestEngine(initial_balance=10_000, risk_pct=0.01)
        return bt.run(symbol, df_sig, timeframe=timeframe)
