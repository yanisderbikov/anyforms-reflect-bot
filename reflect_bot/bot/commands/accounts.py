from reflect_bot.bot.commands.base import Command, CommandContext
from reflect_bot.domain.models import is_valid_username, normalize_username
from reflect_bot.interfaces.runtime import Clock
from reflect_bot.services.account_service import AccountService
from reflect_bot.services.report_service import ReportService
from reflect_bot.texts import BotTexts


class AddAccountCommand(Command):
    name = "/add"
    usage = "/add @username Имя"
    description = "добавить или переименовать"

    def __init__(self, accounts: AccountService, texts: BotTexts):
        self._accounts = accounts
        self._texts = texts

    def execute(self, context: CommandContext) -> str:
        raw_username, _, name = context.args.partition(" ")
        username, name = normalize_username(raw_username), name.strip()
        if not name or not is_valid_username(username):
            return self._texts.usage(self.usage)
        account, created = self._accounts.add(username, name)
        return self._texts.account_saved(account, created)


class RemoveAccountCommand(Command):
    name = "/remove"
    usage = "/remove @username"
    description = "убрать"

    def __init__(self, accounts: AccountService, texts: BotTexts):
        self._accounts = accounts
        self._texts = texts

    def execute(self, context: CommandContext) -> str:
        username = normalize_username(context.args)
        if not username:
            return self._texts.usage(self.usage)
        return self._texts.account_removed(username, self._accounts.remove(username))


class ListAccountsCommand(Command):
    name = "/users"
    usage = "/users"
    description = "список и кто сдал сегодня"

    def __init__(self, accounts: AccountService, reports: ReportService, clock: Clock, texts: BotTexts):
        self._accounts = accounts
        self._reports = reports
        self._clock = clock
        self._texts = texts

    def execute(self, context: CommandContext) -> str:
        today = self._clock.now().date()
        rows = [(account, self._reports.has_reported(account.username, today)) for account in self._accounts.all()]
        return self._texts.accounts(rows)
