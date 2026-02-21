"""Configuration loaded from .env file."""

from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class Config:
    """Application configuration loaded from environment variables."""

    alpaca_api_key: str = field(default_factory=lambda: os.getenv("ALPACA_API_KEY", ""))
    alpaca_secret_key: str = field(default_factory=lambda: os.getenv("ALPACA_SECRET_KEY", ""))
    alpaca_base_url: str = field(
        default_factory=lambda: os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
    )

    watchlist: list[str] = field(default_factory=lambda: [
        "SPY", "QQQ", "AAPL", "NVDA", "MSFT",
        "TSLA", "AMZN", "META", "GOOGL", "AMD",
    ])

    timeframes: list[str] = field(default_factory=lambda: ["1Day", "1Hour"])

    data_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "data")

    telegram_bot_token: str = field(default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", ""))
    telegram_chat_id: str = field(default_factory=lambda: os.getenv("TELEGRAM_CHAT_ID", ""))

    def __post_init__(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)


# Singleton instance
config = Config()
