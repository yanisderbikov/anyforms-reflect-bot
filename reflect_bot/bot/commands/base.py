from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar

from reflect_bot.domain.models import IncomingMessage


@dataclass(frozen=True)
class CommandLine:
    """'/add@my_bot @ivan_bel Белорус' -> name='/add', addressee='my_bot', args='@ivan_bel Белорус'."""

    name: str
    addressee: str
    args: str

    @classmethod
    def parse(cls, text: str) -> CommandLine:
        head, _, args = text.strip().partition(" ")
        name, _, addressee = head.lower().partition("@")
        return cls(name, addressee, args.strip())


@dataclass(frozen=True)
class CommandContext:
    message: IncomingMessage
    args: str
    is_admin: bool


class Command(ABC):
    name: ClassVar[str]
    aliases: ClassVar[tuple[str, ...]] = ()
    usage: ClassVar[str]
    description: ClassVar[str]
    admin_only: ClassVar[bool] = True

    @abstractmethod
    def execute(self, context: CommandContext) -> str | None:
        """Возвращает текст ответа (reply) или None, если отвечать не нужно."""
