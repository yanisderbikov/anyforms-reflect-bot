from __future__ import annotations

from reflect_bot.bot.commands.base import Command


class CommandRegistry:
    """Новая команда = новый класс + register(), диспетчер не меняется (OCP)."""

    def __init__(self):
        self._by_name: dict[str, Command] = {}
        self._commands: list[Command] = []

    def register(self, *commands: Command) -> CommandRegistry:
        for command in commands:
            self._commands.append(command)
            for name in (command.name, *command.aliases):
                self._by_name[name] = command
        return self

    def find(self, name: str) -> Command | None:
        return self._by_name.get(name)

    def admin_help(self) -> list[tuple[str, str]]:
        return [(command.usage, command.description) for command in self._commands if command.admin_only]
