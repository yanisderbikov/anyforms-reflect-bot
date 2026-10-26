from abc import ABC, abstractmethod

from reflect_bot.domain.models import Account, Report


class AccountRepository(ABC):
    @abstractmethod
    def find_all(self) -> list[Account]: ...

    @abstractmethod
    def save(self, account: Account) -> bool:
        """Создаёт или обновляет. True — аккаунт новый."""

    @abstractmethod
    def delete(self, username: str) -> bool:
        """True — аккаунт был и удалён."""


class SettingsRepository(ABC):
    @abstractmethod
    def find_all(self) -> dict[str, str]: ...


class ReportRepository(ABC):
    @abstractmethod
    def save(self, report: Report) -> None: ...

    @abstractmethod
    def find_by_month(self, year: int, month: int) -> list[Report]: ...
