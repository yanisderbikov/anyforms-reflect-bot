from gspread.utils import ValueRenderOption

from reflect_bot.infrastructure.sheets.gateway import SpreadsheetGateway, cell
from reflect_bot.interfaces.repositories import SettingsRepository


class SheetSettingsRepository(SettingsRepository):
    TITLE = "Настройки"
    HEADER = ("Ключ", "Значение")
    TEMPLATE_ROWS = (("chat_id", ""),)

    def __init__(self, gateway: SpreadsheetGateway):
        self._gateway = gateway

    def find_all(self) -> dict[str, str]:
        worksheet = self._gateway.worksheet(self.TITLE, self.HEADER, self.TEMPLATE_ROWS)
        # unformatted — чтобы длинный id группы не пришёл как «-1,00123E+12»
        rows = worksheet.get_all_values(value_render_option=ValueRenderOption.unformatted)[1:]
        return {cell(row, 0).lower(): self._as_text(row[1] if len(row) > 1 else "")
                for row in rows if cell(row, 0)}

    @staticmethod
    def _as_text(value) -> str:
        if isinstance(value, float) and value.is_integer():
            value = int(value)
        return str(value).strip()
