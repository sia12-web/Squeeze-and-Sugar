# Squeeze & Surge — CONTEXT

## Project Name
**Squeeze & Surge** — A momentum trading strategy engine focused on Bollinger Band squeeze detection and breakout surges.

## Stack
| Layer | Technology |
|-------|-----------|
| Language | Python 3.12 |
| Data SDK | `alpaca-py` (Alpaca Data API v2) |
| Storage | `pandas` + `pyarrow` (parquet files) |
| Config | `python-dotenv` (.env) |
| Testing | `pytest` |

## Watchlist
`SPY`, `QQQ`, `AAPL`, `NVDA`, `MSFT`, `TSLA`, `AMZN`, `META`, `GOOGL`, `AMD`

## Timeframes
- `1Day` — daily bars (~750 rows per symbol for 3 years)
- `1Hour` — hourly bars (~6000 rows per symbol for 3 years)

## File Structure
```
Squeeze and Sugar/
├── .env.example          # Placeholder API keys
├── .gitignore            # Excludes .env, data/, __pycache__
├── requirements.txt      # Python dependencies
├── CONTEXT.md            # This file
├── CHANGELOG.md          # Release history
├── logs/                 # Runtime logs
├── data/                 # Parquet files (gitignored)
│   └── {SYMBOL}_{TIMEFRAME}.parquet
├── squeeze_surge/
│   ├── __init__.py
│   ├── config.py         # Config dataclass from .env
│   ├── pipeline.py       # run_pipeline() orchestrator
│   ├── data/
│   │   ├── __init__.py
│   │   ├── alpaca_client.py  # AlpacaClient wrapping SDK
│   │   └── data_store.py     # DataStore for parquet I/O
│   ├── indicators/
│   │   ├── __init__.py
│   │   ├── bollinger.py       # BollingerBands
│   │   ├── keltner.py         # KeltnerChannels
│   │   ├── squeeze.py         # SqueezeDetector (TTM Squeeze)
│   │   ├── momentum.py        # Momentum + delta
│   │   ├── volume_ratio.py    # VolumeRatio
│   │   ├── symbol_configs.py  # Per-symbol indicator params
│   │   └── indicator_engine.py # IndicatorEngine orchestrator
│   ├── strategy/
│   │   ├── __init__.py
│   │   ├── squeeze_ranker.py    # SqueezeRanker (quality scoring)
│   │   ├── signal_generator.py  # SignalGenerator (entry/exit)
│   │   ├── position_sizer.py    # PositionSizer (risk-based sizing)
│   │   └── strategy_engine.py   # StrategyEngine orchestrator
│   ├── backtest/
│   │   ├── __init__.py
│   │   ├── trade.py              # Trade dataclass
│   │   ├── metrics.py            # Sharpe, drawdown, profit factor, win rate
│   │   ├── backtest_result.py    # BacktestResult dataclass
│   │   ├── backtest_engine.py    # Bar-by-bar backtest engine
│   │   └── run_backtest.py       # Convenience runner
│   └── optimization/
│       ├── __init__.py
│       ├── param_grid.py          # 648-combo parameter grid
│       ├── optimization_result.py # Result dataclass (JSON serialisable)
│       ├── optimizer.py           # Single-symbol grid-search with IS/OOS
│       └── run_optimization.py    # All-symbol parallel runner
└── tests/
    ├── __init__.py
    ├── test_alpaca_client.py
    ├── test_data_store.py
    ├── test_pipeline.py
    ├── test_bollinger.py
    ├── test_keltner.py
    ├── test_squeeze.py
    ├── test_momentum.py
    ├── test_volume_ratio.py
    ├── test_indicator_engine.py
    ├── test_squeeze_ranker.py
    ├── test_signal_generator.py
    ├── test_position_sizer.py
    ├── test_strategy_engine.py
    ├── test_trade.py
    ├── test_metrics.py
    ├── test_backtest_engine.py
    ├── test_run_backtest.py
    ├── test_optimizer.py
    ├── test_optimization_result.py
    └── test_run_optimization.py
```

## Data Format
Each parquet file contains a DataFrame with columns:
| Column | Type | Description |
|--------|------|-------------|
| `time` | datetime64[ns, UTC] | Bar timestamp |
| `open` | float64 | Opening price |
| `high` | float64 | High price |
| `low` | float64 | Low price |
| `close` | float64 | Closing price |
| `volume` | int64 | Volume traded |

