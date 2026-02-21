"""Tests for TelegramNotifier."""

from unittest.mock import patch, MagicMock
from squeeze_surge.live.telegram_notifier import TelegramNotifier

def test_send_signal_format():
    """Mock requests.post, assert payload contains symbol and entry price."""
    notifier = TelegramNotifier("fake_token", "fake_id")
    
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        
        notifier.send_signal("AAPL", "long", 182.45, 178.20, 0.05, "paper")
        
        assert mock_post.called
        args, kwargs = mock_post.call_args
        payload = kwargs["json"]
        
        assert "AAPL" in payload["text"]
        assert "182.45" in payload["text"]
        assert "LONG" in payload["text"]
        assert "PAPER" in payload["text"]
        assert "chat_id" in payload
        assert payload["chat_id"] == "fake_id"

def test_disabled_when_token_none():
    """token=None, assert requests.post never called."""
    notifier = TelegramNotifier(None, "fake_id")
    
    with patch("requests.post") as mock_post:
        notifier.send_signal("AAPL", "long", 180.0, 175.0, 0.05, "paper")
        assert not mock_post.called
        
    notifier2 = TelegramNotifier("fake_token", None)
    with patch("requests.post") as mock_post:
        notifier2.send_signal("AAPL", "long", 180.0, 175.0, 0.05, "paper")
        assert not mock_post.called
