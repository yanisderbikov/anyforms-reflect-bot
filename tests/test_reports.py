from datetime import timedelta

from tests.conftest import ADMIN_DM, GROUP_ID, REPORT


def test_first_long_message_is_report_and_gets_thumbs_up(team):
    team.send("ivan_bel", "привет всем")  # короткое — переписка
    message_id = team.send("ivan_bel", REPORT)
    assert [r.text for r in team.reports_repo.reports] == [REPORT]
    assert team.messenger.reactions == [(GROUP_ID, message_id, "👍")]
    assert team.messenger.sent == []  # никаких reply в группе


def test_second_message_same_day_is_chat(team):
    team.send("ivan_bel", REPORT)
    team.send("ivan_bel", REPORT + " и ещё немного болтовни")
    assert len(team.reports_repo.reports) == 1


def test_next_day_is_new_report(team):
    team.send("ivan_bel", REPORT)
    team.clock.moment += timedelta(days=1)
    team.send("ivan_bel", REPORT)
    assert len(team.reports_repo.reports) == 2


def test_strangers_and_other_chats_are_ignored(team):
    team.send("stranger", REPORT)
    team.send("ivan_bel", REPORT, chat_id=-100555)
    assert team.reports_repo.reports == []


def test_edit_is_saved_as_separate_row_once(team):
    message_id = team.send("ivan_bel", REPORT)
    team.send("ivan_bel", REPORT + " (уточнил)", edit_of=message_id)
    team.send("ivan_bel", REPORT + " (уточнил)", edit_of=message_id)  # тот же текст — дубль
    edits = [r for r in team.reports_repo.reports if r.is_edit]
    assert len(edits) == 1 and edits[0].marks == ("правка",)
    assert edits[0].written_at > edits[0].sent_at


def test_editing_non_report_message_is_ignored(team):
    team.send("ivan_bel", REPORT)
    chat_id = team.send("ivan_bel", "реплика")
    team.send("ivan_bel", "реплика стала длинной, но это всё равно не отчёт, а переписка", edit_of=chat_id)
    assert len(team.reports_repo.reports) == 1


def test_photo_caption_counts(team):
    team.send("petya", REPORT, photo=True)
    assert team.reports_repo.reports[0].marks == ("фото",)


def test_sheet_failure_asks_to_resend(team):
    team.reports_repo.fail_next = True
    try:
        team.send("ivan_bel", REPORT)
    except RuntimeError:
        pass
    assert "Не смог записать" in team.messenger.last_text
    team.send("ivan_bel", REPORT)  # повтор засчитывается
    assert len(team.reports_repo.reports) == 1


def test_forbidden_reactions_do_not_break_saving(team):
    team.messenger.reactions_forbidden = True
    team.send("ivan_bel", REPORT)
    assert len(team.reports_repo.reports) == 1


def test_restart_restores_who_reported_and_tracks_edits(team):
    message_id = team.send("ivan_bel", REPORT)
    team.reset_context()  # холодный старт: кеш пустой, всё из «таблицы»
    team.send("ivan_bel", REPORT + " ещё одно длинное сообщение")
    assert len(team.reports_repo.reports) == 1
    team.send("ivan_bel", REPORT + " (правка после рестарта)", edit_of=message_id)
    assert team.reports_repo.reports[-1].is_edit


def test_users_shows_today_status(team):
    team.send("ivan_bel", REPORT)
    team.send("boss", "/users", ADMIN_DM)
    assert "✅ Белорус @ivan_bel" in team.messenger.last_text
    assert "⏳ Петя @petya" in team.messenger.last_text
