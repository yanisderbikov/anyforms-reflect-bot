from __future__ import annotations

import logging
from dataclasses import dataclass

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


class SyncService(HealthIndicator):
    """Перечитывает все кеши из таблицы: холодный старт и команда /sync."""

    def __init__(self, accounts: AccountService, chat_settings: ChatSettingsService,
                 reports: ReportService, clock: Clock):
        self._accounts = accounts
        self._chat_settings = chat_settings
        self._reports = reports
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
                            self._reports.reported_today())
        logger.info("таблица синхронизирована: %s", result)
        return result

    @property
    def health_name(self) -> str:
        return "sheet"

    def health(self) -> dict:
        return {"synced_at": self._synced_at, "accounts": len(self._accounts.all()),
                "chat_id": self._chat_settings.chat_id}
