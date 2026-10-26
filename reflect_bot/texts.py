from __future__ import annotations

from typing import TYPE_CHECKING

from reflect_bot.domain.models import Account, TimeOfDay

if TYPE_CHECKING:
    from reflect_bot.services.sync_service import SyncResult


class BotTexts:
    """Все тексты бота в одном месте — правим формулировки, не трогая логику."""

    def __init__(self, remind_at: TimeOfDay):
        self._remind_at = remind_at

    # --- группа ---

    @staticmethod
    def reminder(pending: list[Account]) -> str:
        tail = "Ждём: " + ", ".join(a.mention for a in pending) if pending else "Все уже сдали — спасибо! 🙌"
        return f"Товарищи, день окончен — заполните, пожалуйста, отчёт (рефлексию) 📝\n\n{tail}"

    @staticmethod
    def missing_reports(pending: list[Account]) -> str:
        return "⏰ Не сдали отчёт за сегодня:\n" + "\n".join(a.mention for a in pending)

    @staticmethod
    def report_not_saved() -> str:
        return "⚠️ Не смог записать отчёт в таблицу — отправь, пожалуйста, ещё раз чуть позже."

    # --- личка ---

    def greeting(self, account: Account | None) -> str:
        if account is None:
            return "Привет! Я тебя пока не знаю — попроси админа добавить тебя."
        return (f"Привет, {account.name}! 👋\n\n"
                f"По будням в {self._remind_at} напомню в общей группе про отчёт. Сдать его можно "
                "в любое время дня — одним сообщением в группу. Когда запишу, поставлю 👍.")

    @staticmethod
    def reports_go_to_group() -> str:
        return "Отчёты сдаём в общей группе 🙂"

    @staticmethod
    def admin_help(commands: list[tuple[str, str]]) -> str:
        return "Привет, админ! 👋\n\n" + "\n".join(f"{usage} — {description}" for usage, description in commands)

    @staticmethod
    def admin_only() -> str:
        return "Эта команда только для админа."

    # --- ответы на команды ---

    @staticmethod
    def usage(usage: str) -> str:
        return f"Формат: {usage}"

    @staticmethod
    def account_saved(account: Account, created: bool) -> str:
        return f"✅ {account.mention} {'добавлен' if created else 'переименован'}"

    @staticmethod
    def account_removed(username: str, removed: bool) -> str:
        return f"🗑 @{username} удалён" if removed else f"@{username} и так нет в списке"

    @staticmethod
    def accounts(rows: list[tuple[Account, bool]]) -> str:
        if not rows:
            return "Пока никого нет. Добавь: /add @username Имя"
        lines = [f"{'✅' if reported else '⏳'} {account.mention}" for account, reported in rows]
        return f"Аккаунтов: {len(rows)}\n\n" + "\n".join(lines)

    @staticmethod
    def synced(result: SyncResult) -> str:
        text = (f"🔄 Таблица перечитана\nАккаунтов: {result.accounts}\n"
                f"Чат: {result.chat_id or 'не задан (лист «Настройки»)'}\n"
                f"Сдали сегодня: {result.reported_today}")
        if not result.reads_group_messages:
            text += ("\n\n⚠️ Включён privacy mode: в группе я вижу только команды, отчёты до меня не доходят. "
                     "@BotFather → /setprivacy → выбрать бота → Disable, потом удалить меня из группы "
                     "и добавить заново.")
        return text

    @staticmethod
    def chat_id(chat_id: int) -> str:
        return f"id этого чата: {chat_id}"

    @staticmethod
    def everyone_reported() -> str:
        return "Все сдали ✅"

    @staticmethod
    def command_failed(error: Exception) -> str:
        return f"⚠️ Не получилось: {error}"
