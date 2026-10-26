from datetime import datetime

from reflect_bot.domain.models import Account, Report
from reflect_bot.infrastructure.runtime import MSK
from reflect_bot.infrastructure.sheets.account_repository import SheetAccountRepository
from reflect_bot.infrastructure.sheets.gateway import parse_service_account
from reflect_bot.infrastructure.sheets.report_repository import (ReportRowMapper, SheetReportRepository,
                                                                 month_sheet_title)
from reflect_bot.infrastructure.sheets.settings_repository import SheetSettingsRepository


class FakeWorksheet:
    def __init__(self, rows=()):
        self.rows = [list(r) for r in rows]

    def get_all_values(self, value_render_option=None):
        return [list(r) for r in self.rows]

    def append_row(self, values):
        self.rows.append(list(values))

    def append_rows(self, values):
        self.rows.extend(list(v) for v in values)

    def update(self, values, range_name):
        column, row = range_name[0], int(range_name[1:])
        self.rows[row - 1][ord(column) - ord("A")] = values[0][0]

    def delete_rows(self, index):
        del self.rows[index - 1]


class FakeGateway:
    """Тот же контракт, что у SpreadsheetGateway, но листы в памяти."""

    def __init__(self):
        self.sheets: dict[str, FakeWorksheet] = {}

    def find_worksheet(self, title):
        return self.sheets.get(title)

    def worksheet(self, title, header, initial_rows=()):
        if title not in self.sheets:
            self.sheets[title] = FakeWorksheet([header, *initial_rows])
        return self.sheets[title]


def test_accounts_crud():
    gateway = FakeGateway()
    repository = SheetAccountRepository(gateway)
    assert repository.save(Account("ivan_bel", "Белорус")) is True
    assert repository.save(Account("ivan_bel", "Белорус Иваныч")) is False
    gateway.sheets["Аккаунты"].append_row(["@Petya ", ""])  # админ вписал руками, без имени
    assert repository.find_all() == [Account("ivan_bel", "Белорус Иваныч"), Account("petya", "petya")]
    assert repository.delete("petya") is True and repository.delete("petya") is False


def test_settings_template_and_numeric_chat_id():
    gateway = FakeGateway()
    repository = SheetSettingsRepository(gateway)
    assert repository.find_all() == {"chat_id": ""}  # лист создан с шаблоном
    gateway.sheets["Настройки"].rows[1][1] = -1001234567890.0
    assert repository.find_all() == {"chat_id": "-1001234567890"}


def test_reports_go_to_month_sheet_and_round_trip():
    gateway = FakeGateway()
    repository = SheetReportRepository(gateway, ReportRowMapper(MSK))
    sent = datetime(2026, 10, 31, 23, 50, tzinfo=MSK)
    edited = datetime(2026, 11, 1, 9, 5, tzinfo=MSK)
    account = Account("ivan_bel", "Белорус")
    repository.save(Report(account, 42, sent, sent, "=отчёт", ()))
    repository.save(Report(account, 42, sent, edited, "отчёт v2", ("правка", "фото")))

    sheet = gateway.sheets[month_sheet_title(2026, 10)]  # правка — на листе исходного сообщения
    assert sheet.rows[0] == list(ReportRowMapper.HEADER)
    assert sheet.rows[1] == ["Белорус", "31.10.2026 23:50", "=отчёт", "", "@ivan_bel", "42"]
    assert sheet.rows[2][1:4] == ["01.11.2026 09:05", "отчёт v2", "правка, фото"]

    loaded = repository.find_by_month(2026, 10)
    assert [r.is_edit for r in loaded] == [False, True]
    assert loaded[0].sent_at == sent and loaded[1].marks == ("правка", "фото")
    assert repository.find_by_month(2026, 12) == []


def test_rows_with_broken_cells_are_skipped():
    mapper = ReportRowMapper(MSK)
    assert mapper.from_row(["Кто", "вчера", "текст", "", "@ivan_bel", "1"]) is None
    assert mapper.from_row(["Кто", "01.10.2026 10:00", "текст"]) is None


def test_service_account_json_plain_or_base64():
    assert parse_service_account('{"a": 1}') == {"a": 1}
    assert parse_service_account("eyJhIjogMX0=") == {"a": 1}
