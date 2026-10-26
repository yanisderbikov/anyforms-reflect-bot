from reflect_bot.domain.models import Account
from tests.conftest import ADMIN_DM, GROUP_ID, USER_DM


def test_admin_adds_and_renames_account_in_sheet_and_cache(harness):
    harness.send("Boss", "/add @Ivan_Bel Белорус", ADMIN_DM)
    assert harness.messenger.last_text == "✅ Белорус @ivan_bel добавлен"
    harness.send("boss", "/add ivan_bel Белорус Иваныч", ADMIN_DM)
    assert harness.messenger.last_text == "✅ Белорус Иваныч @ivan_bel переименован"
    assert harness.accounts_repo.accounts["ivan_bel"].name == "Белорус Иваныч"
    assert harness.context.accounts.find("ivan_bel").name == "Белорус Иваныч"


def test_add_validates_input(harness):
    harness.send("boss", "/add @x", ADMIN_DM)
    assert harness.messenger.last_text == "Формат: /add @username Имя"
    harness.send("boss", "/add @ab Коротко", ADMIN_DM)
    assert harness.messenger.last_text == "Формат: /add @username Имя"


def test_non_admin_cannot_manage(harness):
    harness.send("ivan_bel", "/add @petya Петя", USER_DM)
    assert harness.messenger.last_text == "Эта команда только для админа."
    assert harness.accounts_repo.accounts == {}


def test_non_admin_command_in_group_is_silent(team):
    team.send("ivan_bel", "/users", GROUP_ID)
    assert team.messenger.sent == []


def test_command_to_another_bot_is_ignored(team):
    team.send("boss", "/users@other_bot", GROUP_ID)
    assert team.messenger.sent == []
    team.send("boss", "/users@reflect_bot", GROUP_ID)
    assert "Аккаунтов: 2" in team.messenger.last_text


def test_remove(team):
    team.send("boss", "/remove @petya", ADMIN_DM)
    assert team.messenger.last_text == "🗑 @petya удалён"
    team.send("boss", "/remove @petya", ADMIN_DM)
    assert team.messenger.last_text == "@petya и так нет в списке"


def test_sync_picks_up_manual_sheet_edits(team):
    team.settings_repo.settings["chat_id"] = "-100999"
    team.accounts_repo.save(Account("vasya", "Вася"))
    team.send("boss", "/sync", ADMIN_DM)
    assert "Аккаунтов: 3" in team.messenger.last_text and "-100999" in team.messenger.last_text


def test_start_greets_known_and_unknown(team):
    team.send("ivan_bel", "/start", USER_DM)
    assert team.messenger.last_text.startswith("Привет, Белорус! 👋")
    team.send("stranger", "/start", USER_DM)
    assert "не знаю" in team.messenger.last_text
    team.send("boss", "/help", ADMIN_DM)
    assert "/add @username Имя — добавить или переименовать" in team.messenger.last_text


def test_chatid(team):
    team.send("boss", "/chatid", GROUP_ID)
    assert team.messenger.last_text == f"id этого чата: {GROUP_ID}"


def test_private_text_is_redirected_to_group(team):
    team.send("ivan_bel", "вот мой отчёт", USER_DM)
    assert team.messenger.last_text == "Отчёты сдаём в общей группе 🙂"


def test_every_super_admin_from_env_can_manage(harness):
    harness.send("deputy", "/add @petya Петя", ADMIN_DM)
    assert harness.messenger.last_text == "✅ Петя @petya добавлен"


def test_super_admins_parsed_from_comma_separated_env():
    from reflect_bot.config import Settings
    settings = Settings.from_env({"TELEGRAM_BOT_TOKEN": "t", "GOOGLE_SHEET_ID": "s",
                                  "GOOGLE_SERVICE_ACCOUNT_JSON": "{}",
                                  "SUPER_ADMIN_USERNAME": "@Yan, ivan_bel ,, @Petya"})
    assert settings.super_admins == {"yan", "ivan_bel", "petya"}


def test_sync_warns_about_privacy_mode(team):
    team.send("boss", "/sync", ADMIN_DM)
    assert "privacy mode" not in team.messenger.last_text
    team.messenger.privacy_mode = True
    team.send("boss", "/sync", ADMIN_DM)
    assert "Включён privacy mode" in team.messenger.last_text
