from abc import ABC, abstractmethod


class Messenger(ABC):
    @abstractmethod
    def send_message(self, chat_id: int | str, text: str, reply_to: int | None = None) -> None: ...

    @abstractmethod
    def react(self, chat_id: int | str, message_id: int, emoji: str) -> None: ...

    @abstractmethod
    def bot_username(self) -> str: ...


class UpdateSource(ABC):
    @abstractmethod
    async def fetch(self, offset: int | None) -> list[dict]:
        """Long polling: ждёт новые апдейты, начиная с offset."""

    @abstractmethod
    async def close(self) -> None: ...


class Alerter(ABC):
    """Аларм для разработчика (сервисный чат, лог)."""

    @abstractmethod
    def alert(self, text: str) -> None: ...
