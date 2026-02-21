"""Data pipeline — fetches, enriches with indicators, and stores bars."""

import logging
import time
from datetime import datetime, timedelta, timezone

from squeeze_surge.config import config
from squeeze_surge.data.alpaca_client import AlpacaClient
from squeeze_surge.data.data_store import DataStore
from squeeze_surge.indicators.indicator_engine import IndicatorEngine

logger = logging.getLogger(__name__)


def run_pipeline(
    symbols: list[str] | None = None,
    timeframes: list[str] | None = None,
    years: int = 3,
    client: AlpacaClient | None = None,
    store: DataStore | None = None,
    indicator_engine: IndicatorEngine | None = None,
) -> dict[str, int]:
    """Fetch, enrich with indicators, and store bars for every symbol × timeframe.

    Args:
        symbols: List of ticker symbols. Defaults to config.watchlist.
        timeframes: List of timeframe strings. Defaults to config.timeframes.
        years: Number of years of history to fetch.
        client: Optional AlpacaClient (useful for testing with mocks).
        store: Optional DataStore (useful for testing with tmp dirs).
        indicator_engine: Optional IndicatorEngine override.

    Returns:
        Dict mapping "{symbol}_{timeframe}" to number of rows stored.
    """
    symbols = symbols or config.watchlist
    timeframes = timeframes or config.timeframes
    client = client or AlpacaClient()
    store = store or DataStore()
    indicator_engine = indicator_engine or IndicatorEngine()

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=365 * years)

    results: dict[str, int] = {}

    for symbol in symbols:
        for timeframe in timeframes:
            key = f"{symbol}_{timeframe}"
            logger.info("Fetching %s ...", key)

            try:
                df = client.get_bars(symbol, timeframe, start, end)
                df = indicator_engine.run(symbol, timeframe, df)
                store.save(symbol, timeframe, df)
                results[key] = len(df)
                logger.info("  → %d rows saved (%d columns)", len(df), len(df.columns))
            except Exception:
                logger.exception("  ✗ Failed to fetch %s", key)
                results[key] = 0

            # Respect Alpaca free-tier rate limits
            time.sleep(0.3)

    return results
