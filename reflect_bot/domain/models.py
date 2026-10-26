from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

EDIT_MARK = "правка"
PHOTO_MARK = "фото"
_USERNAME_PATTERN = re.compile(r"^[a-z0-9_]{4,32}$")


def normalize_username(raw: object) -> str:
    """'@Ivan_Bel ' -> 'ivan_bel'. Telegram-ники регистронезависимы."""
    return str(raw).strip().lstrip("@").lower()


def is_valid_username(username: str) -> bool:
    return bool(_USERNAME_PATTERN.match(username))


@dataclass(frozen=True)
class TimeOfDay:
    hour: int
    minute: int

    @classmethod
    def parse(cls, value: str) -> TimeOfDay:
        hour, _, minute = value.strip().partition(":")
        return cls(int(hour), int(minute or 0))

    def reached_by(self, moment: datetime) -> bool:
        return (moment.hour, moment.minute) >= (self.hour, self.minute)

    def __str__(self) -> str:
        return f"{self.hour:02d}:{self.minute:02d}"


@dataclass(frozen=True)
class Account:
    username: str
    name: str

    @property
    def mention(self) -> str:
        return f"{self.name} @{self.username}"


@dataclass(frozen=True)
class IncomingMessage:
    message_id: int
    chat_id: int
    chat_type: str
    username: str
    text: str
    sent_at: datetime
    edited_at: datetime | None = None
    has_photo: bool = False

    @property
    def is_private(self) -> bool:
        return self.chat_type == "private"

    @property
    def is_edit(self) -> bool:
        return self.edited_at is not None

    @property
    def is_command(self) -> bool:
        return not self.is_edit and self.text.startswith("/")


@dataclass(frozen=True)
class Report:
    account: Account
    message_id: int
    sent_at: datetime      # отправка исходного сообщения — по ней выбирается лист месяца
    written_at: datetime   # когда записали; для правки — время правки
    text: str
    marks: tuple[str, ...] = ()

    @classmethod
    def from_message(cls, account: Account, message: IncomingMessage) -> Report:
        marks = [EDIT_MARK] if message.is_edit else []
        if message.has_photo:
            marks.append(PHOTO_MARK)
        return cls(account, message.message_id, message.sent_at,
                   message.edited_at or message.sent_at, message.text, tuple(marks))

    @property
    def is_edit(self) -> bool:
        return EDIT_MARK in self.marks
