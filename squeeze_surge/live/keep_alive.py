"""Keep-alive wrapper for the live engine — same pattern as BB-Strategy."""

import subprocess
import time
import sys
import logging
from squeeze_surge.config import config
from squeeze_surge.live.telegram_notifier import TelegramNotifier

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger("keep_alive")

MAX_RESTARTS = 10
RESTART_DELAY = 10  # Seconds

def run_with_retries():
    """Run the live engine in a subprocess and restart if it crashes."""
    notifier = TelegramNotifier(config.telegram_bot_token, config.telegram_chat_id)
    restart_count = 0
    
    import os
    env = os.environ.copy()
    env["PYTHONPATH"] = str(config.data_dir.parent)
    
    while restart_count < MAX_RESTARTS:
        logger.info("Starting live engine (Attempt %d/%d)...", restart_count + 1, MAX_RESTARTS)
        
        try:
            # Run the main script as a separate process
            process = subprocess.Popen(
                [sys.executable, "-m", "squeeze_surge.live.run_live"],
                env=env
            )
            
            # Wait for the process to exit
            exit_code = process.wait()
            
            if exit_code == 0:
                logger.info("Live engine exited cleanly.")
                break
            else:
                logger.error("Live engine crashed with exit code %d.", exit_code)
                restart_count += 1
                if restart_count < MAX_RESTARTS:
                    msg = f"Squeeze-Surge Engine crashed (Code {exit_code}). Restarting ({restart_count}/{MAX_RESTARTS})..."
                    logger.info(msg)
                    notifier.send_error(msg)
                    time.sleep(RESTART_DELAY)
                else:
                    msg = "Squeeze-Surge Engine reached MAX_RESTARTS. Giving up. 🛑"
                    logger.error(msg)
                    notifier.send_error(msg)
                    
        except Exception as e:
            logger.exception("Keep-alive wrapper encountered an error: %s", e)
            restart_count += 1
            time.sleep(RESTART_DELAY)

if __name__ == "__main__":
    run_with_retries()
