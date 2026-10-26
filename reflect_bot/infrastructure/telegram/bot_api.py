from __future__ import annotations

import logging

import httpx

from reflect_bot.domain.errors import MessengerError
from reflect_bot.interfaces.messaging import Messenger

logger = logging.getLogger(__name__)

API_BASE = "https://api.telegram.org/bot{token}"


def short(text: str, limit: int = 300) -> str:
    flat = " ".join(text.split())
    return flat if len(flat) <= limit else flat[: limit - 1] + "…"


class TelegramBotApi(Messenger):
    """Синхронный клиент Bot API для исходящих вызовов."""

    def __init__(self, token: str, http: httpx.Client | None = None):
        self._base_url = API_BASE.format(token=token)
        self._http = http or httpx.Client(timeout=15)
        self._username: str | None = None

    def send_message(self, chat_id: int | str, text: str, reply_to: int | None = None) -> None:
        payload = {"chat_id": chat_id, "text": text}
        if reply_to:
            payload["reply_parameters"] = {"message_id": reply_to, "allow_sending_without_reply": True}
        self._call("sendMessage", payload)

    def react(self, chat_id: int | str, message_id: int, emoji: str) -> None:
        self._call("setMessageReaction", {"chat_id": chat_id, "message_id": message_id,
                                          "reaction": [{"type": "emoji", "emoji": emoji}]})

    def bot_username(self) -> str:
        if self._username is None:
            self._username = self._call("getMe", {}).get("username", "")
        return self._username

    def reads_group_messages(self) -> bool:
        # Без кеша: privacy mode могут переключить в @BotFather на ходу
        return bool(self._call("getMe", {}).get("can_read_all_group_messages"))

    def close(self) -> None:
        self._http.close()

    def _call(self, method: str, payload: dict):
        try:
            response = self._http.post(f"{self._base_url}/{method}", json=payload)
        except httpx.HTTPError as e:
            raise MessengerError(f"telegram {method} недоступен: {e}") from e
        if response.status_code != 200:
            raise MessengerError(f"telegram {method} responded {response.status_code}: {short(response.text)}")
        return response.json().get("result")
