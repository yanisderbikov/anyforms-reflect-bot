from reflect_bot.domain.models import Account
from reflect_bot.interfaces.repositories import AccountRepository
from reflect_bot.interfaces.runtime import Reloadable


class AccountService(Reloadable):
    """Аккаунты в памяти: читаем из таблицы при старте и /sync, изменения пишем сразу в оба места."""

    def __init__(self, repository: AccountRepository):
        self._repository = repository
        self._accounts: dict[str, Account] = {}

    def reload(self) -> None:
        self._accounts = {account.username: account for account in self._repository.find_all()}

    def find(self, username: str) -> Account | None:
        return self._accounts.get(username)

    def all(self) -> list[Account]:
        return list(self._accounts.values())

    def add(self, username: str, name: str) -> tuple[Account, bool]:
        account = Account(username, name)
        created = self._repository.save(account)
        self._accounts[username] = account
        return account, created

    def remove(self, username: str) -> bool:
        deleted = self._repository.delete(username)
        cached = self._accounts.pop(username, None) is not None
        return deleted or cached