## Indicator Columns
After `IndicatorEngine.run()`, 12 columns are appended:

| Column | Type | Formula |
|--------|------|---------|
| `bb_upper` | float64 | SMA(close, 20) + 2.0 × StdDev(close, 20) |
| `bb_middle` | float64 | SMA(close, 20) |
| `bb_lower` | float64 | SMA(close, 20) − 2.0 × StdDev(close, 20) |
| `bb_width` | float64 | bb_upper − bb_lower |
| `kc_upper` | float64 | EMA(close, 20) + 1.5 × ATR(20) |
| `kc_middle` | float64 | EMA(close, 20) |
| `kc_lower` | float64 | EMA(close, 20) − 1.5 × ATR(20) |
| `squeeze_on` | bool | True when bb_upper < kc_upper AND bb_lower > kc_lower |
| `squeeze_bars` | int64 | Consecutive bars squeeze has been active (resets to 0 on release) |
| `momentum` | float64 | close − close.shift(12) |
| `momentum_delta` | float64 | momentum − momentum.shift(1) |
| `volume_ratio` | float64 | volume / SMA(volume, 20) |

## Symbol Configs
| Symbol | BB Std | Notes |
|--------|--------|-------|
| SPY, QQQ, AAPL, MSFT, AMZN, META, GOOGL, AMD | 2.0 | Default |
| TSLA, NVDA | 2.5 | Higher volatility → wider bands → higher quality squeeze |

All symbols share: BB period=20, KC period=20, KC ATR mult=1.5, Momentum period=12, Volume Ratio period=20.

## Signal Entry Rules

### Long Entry
All conditions must be true on the same bar:
1. **Squeeze release** — previous bar `squeeze_on=True`, current bar `squeeze_on=False`
2. **Minimum squeeze duration** — previous bar `squeeze_bars >= 3`
3. **Price breakout** — `close > bb_upper`
4. **Positive momentum** — `momentum > 0`
5. **Momentum accelerating** — `momentum_delta > 0`
6. **Volume surge** — `volume_ratio > 1.5`

### Short Entry
Mirror of long: `close < bb_lower`, `momentum < 0`, `momentum_delta < 0`, `volume_ratio > 1.5`.

### Exit Rules
- **Stop loss**: `entry_price - ATR(20) × 2.0` for longs, `entry_price + ATR(20) × 2.0` for shorts
- **Trailing stop**: 5% (`trail_stop_pct = 0.05`) — lets winners run
- **Momentum exit**: exit when `momentum_delta < 0` for 2 consecutive bars after entry

### Signal Columns Added
| Column | Type | Description |
|--------|------|-------------|
| `signal` | int | 1 = long, -1 = short, 0 = none |
| `signal_type` | str | 'long', 'short', '' |
| `entry_price` | float | Close of signal bar |
| `stop_loss` | float | Entry ∓ ATR × 2.0 |
| `trail_stop_pct` | float | 0.05 on signal bars |
| `exit_signal` | int | 1 = exit, 0 = hold |

## Position Sizing
- Risk = `account_balance × risk_pct` (default 1%)
- Shares = `floor(risk_amount / abs(entry_price - stop_loss))`

## Squeeze Ranking (Dashboard)
- `squeeze_score = squeeze_bars × 10 + avg_volume_ratio × 5 + normalised_|momentum| (0-10)`
- Used for display/ranking, **not** for signal gating

## Backtest Engine

### Execution Model
- **Bar-by-bar** iteration via `itertuples()`
- **One position at a time** per symbol — no overlapping trades
- **Initial balance**: $10,000 (configurable)
- **Risk per trade**: 1% of balance (configurable)

### Exit Reasons
| Reason | Logic |
|--------|-------|
| `stop_loss` | Long: low ≤ stop_loss. Short: high ≥ stop_loss. **Priority over trail.** |
| `trail_stop` | Track peak via *high*. Exit when close < peak × (1 − 0.05). |
| `momentum_exit` | `momentum_delta < 0` for 2 consecutive bars after entry |
| `end_of_data` | Open position closed at last bar's close |

### Market Hours Filter
- **1Hour** bars: only process 09:30–16:00 ET (`America/New_York`). Pre/after market bars skipped.
- **1Day** bars: always valid, no filter applied.

