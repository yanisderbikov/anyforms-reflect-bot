from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

from reflect_bot.domain.errors import ConfigError
from reflect_bot.domain.models import TimeOfDay, normalize_username

_REQUIRED = ("TELEGRAM_BOT_TOKEN", "SUPER_ADMIN_USERNAME", "GOOGLE_SHEET_ID", "GOOGLE_SERVICE_ACCOUNT_JSON")


@dataclass(frozen=True)
class Settings:
    bot_token: str
    super_admins: frozenset[str]
    sheet_id: str
    service_account_json: str
    alert_chat_id: str | None = None
    remind_at: TimeOfDay = TimeOfDay(18, 0)
    check_at: TimeOfDay = TimeOfDay(20, 0)
    min_report_chars: int = 30
    max_attempts: int = 5
    scheduler_tick_seconds: int = 60
    bootstrap_retry_seconds: int = 30
    log_level: str = "INFO"

    @classmethod
    def from_env(cls, env: Mapping[str, str] = os.environ) -> Settings:
        missing = [name for name in _REQUIRED if not env.get(name)]
        if missing:
            raise ConfigError(f"не заданы переменные окружения: {', '.join(missing)}")
        super_admins = frozenset(filter(None, map(normalize_username, env["SUPER_ADMIN_USERNAME"].split(","))))
        if not super_admins:
            raise ConfigError("SUPER_ADMIN_USERNAME: ни одного ника")
        return cls(
            bot_token=env["TELEGRAM_BOT_TOKEN"],
            super_admins=super_admins,
            sheet_id=env["GOOGLE_SHEET_ID"],
            service_account_json=env["GOOGLE_SERVICE_ACCOUNT_JSON"],
            alert_chat_id=env.get("TELEGRAM_ALERT_CHAT_ID") or None,
            remind_at=TimeOfDay.parse(env.get("REMIND_AT", "18:00")),
            check_at=TimeOfDay.parse(env.get("CHECK_AT", "20:00")),
            min_report_chars=int(env.get("MIN_REPORT_CHARS", "30")),
            max_attempts=int(env.get("MAX_ATTEMPTS", "5")),
            scheduler_tick_seconds=int(env.get("SCHEDULER_TICK_SECONDS", "60")),
            bootstrap_retry_seconds=int(env.get("BOOTSTRAP_RETRY_SECONDS", "30")),
            log_level=env.get("LOG_LEVEL", "INFO"),
        )
