from collections.abc import Sequence

from reflect_bot.bot.handlers.base import MessageHandler
from reflect_bot.infrastructure.telegram.updates import UpdateParser


class UpdateDispatcher:
    """Разбирает апдейт и отдаёт первому подходящему обработчику — порядок в цепочке важен."""

    def __init__(self, parser: UpdateParser, handlers: Sequence[MessageHandler]):
        self._parser = parser
        self._handlers = tuple(handlers)

    def dispatch(self, update: dict) -> None:
        message = self._parser.parse(update)
        if message is None:
            return
        for handler in self._handlers:
            if handler.can_handle(message):
                handler.handle(message)
                return
