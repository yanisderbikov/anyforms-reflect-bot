from __future__ import annotations

from reflect_bot.app.application import Application
from reflect_bot.app.infrastructure import Infrastructure
from reflect_bot.bot.access import AccessPolicy
from reflect_bot.bot.commands.accounts import AddAccountCommand, ListAccountsCommand, RemoveAccountCommand
from reflect_bot.bot.commands.operations import CheckCommand, ChatIdCommand, RemindCommand, SyncCommand
from reflect_bot.bot.commands.registry import CommandRegistry
from reflect_bot.bot.commands.start import StartCommand
from reflect_bot.bot.dispatcher import UpdateDispatcher
from reflect_bot.bot.handlers.command_handler import CommandMessageHandler
from reflect_bot.bot.handlers.private_handler import PrivateChatHandler
from reflect_bot.bot.handlers.report_handler import GroupReportHandler
from reflect_bot.bot.poller import LongPoller
from reflect_bot.config import Settings
from reflect_bot.infrastructure.runtime import MSK, LoggingAlerter, SerialExecutor, TelegramAlerter
from reflect_bot.infrastructure.telegram.updates import UpdateParser
from reflect_bot.interfaces.messaging import Alerter
from reflect_bot.scheduling.jobs import MissingReportsJob, ReminderJob
from reflect_bot.scheduling.scheduler import DailyScheduler
from reflect_bot.services.account_service import AccountService
from reflect_bot.services.chat_settings_service import ChatSettingsService
from reflect_bot.services.reminder_service import ReminderService
from reflect_bot.services.report_ledger import ReportLedger
from reflect_bot.services.report_service import ReportService
from reflect_bot.services.sync_service import SyncService
from reflect_bot.texts import BotTexts


class ApplicationContext:
    """Ручной DI — аналог @Configuration в Spring: только здесь классы узнают о конкретных реализациях."""

    def __init__(self, settings: Settings, infrastructure: Infrastructure | None = None):
        infra = infrastructure or Infrastructure.production(settings)
        self.settings = settings
        self.texts = BotTexts(settings.remind_at)
        self.alerter = self._alerter(settings, infra)

        self.accounts = AccountService(infra.account_repository)
        self.chat_settings = ChatSettingsService(infra.settings_repository)
        self.reports = ReportService(infra.report_repository, ReportLedger(), infra.clock,
                                     settings.min_report_chars)
        self.sync = SyncService(self.accounts, self.chat_settings, self.reports, infra.clock)
        self.reminders = ReminderService(self.accounts, self.reports, self.chat_settings,
                                         infra.messenger, infra.clock, self.texts)

        self.dispatcher = UpdateDispatcher(UpdateParser(MSK), [
            CommandMessageHandler(self._commands(infra), AccessPolicy(settings.super_admin),
                                  infra.messenger, self.texts),
            PrivateChatHandler(self.accounts, infra.messenger, self.texts),
            GroupReportHandler(self.accounts, self.chat_settings, self.reports, infra.messenger, self.texts),
        ])
        self.scheduler = DailyScheduler([
            ReminderJob(settings.remind_at, self.reminders),
            MissingReportsJob(settings.check_at, self.reminders),
        ], infra.clock, self.alerter, settings.max_attempts)

        executor = SerialExecutor()
        self.poller = LongPoller(infra.update_source, self.dispatcher, executor, self.alerter)
        self.application = Application(settings, infra, executor, self.sync, self.poller, self.scheduler,
                                       self.alerter, health=[self.sync, self.reports, self.poller, self.scheduler])

    def _commands(self, infra: Infrastructure) -> CommandRegistry:
        registry = CommandRegistry()
        return registry.register(
            StartCommand(self.accounts, self.texts, registry),
            AddAccountCommand(self.accounts, self.texts),
            RemoveAccountCommand(self.accounts, self.texts),
            ListAccountsCommand(self.accounts, self.reports, infra.clock, self.texts),
            SyncCommand(self.sync, self.texts),
            ChatIdCommand(self.texts),
            RemindCommand(self.reminders),
            CheckCommand(self.reminders, self.texts),
        )

    @staticmethod
    def _alerter(settings: Settings, infra: Infrastructure) -> Alerter:
        if settings.alert_chat_id:
            return TelegramAlerter(infra.messenger, settings.alert_chat_id)
        return LoggingAlerter()
