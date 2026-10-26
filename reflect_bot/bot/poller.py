import asyncio
import logging

from reflect_bot.bot.dispatcher import UpdateDispatcher
from reflect_bot.domain.errors import ReflectBotError
from reflect_bot.infrastructure.runtime import SerialExecutor
from reflect_bot.interfaces.messaging import Alerter, UpdateSource
from reflect_bot.interfaces.runtime import HealthIndicator

logger = logging.getLogger(__name__)


class LongPoller(HealthIndicator):
    """Забирает апдейты и по одному отдаёт диспетчеру. Упавший апдейт не блокирует очередь."""

    def __init__(self, source: UpdateSource, dispatcher: UpdateDispatcher, executor: SerialExecutor,
                 alerter: Alerter, error_backoff_seconds: float = 5):
        self._source = source
        self._dispatcher = dispatcher
        self._executor = executor
        self._alerter = alerter
        self._error_backoff_seconds = error_backoff_seconds
        self._offset: int | None = None
        self._processed = 0
        self._failed = 0
        self._last_error: str | None = None

    async def run(self) -> None:
        while True:
            try:
                updates = await self._source.fetch(self._offset)
            except ReflectBotError as e:
                self._last_error = str(e)
                logger.warning("%s", e)
                await asyncio.sleep(self._error_backoff_seconds)
                continue
            for update in updates:
                self._offset = update["update_id"] + 1
                await self._process(update)

    async def _process(self, update: dict) -> None:
        try:
            await self._executor.run(self._dispatcher.dispatch, update)
            self._processed += 1
        except Exception as e:
            self._failed += 1
            self._last_error = str(e)
            logger.exception("апдейт %s не обработан", update.get("update_id"))
            await self._executor.run(self._alerter.alert, f"апдейт не обработан — {e}")

    @property
    def health_name(self) -> str:
        return "telegram"

    def health(self) -> dict:
        return {"offset": self._offset, "processed": self._processed,
                "failed": self._failed, "last_error": self._last_error}
