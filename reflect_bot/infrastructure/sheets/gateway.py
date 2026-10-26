from __future__ import annotations

import base64
import json
import logging
from collections.abc import Sequence

import gspread

logger = logging.getLogger(__name__)


def parse_service_account(raw: str) -> dict:
    """JSON ключа сервис-аккаунта — как есть или в base64 (Railway не любит многострочные значения)."""
    raw = raw.strip()
    if not raw.startswith("{"):
        raw = base64.b64decode(raw).decode()
    return json.loads(raw)


class SpreadsheetGateway:
    """Единая точка доступа к Google-таблице: ленивое подключение и листы по имени."""

    def __init__(self, sheet_id: str, service_account_json: str):
        self._sheet_id = sheet_id
        self._service_account_json = service_account_json
        self._spreadsheet: gspread.Spreadsheet | None = None

    def find_worksheet(self, title: str) -> gspread.Worksheet | None:
        try:
            return self._open().worksheet(title)
        except gspread.WorksheetNotFound:
            return None

    def worksheet(self, title: str, header: Sequence[str],
                  initial_rows: Sequence[Sequence[str]] = ()) -> gspread.Worksheet:
        """Лист по имени; если его нет — создаёт с шапкой и стартовыми строками."""
        existing = self.find_worksheet(title)
        if existing is not None:
            return existing
        created = self._open().add_worksheet(title, rows=1000, cols=len(header))
        created.append_rows([list(header), *map(list, initial_rows)])
        logger.info("создан лист «%s»", title)
        return created

    def _open(self) -> gspread.Spreadsheet:
        if self._spreadsheet is None:
            client = gspread.service_account_from_dict(parse_service_account(self._service_account_json))
            self._spreadsheet = client.open_by_key(self._sheet_id)
        return self._spreadsheet


def cell(row: Sequence, index: int) -> str:
    return str(row[index]).strip() if len(row) > index else ""
