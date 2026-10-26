import asyncio
from datetime import datetime

import pytest

from reflect_bot.domain.errors import MessengerError
from reflect_bot.infrastructure.runtime import MSK
from tests.conftest import ADMIN_DM, GROUP_ID, REPORT


def at(hour, minute=0, day=26):
    return datetime(2026, 10, day, hour, minute, tzinfo=MSK)


def test_reminder_at_18_mentions_only_pending(team):
    team.send("ivan_bel", REPORT)
    team.clock.moment = at(18)
    team.context.scheduler.tick()
    chat_id, text, _ = team.messenger.sent[-1]
    assert chat_id == str(GROUP_ID)
    assert text.startswith("Товарищи, день окончен")
    assert "Петя @petya" in text and "ivan_bel" not in text
    team.context.scheduler.tick()  # второй тик в тот же день — без дубля
    assert len(team.messenger.sent) == 1


def test_check_at_20_tags_missing_or_stays_silent(team):
    team.clock.moment = at(20, 5)
    team.context.scheduler.tick()
    assert team.messenger.last_text == "⏰ Не сдали отчёт за сегодня:\nБелорус @ivan_bel\nПетя @petya"
    team.send("ivan_bel", REPORT)
    team.send("petya", REPORT)
    team.messenger.sent.clear()
    team.send("boss", "/check", ADMIN_DM)
    assert team.messenger.last_text == "Все сдали ✅"


def test_weekend_is_skipped(team):
    team.clock.moment = at(18, day=31)  # суббота
    team.context.scheduler.tick()
    assert team.messenger.sent == []


def test_slots_passed_before_start_are_not_resent(team):
    team.clock.moment = at(19)
    team.context.scheduler.skip_passed_slots()
    team.context.scheduler.tick()
    assert team.messenger.sent == []


def test_failed_slot_retries_then_alerts(team, caplog):
    team.settings_repo.settings["chat_id"] = ""
    team.context.sync.sync()
    team.clock.moment = at(18)
    for _ in range(team.settings.max_attempts + 2):
        team.context.scheduler.tick()
    assert "«напоминание» не выполнено за 5 попыток" in caplog.text
    assert team.context.scheduler.health()["напоминание"]["attempts"] == 0


def test_poller_survives_errors_and_advances_offset(team):
    report = {"update_id": 10, "message": {"message_id": 10, "date": int(team.clock.now().timestamp()),
                                           "from": {"username": "ivan_bel"},
                                           "chat": {"id": GROUP_ID, "type": "supergroup"}, "text": REPORT}}
    broken = {"update_id": 11, "message": {"message_id": 11, "chat": {"id": GROUP_ID}}}  # нет date
    team.source.batches = [MessengerError("409 Conflict"), [report, broken]]
    team.context.poller._error_backoff_seconds = 0

    with pytest.raises(StopAsyncIteration):
        asyncio.run(team.context.poller.run())

    assert team.source.offsets == [None, None, 12]
    assert len(team.reports_repo.reports) == 1
    assert team.context.poller.health()["failed"] == 1