### ETF Long-Only Rule
- **SPY, QQQ**: short signals are skipped. These are index ETFs — long bias only.

### Trailing Stop Detail
- Peak tracked using bar *high* (not close) for accuracy
- Trail level = peak × (1 − trail_stop_pct)
- Exit price = close of the bar that triggers the trail

### Metrics
| Metric | Formula |
|--------|--------|
| Sharpe Ratio | mean(daily_returns) / std(daily_returns) × √252 |
| Max Drawdown | max((peak − trough) / peak) over equity curve |
| Profit Factor | gross_profit / gross_loss |
| Win Rate | winning_trades / total_trades |

## Alpaca API Notes
- **Data API base URL**: `https://data.alpaca.markets` (separate from trading API)
- **Trading API base URL**: `https://paper-api.alpaca.markets` (paper trading)
- Paper API keys work for data fetching — no live account needed
- Uses `StockHistoricalDataClient` → `get_stock_bars(StockBarsRequest(...))`
- Response is dict keyed by symbol; bars are converted via `bar.model_dump()`
- `timestamp` column renamed to `time` for consistency
- Free plan rate limit: `time.sleep(0.3)` between fetches
- **Feed**: `iex` (free tier) — set in `StockBarsRequest(feed="iex")`

## Optimization

### Parameter Grid (648 combos)
| Parameter | Values |
|-----------|--------|
| `bb_period` | 15, 20, 25 |
| `bb_std` | 1.8, 2.0, 2.2, 2.5 |
| `kc_period` | 15, 20 |
| `kc_atr_mult` | 1.3, 1.5, 1.8 |
| `momentum_period` | 8, 12, 16 |
| `min_squeeze_bars` | 2, 3, 5 |

### IS/OOS Split
- Chronological 70/30 split on daily data
- Grid search on IS by Sharpe ratio
- OOS validation with dual gates:
  - **Primary**: Sharpe ≥ 0.3 AND win_rate ≥ 0.4 AND trades ≥ 5
  - **Fallback**: Sharpe ≥ 0.15 AND win_rate ≥ 0.45 AND trades ≥ 8

### Results (3y daily, Feb 2023–Feb 2026)
| Symbol | IS Sharpe | OOS Sharpe | OOS WR | OOS Trades | Passed |
|--------|-----------|------------|--------|------------|--------|
| SPY | 0.00 | 0.00 | 0% | 0 | ❌ |
| QQQ | 0.00 | 0.00 | 0% | 0 | ❌ |
| AAPL | 225.87 | 0.00 | 100% | 1 | ❌ |
| NVDA | 9.48 | -18.80 | 33% | 3 | ❌ |
| TSLA | 50.37 | 0.00 | 0% | 0 | ❌ |
| MSFT | 1.87 | 0.00 | 100% | 1 | ❌ |
| AMZN | 1.86 | 0.00 | 100% | 1 | ❌ |
| META | 31.14 | 0.00 | 0% | 0 | ❌ |
| GOOGL | 41.75 | 0.00 | 0% | 0 | ❌ |
| AMD | 19.14 | 0.00 | 0% | 0 | ❌ |

**Analysis**: Squeeze signals are extremely rare on daily bars (~0-3 trades per symbol in OOS). The strict 6-condition entry filter produces high-quality but infrequent signals. IS Sharpe is inflated by 1-2 lucky trades. SPY/QQQ long-only further limits signals.

**Next steps**: Consider 1Hour optimization, relaxing volume_ratio threshold, or combining with other entry setups.

### Config Update
- `symbol_configs.update_from_optimization(path)` loads validated params from JSON
- Only updates symbols that passed OOS validation

## Optimization Phase 5C (Continuation Breakout + 10-Trade Floor)

### Key Changes
- **Entry Mode**: Switched from `release` to `continuation`.
- **Logic**: Enter when `squeeze_on == True` AND `close > bb_upper` (breakout *during* squeeze).
- **Volume Ratio Threshold**: Added to optimization grid [1.1, 1.2, 1.5].
- **Trade Floor**: Hard floor of **10 trades** for both In-Sample and Out-of-Sample.
- **Validation Gates (1Hour)**:
  - Primary: Sharpe ≥ 0.5 AND win_rate ≥ 0.45 AND trades ≥ 10
  - Fallback: Sharpe ≥ 0.25 AND win_rate ≥ 0.40 AND trades ≥ 10

