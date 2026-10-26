import logging

from reflect_bot.bot.handlers.base import MessageHandler
from reflect_bot.domain.models import IncomingMessage
from reflect_bot.services.account_service import AccountService
from reflect_bot.services.chat_settings_service import ChatSettingsService

logger = logging.getLogger(__name__)


class SkippedMessageHandler(MessageHandler):
    """Последнее звено цепочки: никто не взял сообщение — пишем в лог почему, чтобы было что искать."""

    def __init__(self, accounts: AccountService, chat_settings: ChatSettingsService):
        self._accounts = accounts
        self._chat_settings = chat_settings

    def can_handle(self, message: IncomingMessage) -> bool:
        return True

    def handle(self, message: IncomingMessage) -> None:
        logger.info("сообщение из чата %s от @%s пропущено: %s",
                    message.chat_id, message.username or "?", self._reason(message))

    def _reason(self, message: IncomingMessage) -> str:
        if not self._chat_settings.is_report_chat(message.chat_id):
            return f"это не группа отчётов (chat_id в «Настройках»: {self._chat_settings.chat_id})"
        if not message.username:
            return "у отправителя нет username"
        return "его нет в листе «Аккаунты» — /add или /sync"
