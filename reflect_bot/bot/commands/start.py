from reflect_bot.bot.commands.base import Command, CommandContext
from reflect_bot.bot.commands.registry import CommandRegistry
from reflect_bot.services.account_service import AccountService
from reflect_bot.texts import BotTexts


class StartCommand(Command):
    name = "/start"
    aliases = ("/help",)
    usage = "/start"
    description = "приветствие и список команд"
    admin_only = False

    def __init__(self, accounts: AccountService, texts: BotTexts, registry: CommandRegistry):
        self._accounts = accounts
        self._texts = texts
        self._registry = registry

    def execute(self, context: CommandContext) -> str | None:
        if context.is_admin:
            return self._texts.admin_help(self._registry.admin_help())
        if not context.message.is_private:
            return None  # в группе /start отвечаем только админу, чтобы не шуметь
        return self._texts.greeting(self._accounts.find(context.message.username))
