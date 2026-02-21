"""Live engine entry point."""

import json
import logging
import sys
from pathlib import Path
from squeeze_surge.config import config
from squeeze_surge.live.startup_check import run_startup_check
from squeeze_surge.live.trade_mode import get_trade_modes
from squeeze_surge.live.telegram_notifier import TelegramNotifier
from squeeze_surge.live.order_executor import OrderExecutor
from squeeze_surge.live.signal_monitor import SignalMonitor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(config.data_dir / "live_engine.log")
    ]
)
logger = logging.getLogger("squeeze_surge.live")

def run_live():
    """Main loop for the live signal engine."""
    logger.info("Starting Squeeze and Surge Live Engine...")
    
    # 1. Startup Check
    if not run_startup_check():
        logger.error("Startup checks failed. Aborting.")
        sys.exit(1)
        
    # 2. Load Resources
    opt_path = config.data_dir / "optimization_results.json"
    with open(opt_path) as f:
        optimized_params = json.load(f)
        
    trade_modes = get_trade_modes(opt_path)
    # Count validated symbols
    validated = [s for s, r in optimized_params.items() if r.get("passed_validation")]
    
    # 3. Initialize Components
    notifier = TelegramNotifier(config.telegram_bot_token, config.telegram_chat_id)
    executor = OrderExecutor(config.data_dir / "paper_trades.json")
    
    monitor = SignalMonitor(
        symbols=config.watchlist,
        optimized_params=optimized_params,
        trade_modes=trade_modes,
        poll_interval_seconds=300,
        order_executor=executor,
        notifier=notifier
    )
    
    # 4. Startup Notification
    notifier.send_startup(validated)
    
    # 5. Start Polling
    try:
        monitor.run()
    except KeyboardInterrupt:
        logger.info("Engine stopped by user.")
    except Exception as e:
        logger.exception("Engine crashed: %s", e)
        notifier.send_error(f"Live engine crashed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run_live()
