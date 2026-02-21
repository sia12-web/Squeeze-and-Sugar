"""Startup verification for the live engine."""

import logging
from pathlib import Path
from squeeze_surge.config import config
from squeeze_surge.data.alpaca_client import AlpacaClient

logger = logging.getLogger(__name__)

def run_startup_check() -> bool:
    """Verifies environment, data files, and connectivity.
    
    Returns:
        bool: True if all checks pass.
    """
    logger.info("Running startup checks...")
    
    # 1. Check for optimization_results.json
    opt_path = config.data_dir / "optimization_results.json"
    if not opt_path.exists():
        logger.error("MISSING: optimization_results.json not found at %s", opt_path)
        return False
    logger.info("OK: optimization_results.json found.")

    # 2. Check for 1Hour parquet files (at least for AAPL)
    data_found = False
    for p in (config.data_dir / "1Hour").glob("*.parquet"):
        data_found = True
        break
        
    if not data_found:
        logger.error("MISSING: No 1Hour parquet data found in %s", config.data_dir / "1Hour")
        return False
    logger.info("OK: 1Hour historical data found.")

    # 3. Alpaca Connectivity
    try:
        client = AlpacaClient()
        # Fetch 1 bar of AAPL as connectivity test
        df = client.fetch_ohlcv("AAPL", "1Hour", bars=1)
        if df.empty:
            logger.error("FAIL: Alpaca connectivity test failed (empty response).")
            return False
        logger.info("OK: Alpaca API reachable.")
    except Exception as e:
        logger.error("FAIL: Alpaca connectivity error: %s", e)
        return False

    # 4. Environment Keys
    if not config.alpaca_api_key or not config.alpaca_secret_key:
        logger.error("MISSING: ALPACA_API_KEY or ALPACA_SECRET_KEY in .env")
        return False
    logger.info("OK: Alpaca credentials found.")

    logger.info("All startup checks passed! ✅")
    return True
