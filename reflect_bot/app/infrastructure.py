from __future__ import annotations

from dataclasses import dataclass

from reflect_bot.config import Settings
from reflect_bot.infrastructure.runtime import MSK, MoscowClock
from reflect_bot.infrastructure.sheets.account_repository import SheetAccountRepository
from reflect_bot.infrastructure.sheets.gateway import SpreadsheetGateway
from reflect_bot.infrastructure.sheets.report_repository import ReportRowMapper, SheetReportRepository
from reflect_bot.infrastructure.sheets.settings_repository import SheetSettingsRepository
from reflect_bot.infrastructure.telegram.bot_api import TelegramBotApi
from reflect_bot.infrastructure.telegram.updates import TelegramUpdateSource
from reflect_bot.interfaces.messaging import Messenger, UpdateSource
from reflect_bot.interfaces.repositories import AccountRepository, ReportRepository, SettingsRepository
from reflect_bot.interfaces.runtime import Clock


@dataclass(frozen=True)
class Infrastructure:
    """Все внешние зависимости за интерфейсами. В тестах подменяются фейками целиком."""

    clock: Clock
    messenger: Messenger
    update_source: UpdateSource
    account_repository: AccountRepository
    settings_repository: SettingsRepository
    report_repository: ReportRepository

    @classmethod
    def production(cls, settings: Settings) -> Infrastructure:
        gateway = SpreadsheetGateway(settings.sheet_id, settings.service_account_json)
        return cls(
            clock=MoscowClock(),
            messenger=TelegramBotApi(settings.bot_token),
            update_source=TelegramUpdateSource(settings.bot_token),
            account_repository=SheetAccountRepository(gateway),
            settings_repository=SheetSettingsRepository(gateway),
            report_repository=SheetReportRepository(gateway, ReportRowMapper(MSK)),
        )
