"""Run optimisation for all symbols and save results to JSON."""

from __future__ import annotations

import json
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from squeeze_surge.config import config
from squeeze_surge.optimization.optimizer import Optimizer
from squeeze_surge.optimization.optimization_result import OptimizationResult

logger = logging.getLogger(__name__)


def _optimize_symbol(symbol: str, timeframe: str = "1Hour") -> dict:
    """Worker function — runs in a child process."""
    result = Optimizer(symbol, timeframe=timeframe).run()
    return result.to_dict()


def run_all_symbols(
    symbols: list[str] | None = None,
    max_workers: int = 4,
    output_path: Path | None = None,
    parallel: bool = True,
    timeframe: str = "1Hour",
    run_diagnostics_first: bool = True,
) -> dict[str, dict]:
    """Grid-search all symbols and save results.

    Args:
        parallel: Use ProcessPoolExecutor when True (default).
        timeframe: '1Hour' (default) or '1Day'.
        run_diagnostics_first: If True, skip symbols with < 3 signals in IS period.

    Returns dict mapping symbol → OptimizationResult (as dict).
    """
    from squeeze_surge.diagnostics.filter_counter import FilterCounter
    from squeeze_surge.data.data_store import DataStore
    
    symbols = symbols or config.watchlist
    output_path = output_path or (config.data_dir / "optimization_results.json")

    # --- Diagnostics Gate ---
    if run_diagnostics_first:
        logger.info("Running diagnostics first...")
        fc = FilterCounter()
        viable_symbols = []
        for sym in symbols:
            # We check IS period signals. IS is roughly 70%.
            store = DataStore()
            df_full = store.load(sym, timeframe)
            split_idx = int(len(df_full) * 0.7)
            # FilterCounter doesn't currently take a DF, but we can pass one if we update it
            # Or we can just run it on full data as a proxy.
            # For simplicity and speed, let's run it on the full data for now, 
            # as a symbol with <3 signals total definitely won't have 3 in IS.
            counts = fc.run(sym, timeframe)
            # Gate on 3 signals to allow optimizer to find 10+ with better params
            if counts["final_signals"] < 3:
                logger.warning("%s: too few signals (%d), skipping optimization", sym, counts["final_signals"])
            else:
                viable_symbols.append(sym)
        
        symbols = viable_symbols

    results: dict[str, dict] = {}

    if not symbols:
        logger.warning("No symbols passed diagnostics. Aborting.")
        return {}

    if parallel:
        with ProcessPoolExecutor(max_workers=max_workers) as pool:
            futures = {pool.submit(_optimize_symbol, sym, timeframe): sym for sym in symbols}
            for future in as_completed(futures):
                sym = futures[future]
                try:
                    results[sym] = future.result()
                except Exception:
                    logger.exception("Optimization failed for %s", sym)
                    results[sym] = OptimizationResult(symbol=sym).to_dict()
    else:
        for sym in symbols:
            try:
                results[sym] = _optimize_symbol(sym, timeframe)
            except Exception:
                logger.exception("Optimization failed for %s", sym)
                results[sym] = OptimizationResult(symbol=sym).to_dict()

    # Save to JSON
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    # Summary
    passed = [s for s, r in results.items() if r.get("passed_validation")]
    logger.info("Optimization complete: %d/%d symbols passed", len(passed), len(symbols))
    for sym in passed:
        r = results[sym]
        oos_sharpe = r["out_of_sample_sharpe"]
        
        # Sanity check for overfitting
        if oos_sharpe > 5.0:
            logger.warning("  %s: SUSPICIOUSLY HIGH SHARPE (%.2f) - likely overfitting", sym, oos_sharpe)

        logger.info(
            "  %s: IS=%.2f OOS=%.2f WR=%.0f%% trades=%d",
            sym, r["in_sample_sharpe"], oos_sharpe,
            r["out_of_sample_win_rate"] * 100, r["total_trades"],
        )

    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    run_all_symbols()
