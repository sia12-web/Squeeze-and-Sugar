"""Parameter grid for optimization."""

from itertools import product

PARAM_GRID = {
    "bb_period": [20],
    "bb_std": [1.8, 2.0, 2.2],
    "kc_period": [15, 20],
    "kc_atr_mult": [1.3, 1.5, 1.8],
    "momentum_period": [8, 12, 16],
    "min_squeeze_bars": [2, 3, 4],
    "volume_ratio_threshold": [1.1, 1.2, 1.5],
}

MAX_COMBOS = 700


def generate_combos() -> list[dict]:
    """Generate all parameter combinations from PARAM_GRID.

    Raises ValueError if the grid exceeds MAX_COMBOS.
    """
    keys = list(PARAM_GRID.keys())
    values = list(PARAM_GRID.values())
    combos = [dict(zip(keys, v)) for v in product(*values)]

    if len(combos) > MAX_COMBOS:
        raise ValueError(
            f"Grid produces {len(combos)} combos, exceeds cap of {MAX_COMBOS}"
        )

    return combos
