from __future__ import annotations

import json
from datetime import datetime, tzinfo

import httpx

from reflect_bot.domain.errors import MessengerError
from reflect_bot.domain.models import IncomingMessage, normalize_username
from reflect_bot.infrastructure.telegram.bot_api import API_BASE, short
from reflect_bot.interfaces.messaging import UpdateSource

POLL_TIMEOUT_SECONDS = 50
ALLOWED_UPDATES = ("message", "edited_message")


class TelegramUpdateSource(UpdateSource):
    """Long polling через getUpdates. Асинхронный — чтобы остановка сервиса не ждала 50 секунд."""

    def __init__(self, token: str, http: httpx.AsyncClient | None = None):
        self._url = API_BASE.format(token=token) + "/getUpdates"
        self._http = http or httpx.AsyncClient(timeout=POLL_TIMEOUT_SECONDS + 10)

    async def fetch(self, offset: int | None) -> list[dict]:
        params = {"timeout": POLL_TIMEOUT_SECONDS, "allowed_updates": json.dumps(ALLOWED_UPDATES)}
        if offset is not None:
            params["offset"] = offset
        try:
            response = await self._http.get(self._url, params=params)
        except httpx.HTTPError as e:
            raise MessengerError(f"getUpdates недоступен: {e}") from e
        if response.status_code != 200:
            # 409 — у бота стоит вебхук или параллельно опрашивает второй инстанс (редеплой)
            raise MessengerError(f"getUpdates responded {response.status_code}: {short(response.text)}")
        return response.json().get("result") or []

    async def close(self) -> None:
        await self._http.aclose()


class UpdateParser:
    """Сырой апдейт Telegram -> IncomingMessage. Всё, что не сообщение, отбрасывается."""

    def __init__(self, timezone: tzinfo):
        self._timezone = timezone

    def parse(self, update: dict) -> IncomingMessage | None:
        edited = "edited_message" in update
        raw = update.get("edited_message") or update.get("message")
        if not raw or "chat" not in raw:
            return None
        edit_date = raw.get("edit_date") if edited else None
        return IncomingMessage(
            message_id=raw["message_id"],
            chat_id=raw["chat"]["id"],
            chat_type=raw["chat"].get("type", ""),
            username=normalize_username((raw.get("from") or {}).get("username") or ""),
            text=raw.get("text") or raw.get("caption") or "",
            sent_at=self._time(raw["date"]),
            edited_at=self._time(edit_date or raw["date"]) if edited else None,
            has_photo=bool(raw.get("photo")),
        )

    def _time(self, timestamp: int) -> datetime:
        return datetime.fromtimestamp(timestamp, self._timezone)
