import logging

from reflect_bot.bot.handlers.base import MessageHandler
from reflect_bot.domain.errors import MessengerError
from reflect_bot.domain.models import IncomingMessage
from reflect_bot.interfaces.messaging import Messenger
from reflect_bot.services.account_service import AccountService
from reflect_bot.services.chat_settings_service import ChatSettingsService
from reflect_bot.services.report_service import ReportOutcome, ReportService
from reflect_bot.texts import BotTexts

logger = logging.getLogger(__name__)

SAVED_REACTION = "👍"


class GroupReportHandler(MessageHandler):
    """Сообщения из общей группы от тех, кого добавил админ. Остальных не трогаем."""

    def __init__(self, accounts: AccountService, chat_settings: ChatSettingsService,
                 reports: ReportService, messenger: Messenger, texts: BotTexts):
        self._accounts = accounts
        self._chat_settings = chat_settings
        self._reports = reports
        self._messenger = messenger
        self._texts = texts

    def can_handle(self, message: IncomingMessage) -> bool:
        return (self._chat_settings.is_report_chat(message.chat_id)
                and self._accounts.find(message.username) is not None)

    def handle(self, message: IncomingMessage) -> None:
        account = self._accounts.find(message.username)
        try:
            outcome = self._reports.submit(account, message)
        except Exception:
            if not message.is_edit:
                self._messenger.send_message(message.chat_id, self._texts.report_not_saved(),
                                             reply_to=message.message_id)
            raise
        if outcome is not ReportOutcome.SAVED:
            logger.info("сообщение @%s (%s симв.%s) не отчёт: %s", message.username, len(message.text),
                        ", правка" if message.is_edit else "", outcome.value)
        elif not message.is_edit:
            self._react(message)

    def _react(self, message: IncomingMessage) -> None:
        try:
            self._messenger.react(message.chat_id, message.message_id, SAVED_REACTION)
        except MessengerError as e:
            # Реакции могут быть запрещены в группе — отчёт уже записан, это не ошибка
            logger.warning("не смог поставить %s: %s", SAVED_REACTION, e)
