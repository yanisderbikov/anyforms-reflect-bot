from abc import ABC, abstractmethod

from reflect_bot.domain.models import IncomingMessage


class MessageHandler(ABC):
    """Звено цепочки обязанностей: первый, кто can_handle, обрабатывает сообщение."""

    @abstractmethod
    def can_handle(self, message: IncomingMessage) -> bool: ...

    @abstractmethod
    def handle(self, message: IncomingMessage) -> None: ...
