from abc import ABC, abstractmethod
from datetime import datetime


class Clock(ABC):
    @abstractmethod
    def now(self) -> datetime:
        """Текущее время в рабочем часовом поясе (МСК)."""


class Reloadable(ABC):
    """Кеш, который умеет перечитать себя из источника (холодный старт, /sync)."""

    @abstractmethod
    def reload(self) -> None: ...


class HealthIndicator(ABC):
    """Как HealthIndicator в Spring Actuator: компонент сам отчитывается о состоянии."""

    @property
    @abstractmethod
    def health_name(self) -> str: ...

    @abstractmethod
    def health(self) -> dict: ...
