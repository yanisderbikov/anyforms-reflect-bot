class AccessPolicy:
    """Супер-админ задаётся через env и в таблице не хранится."""

    def __init__(self, super_admin: str):
        self._super_admin = super_admin

    def is_admin(self, username: str) -> bool:
        return bool(username) and username == self._super_admin
