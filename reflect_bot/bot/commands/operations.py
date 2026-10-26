from reflect_bot.bot.commands.base import Command, CommandContext
from reflect_bot.services.reminder_service import ReminderService
from reflect_bot.services.sync_service import SyncService
from reflect_bot.texts import BotTexts


class SyncCommand(Command):
    name = "/sync"
    usage = "/sync"
    description = "перечитать таблицу (аккаунты и чат)"

    def __init__(self, sync: SyncService, texts: BotTexts):
        self._sync = sync
        self._texts = texts

    def execute(self, context: CommandContext) -> str:
        return self._texts.synced(self._sync.sync())


class ChatIdCommand(Command):
    name = "/chatid"
    usage = "/chatid"
    description = "id текущего чата (вписать в лист «Настройки»)"

    def __init__(self, texts: BotTexts):
        self._texts = texts

    def execute(self, context: CommandContext) -> str:
        return self._texts.chat_id(context.message.chat_id)


class RemindCommand(Command):
    name = "/remind"
    usage = "/remind"
    description = "разослать напоминание сейчас"

    def __init__(self, reminders: ReminderService):
        self._reminders = reminders

    def execute(self, context: CommandContext) -> None:
        self._reminders.remind()


class CheckCommand(Command):
    name = "/check"
    usage = "/check"
    description = "проверить, кто не сдал, сейчас"

    def __init__(self, reminders: ReminderService, texts: BotTexts):
        self._reminders = reminders
        self._texts = texts

    def execute(self, context: CommandContext) -> str | None:
        return None if self._reminders.check_missing() else self._texts.everyone_reported()
