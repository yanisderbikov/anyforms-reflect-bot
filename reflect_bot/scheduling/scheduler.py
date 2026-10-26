from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from reflect_bot.interfaces.messaging import Alerter
from reflect_bot.interfaces.runtime import Clock, HealthIndicator
from reflect_bot.scheduling.job import ScheduledJob

logger = logging.getLogger(__name__)


@dataclass
class _JobState:
    done_for: date | None = None
    attempts: int = 0


class DailyScheduler(HealthIndicator):
    """Раз в тик проверяет, каким задачам пора. Упавшую повторяет каждый тик до max_attempts, потом аларм."""

    def __init__(self, jobs: Sequence[ScheduledJob], clock: Clock, alerter: Alerter, max_attempts: int):
        self._jobs = tuple(jobs)
        self._clock = clock
        self._alerter = alerter
        self._max_attempts = max_attempts
        self._states = {job.title: _JobState() for job in self._jobs}

    def skip_passed_slots(self) -> None:
        """Слоты, время которых прошло до старта, не досылаем — иначе каждый редеплой дублирует сообщение."""
        now = self._clock.now()
        for job in self._jobs:
            if job.at.reached_by(now):
                self._states[job.title].done_for = now.date()

    def tick(self) -> None:
        now = self._clock.now()
        for job in self._jobs:
            state = self._states[job.title]
            if state.done_for != now.date() and job.is_due(now):
                self._execute(job, state, now.date())

    def _execute(self, job: ScheduledJob, state: _JobState, today: date) -> None:
        state.attempts += 1
        try:
            job.run()
        except Exception as e:
            logger.error("%s: попытка %d/%d упала: %s", job.title, state.attempts, self._max_attempts, e)
            if state.attempts < self._max_attempts:
                return
            self._alerter.alert(f"«{job.title}» не выполнено за {self._max_attempts} попыток — {e}")
        state.done_for, state.attempts = today, 0

    @property
    def health_name(self) -> str:
        return "scheduler"

    def health(self) -> dict:
        return {job.title: {"at": str(job.at), "done_for": self._states[job.title].done_for,
                            "attempts": self._states[job.title].attempts} for job in self._jobs}
