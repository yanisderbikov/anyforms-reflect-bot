from reflect_bot.domain.models import Account, normalize_username
from reflect_bot.infrastructure.sheets.gateway import SpreadsheetGateway, cell
from reflect_bot.interfaces.repositories import AccountRepository


class SheetAccountRepository(AccountRepository):
    TITLE = "Аккаунты"
    HEADER = ("Username", "Имя")

    def __init__(self, gateway: SpreadsheetGateway):
        self._gateway = gateway

    def find_all(self) -> list[Account]:
        accounts = []
        for row in self._rows():
            username = normalize_username(cell(row, 0))
            if username:
                accounts.append(Account(username, cell(row, 1) or username))
        return accounts

    def save(self, account: Account) -> bool:
        worksheet = self._worksheet()
        row_number = self._row_number(account.username)
        if row_number is None:
            worksheet.append_row([f"@{account.username}", account.name])
            return True
        worksheet.update([[account.name]], f"B{row_number}")
        return False

    def delete(self, username: str) -> bool:
        row_number = self._row_number(username)
        if row_number is None:
            return False
        self._worksheet().delete_rows(row_number)
        return True

    def _row_number(self, username: str) -> int | None:
        for number, row in enumerate(self._rows(), start=2):
            if normalize_username(cell(row, 0)) == username:
                return number
        return None

    def _rows(self) -> list[list]:
        return self._worksheet().get_all_values()[1:]

    def _worksheet(self):
        return self._gateway.worksheet(self.TITLE, self.HEADER)
