from reflect_bot.domain.models import TimeOfDay
from reflect_bot.scheduling.job import ScheduledJob
from reflect_bot.services.reminder_service import ReminderService


class ReminderJob(ScheduledJob):
    title = "напоминание"

    def __init__(self, at: TimeOfDay, reminders: ReminderService):
        super().__init__(at)
        self._reminders = reminders

    def run(self) -> None:
        self._reminders.remind()


class MissingReportsJob(ScheduledJob):
    title = "проверка сдачи"

    def __init__(self, at: TimeOfDay, reminders: ReminderService):
        super().__init__(at)
        self._reminders = reminders

    def run(self) -> None:
        self._reminders.check_missing()