### Diagnostics (Filter Funnel - Continuation Mode)
| Symbol | Total Bars | Squeeze On | Active (≥3b) | Breakout | Final Signals |
|--------|------------|------------|--------------|----------|---------------|
| AAPL | 4476 | 335 | 209 | 13 | 8 |
| MSFT | 4477 | 240 | 142 | 13 | 5 |
| AMZN | 4476 | 184 | 103 | 9 | 5 |
| GOOGL | 4477 | 185 | 100 | 11 | 5 |

*Note: Counts above use default params (BB std 2.0, Vol 1.2). Optimization finds more.*

### Results (1Hour OOS, ~11 months)
| Symbol | IS Sharpe | OOS Sharpe | OOS WR | OOS Trades | Passed |
|--------|-----------|------------|--------|------------|--------|
| AAPL | 5.42 | 8.45 | 67% | 12 | ✅ |
| MSFT | 10.20 | -0.43 | 50% | 4 | ❌ |
| SPY | 2.59 | -0.11 | 67% | 6 | ❌ |
| GOOGL | 9.70 | 0.17 | 25% | 4 | ❌ |

**Analysis**: AAPL successfully reached the 10-trade threshold with a high Sharpe ratio (likely overfitted but valid by gates). Other symbols failed the 10-trade hard floor in the OOS period, despite high IS frequency. The "Continuation Breakout" logic significantly increased signal density compared to the "Release" version.

## Current Phase
- **Phase 5C: Continuation Mode** ✅ — Breakthrough during active squeeze, 10-trade floor, AAPL validated.
- **Phase 6: Reporting Dashboard** ✅ — HTML dashboard with Plotly charts, equity curves, and squeeze filter funnel.
- **Phase 7: Live Signal Engine** ✅ — Polling Alpaca, Strategy alerts, Paper execution.

## Live Signal Engine (Phase 7)

### Architecture
1. **SignalMonitor**: The heart of the engine. Polls Alpaca every 5 minutes (300s), applies optimized parameters via `StrategyEngine`, and monitors for new signals.
2. **CandleFetcher**: Fetches latest 1Hour bars and filters to regular US market hours (09:30-16:00 ET).
3. **Trade Mode Strategy**: All symbols operate in **PAPER** mode. Promotion to live trading requires a symbol (like AAPL) to accumulate 20+ live paper trades with positive expectancy.
4. **OrderExecutor**: Thread-safe recording of all generated signals into `data/paper_trades.json`.
5. **Telegram Notifier**: Real-time alerts for signals, system startup, and critical errors.
6. **Keep-Alive**: Automatic subprocess monitor that restarts the engine on crash (up to 10 attempts).

### VPS Deployment (Hostinger)
- **Service Name**: `squeeze-surge.service`
- **Root Directory**: `~/myApplications/Squeeze and Sugar/`
- **Command**: `python -m squeeze_surge.live.keep_alive`
- **Logs**: `data/live_engine.log` and `data/signal_log.jsonl`

## Current Phase
**Phase 7: Live Signal Engine** — COMPLETE ✅

### Phase History
- **Phase 1: Data Pipeline** ✅ — Alpaca fetcher, parquet storage, pipeline orchestrator.
- **Phase 2: Indicator Engine** ✅ — BB, KC, TTM Squeeze, Momentum, Volume Ratio.
- **Phase 3: Signal Generator** ✅ — Entry/exit rules, PositionSizer, StrategyEngine.
- **Phase 4: Backtesting Engine** ✅ — Trailing stop, market hours filter, metrics.
- **Phase 5: Optimization** ✅ — Grid search, IS/OOS validation, parallel execution.
- **Phase 5B: 1Hour Optimization** ✅ — Relaxed volume threshold, 1Hour data, MSFT/QQQ validated.
- **Phase 5C: Continuation Mode** ✅ — Breakthrough during active squeeze, 10-trade floor, AAPL validated.
- **Phase 6: Reporting Dashboard** ✅ — Static HTML report at `data/report.html`.
- **Phase 7: Live Signal Engine** ✅ — Real-time polling, Telegram alerts, Paper trading.
