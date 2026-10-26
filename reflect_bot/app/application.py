from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import Sequence

from reflect_bot.app.infrastructure import Infrastructure
from reflect_bot.bot.poller import LongPoller
from reflect_bot.config import Settings
from reflect_bot.infrastructure.runtime import SerialExecutor
from reflect_bot.interfaces.messaging import Alerter
from reflect_bot.interfaces.runtime import HealthIndicator
from reflect_bot.scheduling.scheduler import DailyScheduler
from reflect_bot.services.sync_service import SyncService

logger = logging.getLogger(__name__)


class Application:
    """Жизненный цикл: холодный старт (таблица -> кеш), затем long polling и расписание параллельно."""

    def __init__(self, settings: Settings, infra: Infrastructure, executor: SerialExecutor,
                 sync: SyncService, poller: LongPoller, scheduler: DailyScheduler, alerter: Alerter,
                 health: Sequence[HealthIndicator]):
        self._settings = settings
        self._infra = infra
        self._executor = executor
        self._sync = sync
        self._poller = poller
        self._scheduler = scheduler
        self._alerter = alerter
        self._health = tuple(health)
        self._task: asyncio.Task | None = None
        self._bootstrap_error: str | None = None

    async def start(self) -> None:
        self._scheduler.skip_passed_slots()
        self._task = asyncio.create_task(self._run())
        logger.info("reflect-bot стартует: супер-админы %s, напоминание %s, проверка %s МСК по будням",
                    ", ".join(f"@{u}" for u in sorted(self._settings.super_admins)),
                    self._settings.remind_at, self._settings.check_at)

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        await self._infra.update_source.close()
        self._executor.shutdown()

    def health(self) -> dict:
        return {
            "status": "UP" if self._sync.is_loaded else "STARTING",
            "bootstrap_error": self._bootstrap_error,
            "components": {indicator.health_name: indicator.health() for indicator in self._health},
        }

    async def _run(self) -> None:
        await self._bootstrap()
        await asyncio.gather(self._poller.run(), self._run_scheduler())

    async def _bootstrap(self) -> None:
        """Пока таблица не загружена, бот молчит — иначе не узнает своих."""
        while True:
            try:
                await self._executor.run(self._sync.sync)
                await self._executor.run(self._infra.messenger.bot_username)
                self._bootstrap_error = None
                return
            except Exception as e:
                if self._bootstrap_error is None:
                    await self._executor.run(self._alerter.alert, f"не могу загрузить таблицу — {e}")
                self._bootstrap_error = str(e)
                logger.error("холодный старт не удался, повтор через %ss: %s",
                             self._settings.bootstrap_retry_seconds, e)
                await asyncio.sleep(self._settings.bootstrap_retry_seconds)

    async def _run_scheduler(self) -> None:
        while True:
            await self._executor.run(self._scheduler.tick)
            await asyncio.sleep(self._settings.scheduler_tick_seconds)
