from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date

from reflect_bot.domain.models import IncomingMessage, Report


@dataclass
class _TrackedReport:
    username: str
    text: str


class ReportLedger:
    """Индекс в памяти: кто когда сдал и какой текст у каждого отчёта (чтобы ловить правки)."""

    def __init__(self):
        self._reported_on: dict[str, date] = {}
        self._reports: dict[int, _TrackedReport] = {}

    def rebuild(self, reports: Iterable[Report]) -> None:
        fresh = ReportLedger()
        for report in reports:
            fresh.record(report)
        self._reported_on, self._reports = fresh._reported_on, fresh._reports

    def record(self, report: Report) -> None:
        self._reports[report.message_id] = _TrackedReport(report.account.username, report.text)
        if not report.is_edit:
            self._reported_on[report.account.username] = report.sent_at.date()

    def has_reported(self, username: str, day: date) -> bool:
        return self._reported_on.get(username) == day

    def reported_count(self, day: date) -> int:
        return sum(1 for reported_on in self._reported_on.values() if reported_on == day)

    def is_new_edit(self, message: IncomingMessage) -> bool:
        """Правят именно отчёт этого человека, и текст действительно изменился."""
        tracked = self._reports.get(message.message_id)
        return tracked is not None and tracked.username == message.username and tracked.text != message.text
