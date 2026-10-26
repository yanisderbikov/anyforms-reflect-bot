from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, tzinfo

from reflect_bot.domain.models import Account, Report, normalize_username
from reflect_bot.infrastructure.sheets.gateway import SpreadsheetGateway, cell
from reflect_bot.interfaces.repositories import ReportRepository

MONTHS_RU = ("Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль",
             "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь")


def month_sheet_title(year: int, month: int) -> str:
    return f"{MONTHS_RU[month - 1]} {year}"


class ReportRowMapper:
    """Report <-> строка листа. Первые три колонки — для людей, последние две нужны боту после рестарта."""

    HEADER = ("Кто", "Когда", "Отчёт", "Пометка", "Username", "message_id")
    TIME_FORMAT = "%d.%m.%Y %H:%M"

    def __init__(self, timezone: tzinfo):
        self._timezone = timezone

    def to_row(self, report: Report) -> list[str]:
        return [report.account.name, report.written_at.strftime(self.TIME_FORMAT), report.text,
                ", ".join(report.marks), f"@{report.account.username}", str(report.message_id)]

    def from_row(self, row: Sequence) -> Report | None:
        username = normalize_username(cell(row, 4))
        if not username or not cell(row, 5).isdigit():
            return None
        try:
            written_at = datetime.strptime(cell(row, 1), self.TIME_FORMAT).replace(tzinfo=self._timezone)
        except ValueError:
            return None  # дату поправили руками — строку пропускаем
        marks = tuple(mark.strip() for mark in cell(row, 3).split(",") if mark.strip())
        return Report(Account(username, cell(row, 0)), int(cell(row, 5)),
                      written_at, written_at, cell(row, 2), marks)


class SheetReportRepository(ReportRepository):
    """По листу на месяц: «Октябрь 2026», «Ноябрь 2026», …"""

    def __init__(self, gateway: SpreadsheetGateway, mapper: ReportRowMapper):
        self._gateway = gateway
        self._mapper = mapper

    def save(self, report: Report) -> None:
        title = month_sheet_title(report.sent_at.year, report.sent_at.month)
        self._gateway.worksheet(title, self._mapper.HEADER).append_row(self._mapper.to_row(report))

    def find_by_month(self, year: int, month: int) -> list[Report]:
        worksheet = self._gateway.find_worksheet(month_sheet_title(year, month))
        if worksheet is None:
            return []
        reports = (self._mapper.from_row(row) for row in worksheet.get_all_values()[1:])
        return [report for report in reports if report is not None]
