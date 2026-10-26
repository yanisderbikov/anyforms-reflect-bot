"""In-memory реализации интерфейсов — тесты не ходят ни в Google, ни в Telegram."""

from __future__ import annotations

from datetime import datetime

from reflect_bot.domain.errors import MessengerError
from reflect_bot.domain.models import Account, Report
from reflect_bot.infrastructure.runtime import MSK
from reflect_bot.interfaces.messaging import Messenger, UpdateSource
from reflect_bot.interfaces.repositories import AccountRepository, ReportRepository, SettingsRepository
from reflect_bot.interfaces.runtime import Clock


class FixedClock(Clock):
    def __init__(self, moment: datetime = datetime(2026, 10, 26, 16, 0, tzinfo=MSK)):  # понедельник
        self.moment = moment

    def now(self) -> datetime:
        return self.moment


class InMemoryAccountRepository(AccountRepository):
    def __init__(self, *accounts: Account):
        self.accounts = {a.username: a for a in accounts}

    def find_all(self) -> list[Account]:
        return list(self.accounts.values())

    def save(self, account: Account) -> bool:
        created = account.username not in self.accounts
        self.accounts[account.username] = account
        return created

    def delete(self, username: str) -> bool:
        return self.accounts.pop(username, None) is not None


class InMemorySettingsRepository(SettingsRepository):
    def __init__(self, **settings: str):
        self.settings = dict(settings)

    def find_all(self) -> dict[str, str]:
        return dict(self.settings)


class InMemoryReportRepository(ReportRepository):
    def __init__(self):
        self.reports: list[Report] = []
        self.fail_next = False

    def save(self, report: Report) -> None:
        if self.fail_next:
            self.fail_next = False
            raise RuntimeError("sheets down")
        self.reports.append(report)

    def find_by_month(self, year: int, month: int) -> list[Report]:
        return [r for r in self.reports if (r.sent_at.year, r.sent_at.month) == (year, month)]


class RecordingMessenger(Messenger):
    def __init__(self):
        self.sent: list[tuple] = []
        self.reactions: list[tuple] = []
        self.reactions_forbidden = False

    def send_message(self, chat_id, text, reply_to=None) -> None:
        self.sent.append((chat_id, text, reply_to))

    def react(self, chat_id, message_id, emoji) -> None:
        if self.reactions_forbidden:
            raise MessengerError("REACTION_INVALID")
        self.reactions.append((chat_id, message_id, emoji))

    def bot_username(self) -> str:
        return "reflect_bot"

    @property
    def last_text(self) -> str:
        return self.sent[-1][1]


class ScriptedUpdateSource(UpdateSource):
    """Отдаёт заранее заданные пачки апдейтов (или исключения), потом останавливает цикл."""

    def __init__(self, *batches):
        self.batches = list(batches)
        self.offsets: list[int | None] = []

    async def fetch(self, offset):
        self.offsets.append(offset)
        if not self.batches:
            raise StopAsyncIteration
        batch = self.batches.pop(0)
        if isinstance(batch, Exception):
            raise batch
        return batch

    async def close(self) -> None:
        pass
