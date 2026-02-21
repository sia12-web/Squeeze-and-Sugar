"""Optimization result dataclass — JSON serialisable."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path

# Keys that must never appear in serialised output
_SENSITIVE_KEYS = {"api_key", "secret", "account", "token"}


@dataclass
class OptimizationResult:
    """Stores the outcome of a single-symbol optimisation run."""

    symbol: str
    best_params: dict = field(default_factory=dict)
    in_sample_sharpe: float = 0.0
    out_of_sample_sharpe: float = 0.0
    out_of_sample_win_rate: float = 0.0
    out_of_sample_profit_factor: float = 0.0
    total_trades: int = 0
    passed_validation: bool = False

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------
    def to_dict(self) -> dict:
        d = asdict(self)
        return _sanitize(d)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, d: dict) -> "OptimizationResult":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})

    @classmethod
    def from_json(cls, s: str) -> "OptimizationResult":
        return cls.from_dict(json.loads(s))


def _sanitize(d: dict) -> dict:
    """Recursively strip sensitive keys and normalise non-finite floats."""
    import math

    cleaned: dict = {}
    for k, v in d.items():
        if any(s in k.lower() for s in _SENSITIVE_KEYS):
            continue
        if isinstance(v, dict):
            cleaned[k] = _sanitize(v)
        elif isinstance(v, float) and (math.isinf(v) or math.isnan(v)):
            cleaned[k] = 9999.0 if math.isinf(v) and v > 0 else 0.0
        else:
            cleaned[k] = v
    return cleaned
