from reflect_bot.bot.handlers.base import MessageHandler
from reflect_bot.domain.models import IncomingMessage
from reflect_bot.interfaces.messaging import Messenger
from reflect_bot.services.account_service import AccountService
from reflect_bot.texts import BotTexts


class PrivateChatHandler(MessageHandler):
    """Обычный текст в личке: своих отправляем в группу, чужим — приветствие «я тебя не знаю»."""

    def __init__(self, accounts: AccountService, messenger: Messenger, texts: BotTexts):
        self._accounts = accounts
        self._messenger = messenger
        self._texts = texts

    def can_handle(self, message: IncomingMessage) -> bool:
        return message.is_private

    def handle(self, message: IncomingMessage) -> None:
        if message.is_edit:
            return
        account = self._accounts.find(message.username)
        text = self._texts.reports_go_to_group() if account else self._texts.greeting(None)
        self._messenger.send_message(message.chat_id, text)
