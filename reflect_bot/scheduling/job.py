from abc import ABC, abstractmethod
from datetime import datetime
from typing import ClassVar

from reflect_bot.domain.models import TimeOfDay

SATURDAY = 5


class ScheduledJob(ABC):
    """Задача раз в день в заданное время (по умолчанию только по будням)."""

    title: ClassVar[str]
    weekdays_only: ClassVar[bool] = True

    def __init__(self, at: TimeOfDay):
        self.at = at

    def is_due(self, moment: datetime) -> bool:
        if self.weekdays_only and moment.weekday() >= SATURDAY:
            return False
        return self.at.reached_by(moment)

    @abstractmethod
    def run(self) -> None: ...
