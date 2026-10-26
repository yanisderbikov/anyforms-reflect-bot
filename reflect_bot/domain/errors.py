class ReflectBotError(RuntimeError):
    """Базовое исключение сервиса."""


class ConfigError(ReflectBotError):
    pass


class ChatNotConfiguredError(ReflectBotError):
    def __init__(self):
        super().__init__("chat_id не задан в листе «Настройки»")


class MessengerError(ReflectBotError):
    pass
