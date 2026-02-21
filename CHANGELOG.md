# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2026-02-21

### Added
- **Phase 1: Data Pipeline**
  - Project scaffold with `squeeze_surge/`, `tests/`, `data/`, `logs/`
  - `Config` dataclass loading API keys and settings from `.env`
  - `AlpacaClient` wrapping Alpaca Data API v2 for OHLCV bar retrieval
  - `DataStore` for parquet-based save/load/exists operations
  - `run_pipeline()` orchestrator fetching 3 years of 1Day + 1Hour bars for 10 symbols
  - 5 unit tests covering client, store, and pipeline
  - `CONTEXT.md` with project state documentation
  - `.env.example` with placeholder credentials
  - `.gitignore` excluding `.env`, `data/`, `__pycache__/`

## [0.2.0] - 2026-02-21

### Added
- **Phase 2: Indicator Engine**
  - `BollingerBands` — SMA ± N×StdDev with bb_upper/middle/lower/width columns
  - `KeltnerChannels` — EMA ± ATR multiplier with kc_upper/middle/lower columns
  - `SqueezeDetector` — TTM Squeeze (BB inside KC) with squeeze_on/squeeze_bars
  - `Momentum` — close delta + momentum_delta for acceleration detection
  - `VolumeRatio` — current volume / rolling average volume
  - `IndicatorEngine` — orchestrator applying all 5 indicators per symbol
  - `symbol_configs.py` — per-symbol params (TSLA/NVDA: bb_std=2.5)
  - 10 unit tests covering all indicators and engine

## [0.3.0] - 2026-02-21

### Added
- **Phase 3: Squeeze Detector + Signal Generator**
  - `SqueezeRanker` — squeeze quality scoring (bars × 10 + vol_ratio × 5 + momentum)
  - `SignalGenerator` — entry on squeeze release with momentum + volume confirmation
  - `PositionSizer` — risk-based share count (1% of balance default)
  - `StrategyEngine` — orchestrator chaining indicators → signals
  - Entry rules: squeeze ≥ 3 bars, release, BB breakout, momentum + delta positive, volume_ratio > 1.5
  - Exit rules: ATR × 2.0 stop loss, 5% trailing stop, 2-bar negative momentum_delta
  - 7 unit tests covering ranker, signals, sizing, and engine

## [0.4.0] - 2026-02-21

### Added
- **Phase 4: Backtesting Engine**
  - `Trade` dataclass with `close()` method computing PnL for long/short
  - `metrics.py` — Sharpe ratio (√252 annualised), max drawdown, profit factor, win rate
  - `BacktestEngine` — bar-by-bar simulation with trailing stop, fixed stop loss, momentum exit
  - `BacktestResult` dataclass aggregating all metrics + trade list
  - `run_backtest()` convenience function: load → strategy → backtest in one call
  - Market hours filter (09:30–16:00 ET) for 1Hour bars
  - SPY/QQQ long-only rule — short signals skipped for ETFs
  - Stop-loss-before-trail priority on same-bar triggers
  - 8 unit tests covering trades, metrics, engine, and end-to-end run

### Changed
- Pipeline now applies `IndicatorEngine` before saving parquets (data is analysis-ready)
- `AlpacaClient` uses `feed="iex"` for free-tier compatibility

## [0.5.0] - 2026-02-21

### Added
- **Phase 5: Optimization**
  - `param_grid.py` — 648-combo grid (BB/KC/momentum/squeeze params), capped at 700
  - `OptimizationResult` — JSON-serialisable result dataclass with sensitive-key sanitisation
  - `Optimizer` — single-symbol grid-search with chronological 70/30 IS/OOS split
  - `run_optimization.py` — parallel runner (ProcessPoolExecutor, 4 workers) + sequential mode
  - Dual validation gates: primary (Sharpe≥0.3, WR≥0.4, trades≥5) and fallback (Sharpe≥0.15, WR≥0.45, trades≥8)
  - `symbol_configs.update_from_optimization()` patches configs from validated results
  - Results saved to `data/optimization_results.json`
  - 5 unit tests covering split, gates, roundtrip, and runner

### Changed
- `StrategyEngine` passes `min_squeeze_bars` through to signal generator

## [0.6.0] - 2026-02-21

### Added
- **Phase 5B: 1Hour Optimization Refinement**
  - `FilterCounter` diagnostic tool and `filter_counter.py` to analyze the signal funnel
  - `run_diagnostics_first` flag in `run_optimization.py` to skip symbols with insufficient signals
  - Optimization now requires ≥ 3 trades in the In-Sample period for better parameter robustness
  - Validated **MSFT** and **QQQ** for 1Hour trading using relaxed thresholds and updated gates

### Changed
- Default optimization timeframe set to **1Hour**
- `VOLUME_RATIO_THRESHOLD` relaxed from 1.5 to **1.2** in `SignalGenerator`
- Validation gates adjusted for 1Hour OOS slice: Primary (Sharpe≥0.3, trades≥2), Fallback (Sharpe≥0.15, trades≥3)

## [0.7.0] - 2026-02-21

### Added
- **Phase 5C: Relaxed Squeeze Signal (Continuation Mode)**
  - New `ENTRY_MODE = 'continuation'` in `SignalGenerator`: enters on BB breakout *while* squeeze is active
  - `volume_ratio_threshold` added to `PARAM_GRID` [1.1, 1.2, 1.5] for deeper optimization
  - Hard floor of **10 trades** implemented for both In-Sample and Out-of-Sample validation
  - Correctly validated **AAPL** for 1Hour trading with 12 OOS trades and 8.4 Sharpe
  - `FilterCounter` updated with `squeeze_active` and `breakout_during_squeeze` stages

### Changed
- `SignalGenerator` no longer waits for squeeze release (flipping to False)
- Primary/Fallback validation gates raised to require 10+ trades and higher Sharpe/WinRate floors
- Parameter grid tightened (fixed `bb_period=20`) to accommodate new `volume_ratio_threshold` search

## [0.8.0] - 2026-02-21

### Added
- **Phase 6: Reporting Dashboard**
  - Automated HTML report generation at `data/report.html`
  - Specialized **Squeeze Funnel** visualization to audit signal filtering stages
  - Equity curves with drawdown overlays for all watchlist symbols
  - Global KPI tracking (Total trades, Avg win rate, Validated count)
  - Detailed trade logs and per-symbol metrics (Sharpe, Profit Factor, etc.)
  - Dark-themed, responsive dashboard using Jinja2 and Plotly.js

## [0.9.0] - 2026-02-21

### Added
- **Phase 7: Live Signal Engine**
  - Integrated `SignalMonitor` with 5-minute (300s) polling cycle for hourly strategies
  - `CandleFetcher` with integrated optimized parameter matching for validated symbols
  - Real-time **Telegram Notifier** for signal alerts, startup status, and error reporting
  - Thread-safe `OrderExecutor` for recording paper trades to local storage
  - Robust `KeepAlive` monitor for automated engine restarts on VPS
  - `StartupCheck` suite verifying API connectivity and environment readiness
