"""Telegram notification module for live signals."""

import requests
import logging

logger = logging.getLogger(__name__)

class TelegramNotifier:
    """Sends strategy alerts and updates to Telegram."""

    def __init__(self, token: str | None, chat_id: str | None):
        self.token = token
        self.chat_id = chat_id
        self.enabled = bool(token and chat_id)
        
        if not self.enabled:
            logger.warning("Telegram notification disabled (TOKEN or CHAT_ID missing).")

    def _send(self, text: str) -> bool:
        """Helper to post message to Telegram API."""
        if not self.enabled:
            return False
            
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error("Failed to send Telegram message: %s", e)
            return False

    def send_signal(self, symbol: str, direction: str, entry: float, sl: float, trail_pct: float, mode: str):
        """Send a formatted trading signal."""
        emoji = "📈" if direction.lower() == "long" else "📉"
        # 📈 <b>AAPL LONG</b>\n💰 Entry: $182.45\n🛡 SL: $178.20\n📉 Trail: 5%\n📋 Mode: PAPER
        text = (
            f"{emoji} <b>{symbol} {direction.upper()}</b>\n"
            f"💰 Entry: ${entry:.2f}\n"
            f"🛡 SL: ${sl:.2f}\n"
            f"📊 Trail: {trail_pct*100:.1f}%\n"
            f"📋 Mode: {mode.upper()}"
        )
        self._send(text)

    def send_startup(self, validated_symbols: list[str]):
        """Send notification on system startup."""
        text = (
            "🚀 <b>Squeeze and Surge Live Engine Started</b>\n"
            f"Symbols: {len(validated_symbols)} validated, {10 - len(validated_symbols)} paper-only\n"
            "Status: Polling Alpaca (300s interval)"
        )
        self._send(text)

    def send_error(self, message: str):
        """Send error alert."""
        text = f"🚨 <b>ERROR</b>\n{message}"
        self._send(text)
