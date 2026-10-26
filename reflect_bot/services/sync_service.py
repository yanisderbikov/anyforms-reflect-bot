from __future__ import annotations

import logging
from dataclasses import dataclass

from reflect_bot.interfaces.messaging import Messenger
from reflect_bot.interfaces.runtime import Clock, HealthIndicator
from reflect_bot.services.account_service import AccountService
from reflect_bot.services.chat_settings_service import ChatSettingsService
from reflect_bot.services.report_service import ReportService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SyncResult:
    accounts: int
    chat_id: str | None
    reported_today: int
    reads_group_messages: bool


class SyncService(HealthIndicator):
    """Перечитывает все кеши из таблицы и проверяет, видит ли бот группу: холодный старт и /sync."""

    def __init__(self, accounts: AccountService, chat_settings: ChatSettingsService,
                 reports: ReportService, messenger: Messenger, clock: Clock):
        self._accounts = accounts
        self._chat_settings = chat_settings
        self._reports = reports
        self._messenger = messenger
        self._clock = clock
        self._synced_at: str | None = None

    @property
    def is_loaded(self) -> bool:
        return self._synced_at is not None

    def sync(self) -> SyncResult:
        for cache in (self._accounts, self._chat_settings, self._reports):
            cache.reload()
        self._synced_at = self._clock.now().isoformat(timespec="seconds")
        result = SyncResult(len(self._accounts.all()), self._chat_settings.chat_id,
                            self._reports.reported_today(), self._messenger.reads_group_messages())
        logger.info("таблица синхронизирована: %s", result)
        if not result.reads_group_messages:
            logger.warning("privacy mode включён — из группы приходят только команды, отчёты не дойдут. "
                           "@BotFather → /setprivacy → Disable, затем заново добавить бота в группу")
        return result

    @property
    def health_name(self) -> str:
        return "sheet"

    def health(self) -> dict:
        return {"synced_at": self._synced_at, "accounts": len(self._accounts.all()),
                "chat_id": self._chat_settings.chat_id}
