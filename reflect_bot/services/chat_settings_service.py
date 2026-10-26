from reflect_bot.domain.errors import ChatNotConfiguredError
from reflect_bot.interfaces.repositories import SettingsRepository
from reflect_bot.interfaces.runtime import Reloadable


class ChatSettingsService(Reloadable):
    CHAT_ID_KEY = "chat_id"

    def __init__(self, repository: SettingsRepository):
        self._repository = repository
        self._settings: dict[str, str] = {}

    def reload(self) -> None:
        self._settings = self._repository.find_all()

    @property
    def chat_id(self) -> str | None:
        return self._settings.get(self.CHAT_ID_KEY) or None

    def require_chat_id(self) -> str:
        if self.chat_id is None:
            raise ChatNotConfiguredError()
        return self.chat_id

    def is_report_chat(self, chat_id: int | str) -> bool:
        return self.chat_id is not None and str(chat_id) == self.chat_id
