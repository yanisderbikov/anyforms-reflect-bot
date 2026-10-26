import logging

from reflect_bot.bot.access import AccessPolicy
from reflect_bot.bot.commands.base import CommandContext, CommandLine
from reflect_bot.bot.commands.registry import CommandRegistry
from reflect_bot.bot.handlers.base import MessageHandler
from reflect_bot.domain.models import IncomingMessage
from reflect_bot.interfaces.messaging import Messenger
from reflect_bot.texts import BotTexts

logger = logging.getLogger(__name__)


class CommandMessageHandler(MessageHandler):
    def __init__(self, registry: CommandRegistry, access: AccessPolicy, messenger: Messenger, texts: BotTexts):
        self._registry = registry
        self._access = access
        self._messenger = messenger
        self._texts = texts

    def can_handle(self, message: IncomingMessage) -> bool:
        return message.is_command

    def handle(self, message: IncomingMessage) -> None:
        line = CommandLine.parse(message.text)
        if line.addressee and line.addressee != self._messenger.bot_username().lower():
            return  # команда другому боту в группе
        command = self._registry.find(line.name)
        if command is None:
            return

        is_admin = self._access.is_admin(message.username)
        if command.admin_only and not is_admin:
            if message.is_private:
                self._reply(message, self._texts.admin_only())
            return

        logger.info("команда %s от @%s", line.name, message.username)
        try:
            answer = command.execute(CommandContext(message, line.args, is_admin))
        except Exception as e:
            self._reply(message, self._texts.command_failed(e))
            raise
        if answer:
            self._reply(message, answer)

    def _reply(self, message: IncomingMessage, text: str) -> None:
        self._messenger.send_message(message.chat_id, text, reply_to=message.message_id)
