from __future__ import annotations

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

from reflect_bot.domain.errors import ReflectBotError
from reflect_bot.interfaces.messaging import Alerter, Messenger
from reflect_bot.interfaces.runtime import Clock

logger = logging.getLogger(__name__)

MSK = timezone(timedelta(hours=3))


class MoscowClock(Clock):
    def now(self) -> datetime:
        return datetime.now(MSK)


class SerialExecutor:
    """Один рабочий поток на всю блокирующую работу (gspread, Bot API).

    Апдейты и задачи расписания выполняются строго по очереди — кешам не нужны блокировки.
    """

    def __init__(self):
        self._pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="reflect-bot")

    async def run(self, func, *args):
        return await asyncio.get_running_loop().run_in_executor(self._pool, func, *args)

    def shutdown(self) -> None:
        self._pool.shutdown(wait=False, cancel_futures=True)


class TelegramAlerter(Alerter):
    def __init__(self, messenger: Messenger, chat_id: str):
        self._messenger = messenger
        self._chat_id = chat_id

    def alert(self, text: str) -> None:
        logger.error("ALERT: %s", text)
        try:
            self._messenger.send_message(self._chat_id, f"🔴 reflect-bot: {text}")
        except ReflectBotError as e:
            logger.error("аларм не доставлен: %s", e)


class LoggingAlerter(Alerter):
    """Null Object: сервисный чат не задан — алармы только в лог."""

    def alert(self, text: str) -> None:
        logger.error("ALERT: %s", text)
