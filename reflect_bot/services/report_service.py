from __future__ import annotations

import logging
from datetime import date, timedelta
from enum import Enum

from reflect_bot.domain.models import Account, IncomingMessage, Report
from reflect_bot.interfaces.repositories import ReportRepository
from reflect_bot.interfaces.runtime import Clock, HealthIndicator, Reloadable
from reflect_bot.services.report_ledger import ReportLedger

logger = logging.getLogger(__name__)


class ReportOutcome(Enum):
    """Значение — причина для лога."""
    SAVED = "записан"
    ALREADY_REPORTED = "отчёт за день уже есть — обычная переписка"
    TOO_SHORT = "короче минимума — не отчёт"
    UNKNOWN_EDIT = "правка не отчёта или без изменений"


class ReportService(Reloadable, HealthIndicator):
    """Правила: отчёт — первое за день сообщение не короче min_chars; правка отчёта — отдельной строкой."""

    def __init__(self, repository: ReportRepository, ledger: ReportLedger, clock: Clock, min_chars: int):
        self._repository = repository
        self._ledger = ledger
        self._clock = clock
        self._min_chars = min_chars
        self._saved = 0

    def reload(self) -> None:
        """Восстанавливаем индекс из листов текущего и прошлого месяца (правят и вчерашние отчёты)."""
        now = self._clock.now()
        previous = now.replace(day=1) - timedelta(days=1)
        reports = []
        for moment in (previous, now):
            reports += self._repository.find_by_month(moment.year, moment.month)
        self._ledger.rebuild(reports)

    def submit(self, account: Account, message: IncomingMessage) -> ReportOutcome:
        outcome = self._check(account, message)
        if outcome is not ReportOutcome.SAVED:
            return outcome
        report = Report.from_message(account, message)
        self._repository.save(report)
        self._ledger.record(report)
        self._saved += 1
        logger.info("отчёт @%s записан (%s)", account.username, ", ".join(report.marks) or "новый")
        return ReportOutcome.SAVED

    def has_reported(self, username: str, day: date) -> bool:
        return self._ledger.has_reported(username, day)

    def pending(self, accounts: list[Account], day: date) -> list[Account]:
        return [account for account in accounts if not self.has_reported(account.username, day)]

    def reported_today(self) -> int:
        return self._ledger.reported_count(self._clock.now().date())

    @property
    def health_name(self) -> str:
        return "reports"

    def health(self) -> dict:
        return {"saved": self._saved, "reported_today": self.reported_today()}

    def _check(self, account: Account, message: IncomingMessage) -> ReportOutcome:
        if message.is_edit:
            return ReportOutcome.SAVED if self._ledger.is_new_edit(message) else ReportOutcome.UNKNOWN_EDIT
        if self.has_reported(account.username, message.sent_at.date()):
            return ReportOutcome.ALREADY_REPORTED
        if len(message.text.strip()) < self._min_chars:
            return ReportOutcome.TOO_SHORT
        return ReportOutcome.SAVED
