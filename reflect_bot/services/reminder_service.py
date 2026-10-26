import logging

from reflect_bot.domain.models import Account
from reflect_bot.interfaces.messaging import Messenger
from reflect_bot.interfaces.runtime import Clock
from reflect_bot.services.account_service import AccountService
from reflect_bot.services.chat_settings_service import ChatSettingsService
from reflect_bot.services.report_service import ReportService
from reflect_bot.texts import BotTexts

logger = logging.getLogger(__name__)


class ReminderService:
    """Сообщения в общую группу: вечернее напоминание и проверка, кто не сдал."""

    def __init__(self, accounts: AccountService, reports: ReportService, chat_settings: ChatSettingsService,
                 messenger: Messenger, clock: Clock, texts: BotTexts):
        self._accounts = accounts
        self._reports = reports
        self._chat_settings = chat_settings
        self._messenger = messenger
        self._clock = clock
        self._texts = texts

    def remind(self) -> int:
        """Шлёт напоминание всем; возвращает, сколько ещё не сдали."""
        chat_id = self._chat_settings.require_chat_id()
        pending = self._pending()
        self._messenger.send_message(chat_id, self._texts.reminder(pending))
        logger.info("напоминание отправлено, ждём %d", len(pending))
        return len(pending)

    def check_missing(self) -> int:
        """Тегает тех, кто не сдал; если сдали все — молчит. Возвращает число не сдавших."""
        chat_id = self._chat_settings.require_chat_id()
        pending = self._pending()
        if pending:
            self._messenger.send_message(chat_id, self._texts.missing_reports(pending))
        logger.info("проверка сдачи: не сдали %d", len(pending))
        return len(pending)

    def _pending(self) -> list[Account]:
        return self._reports.pending(self._accounts.all(), self._clock.now().date())
