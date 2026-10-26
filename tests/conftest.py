from __future__ import annotations

import itertools

import pytest

from reflect_bot.app.container import ApplicationContext
from reflect_bot.app.infrastructure import Infrastructure
from reflect_bot.config import Settings
from tests.fakes import (FixedClock, InMemoryAccountRepository, InMemoryReportRepository,
                         InMemorySettingsRepository, RecordingMessenger, ScriptedUpdateSource)

GROUP_ID = -1001234567890
ADMIN_DM = 7
USER_DM = 5


class Harness:
    """Полное приложение на фейках + удобная отправка апдейтов."""

    def __init__(self):
        self.clock = FixedClock()
        self.messenger = RecordingMessenger()
        self.accounts_repo = InMemoryAccountRepository()
        self.settings_repo = InMemorySettingsRepository(chat_id=str(GROUP_ID))
        self.reports_repo = InMemoryReportRepository()
        self.source = ScriptedUpdateSource()
        self.settings = Settings(bot_token="t", super_admins=frozenset({"boss", "deputy"}), sheet_id="s", service_account_json="{}")
        self._ids = itertools.count(100)
        self.reset_context()

    def reset_context(self) -> None:
        """Как рестарт процесса: новые кеши поверх тех же «таблиц»."""
        self.context = ApplicationContext(self.settings, Infrastructure(
            self.clock, self.messenger, self.source, self.accounts_repo, self.settings_repo, self.reports_repo))
        self.context.sync.sync()

    def send(self, username: str, text: str, chat_id: int = GROUP_ID, *, edit_of: int | None = None,
             photo: bool = False) -> int:
        message_id = edit_of or next(self._ids)
        timestamp = int(self.clock.now().timestamp())
        raw = {"message_id": message_id, "date": timestamp, "from": {"username": username},
               "chat": {"id": chat_id, "type": "private" if chat_id > 0 else "supergroup"}}
        raw["caption" if photo else "text"] = text
        if photo:
            raw["photo"] = [{"file_id": "x"}]
        if edit_of:
            raw["edit_date"] = timestamp + 60
        self.context.dispatcher.dispatch({"update_id": message_id, "edited_message" if edit_of else "message": raw})
        return message_id


@pytest.fixture
def harness() -> Harness:
    return Harness()


@pytest.fixture
def team(harness: Harness) -> Harness:
    harness.send("boss", "/add @ivan_bel Белорус", ADMIN_DM)
    harness.send("boss", "/add @petya Петя", ADMIN_DM)
    harness.messenger.sent.clear()
    return harness


REPORT = "Сегодня: закрыл пилот оплаты, созвонился с клиентом, разобрал заявки"
