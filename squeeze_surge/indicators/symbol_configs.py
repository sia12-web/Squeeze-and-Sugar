"""Default indicator configurations per symbol."""

import json
from pathlib import Path

_DEFAULT = {
    "bb_period": 20,
    "bb_std": 2.0,
    "kc_period": 20,
    "kc_atr_mult": 1.5,
    "momentum_period": 12,
    "volume_ratio_period": 20,
}

_HIGH_VOL = {
    **_DEFAULT,
    "bb_std": 2.5,  # Wider bands for higher-volatility symbols
}

SYMBOL_CONFIGS: dict[str, dict] = {
    "SPY": {**_DEFAULT},
    "QQQ": {**_DEFAULT},
    "AAPL": {**_DEFAULT},
    "NVDA": {**_HIGH_VOL},
    "MSFT": {**_DEFAULT},
    "TSLA": {**_HIGH_VOL},
    "AMZN": {**_DEFAULT},
    "META": {**_DEFAULT},
    "GOOGL": {**_DEFAULT},
    "AMD": {**_DEFAULT},
}


def update_from_optimization(results_path: str | Path | None = None) -> list[str]:
    """Load optimisation results and update SYMBOL_CONFIGS for validated symbols.

    Returns list of symbols that were updated.
    """
    if results_path is None:
        results_path = Path("data") / "optimization_results.json"
    results_path = Path(results_path)

    if not results_path.exists():
        return []

    with open(results_path) as f:
        results = json.load(f)

    updated: list[str] = []
    for symbol, result in results.items():
        if not result.get("passed_validation"):
            continue
        best = result.get("best_params", {})
        if not best:
            continue

        # Map optimised params onto indicator config keys
        cfg = {
            "bb_period": best.get("bb_period", _DEFAULT["bb_period"]),
            "bb_std": best.get("bb_std", _DEFAULT["bb_std"]),
            "kc_period": best.get("kc_period", _DEFAULT["kc_period"]),
            "kc_atr_mult": best.get("kc_atr_mult", _DEFAULT["kc_atr_mult"]),
            "momentum_period": best.get("momentum_period", _DEFAULT["momentum_period"]),
            "volume_ratio_period": 20,
        }
        SYMBOL_CONFIGS[symbol] = cfg
        updated.append(symbol)

    return updated

