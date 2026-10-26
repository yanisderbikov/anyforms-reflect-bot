from collections.abc import Iterable


class AccessPolicy:
    """Супер-админы задаются через env (через запятую) и в таблице не хранятся."""

    def __init__(self, super_admins: Iterable[str]):
        self._super_admins = frozenset(super_admins)

    def is_admin(self, username: str) -> bool:
        return username in self._super_admins
