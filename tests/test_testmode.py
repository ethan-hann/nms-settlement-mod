import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

import testmode
from testmode import Env, Refused

UNIQUE_PROC = "OTFAKE_GAME.exe"


def make_env(tree, process_name=UNIQUE_PROC):
    return Env(
        game_root=tree["game"],
        save_root=tree["saves"],
        profile=tree["profile"],
        backup_root=tree["backups"],
        repo_root=tree["repo"],
        process_name=process_name,
    )


def gcmodsettings(tree):
    return tree["game"] / "Binaries/SETTINGS/GCMODSETTINGS.MXML"


def mod_flags(path):
    root = ET.fromstring(path.read_bytes().decode("utf-8-sig"))
    flags = {}
    for info in root.find("Property[@name='Data']"):
        fields = {p.get("name"): p.get("value") for p in info}
        flags[fields["Name"]] = (fields["Enabled"], fields["EnabledVR"])
    return flags


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


# --- refusal while the game runs ---------------------------------------------


def test_enter_refuses_while_nms_exe_runs_and_changes_nothing(fake_tree, fake_process):
    env = make_env(fake_tree, process_name="NMS.exe")
    game_before = snapshot(fake_tree["game"])
    saves_before = snapshot(fake_tree["saves"])
    fake_process("NMS.exe")

    with pytest.raises(Refused, match="NMS.exe"):
        testmode.enter(env, ["core"])

    assert snapshot(fake_tree["game"]) == game_before
    assert snapshot(fake_tree["saves"]) == saves_before
    assert not fake_tree["backups"].exists()
    assert not env.state_file.exists()


def test_exit_refuses_while_game_runs_and_leaves_session_open(fake_tree, fake_process):
    env = make_env(fake_tree)
    testmode.enter(env, ["core"])
    fake_process(UNIQUE_PROC)

    with pytest.raises(Refused):
        testmode.exit_session(env)

    assert (env.mods_dir / "_OTDEV_CORE").is_dir()
    assert testmode.status(env).open


def test_real_environment_is_never_built_under_pytest():
    with pytest.raises(RuntimeError):
        testmode.real_env()


# --- enter -------------------------------------------------------------------


def test_enter_writes_a_verified_backup_of_saves_and_settings(fake_tree):
    env = make_env(fake_tree)
    result = testmode.enter(env, ["core"])

    backup = Path(result.backup_dir)
    assert backup.parent == fake_tree["backups"]
    manifest = json.loads((backup / "manifest.json").read_text())["files"]
    expected = {
        "saves/" + str(p.relative_to(fake_tree["saves"])).replace("\\", "/"): sha(p)
        for p in fake_tree["saves"].rglob("*")
        if p.is_file()
    }
    expected["SETTINGS/TKGRAPHICSSETTINGS.MXML"] = sha(
        fake_tree["game"] / "Binaries/SETTINGS/TKGRAPHICSSETTINGS.MXML"
    )
    # GCMODSETTINGS was rewritten after the backup, so compare the backup copy instead.
    expected["SETTINGS/GCMODSETTINGS.MXML"] = sha(backup / "SETTINGS/GCMODSETTINGS.MXML")
    assert manifest == expected
    for rel, digest in manifest.items():
        assert sha(backup / rel) == digest


def test_enter_backs_up_gcmodsettings_before_rewriting_it(fake_tree):
    env = make_env(fake_tree)
    original = gcmodsettings(fake_tree).read_bytes()
    result = testmode.enter(env, ["core"])
    assert (Path(result.backup_dir) / "SETTINGS/GCMODSETTINGS.MXML").read_bytes() == original


def test_enter_copies_requested_modules_into_dev_folders(fake_tree):
    env = make_env(fake_tree)
    testmode.enter(env, ["core", "probes"])

    core = env.mods_dir / "_OTDEV_CORE"
    assert (core / "METADATA/REALITY/TABLES/BASEBUILDINGOBJECTSTABLE.EXML").is_file()
    assert (env.mods_dir / "_OTDEV_PROBES/LocTable.MXML").is_file()


def test_enter_disables_other_mods_and_enables_dev_mods(fake_tree):
    env = make_env(fake_tree)
    testmode.enter(env, ["core"])

    flags = mod_flags(gcmodsettings(fake_tree))
    assert flags["USER MOD A"] == ("false", "false")
    assert flags["USER MOD B"] == ("false", "false")
    assert flags["IT'S A MOD"] == ("false", "false")
    assert flags["_OTDEV_CORE"] == ("true", "true")


def test_enter_with_user_mods_keeps_their_flags(fake_tree):
    env = make_env(fake_tree)
    testmode.enter(env, ["core"], with_user_mods=True)

    flags = mod_flags(gcmodsettings(fake_tree))
    assert flags["USER MOD A"] == ("true", "true")
    assert flags["USER MOD B"] == ("false", "false")
    assert flags["_OTDEV_CORE"] == ("true", "true")


def test_enter_refuses_while_a_session_is_open(fake_tree):
    env = make_env(fake_tree)
    testmode.enter(env, ["core"])
    with pytest.raises(Refused, match="open"):
        testmode.enter(env, ["core"])


def test_enter_refuses_when_a_stale_dev_folder_exists(fake_tree):
    env = make_env(fake_tree)
    (env.mods_dir / "_OTDEV_CORE").mkdir()
    with pytest.raises(Refused, match="_OTDEV_CORE"):
        testmode.enter(env, ["core"])
    assert not fake_tree["backups"].exists()


def test_enter_refuses_unknown_module(fake_tree):
    env = make_env(fake_tree)
    with pytest.raises(Refused, match="nonsense"):
        testmode.enter(env, ["nonsense"])
    assert not fake_tree["backups"].exists()


# --- exit --------------------------------------------------------------------


def test_exit_restores_gcmodsettings_byte_for_byte(fake_tree):
    env = make_env(fake_tree)
    original = gcmodsettings(fake_tree).read_bytes()
    testmode.enter(env, ["core"])
    # The game rewrites its mod list while running.
    gcmodsettings(fake_tree).write_bytes(b"rewritten by the game")

    result = testmode.exit_session(env)

    assert result.ok, result.failures
    assert gcmodsettings(fake_tree).read_bytes() == original


def test_exit_removes_dev_folders(fake_tree):
    env = make_env(fake_tree)
    testmode.enter(env, ["core", "probes"])
    testmode.exit_session(env)
    assert not list(env.mods_dir.glob("_OTDEV_*"))


def test_exit_keeps_the_backup(fake_tree):
    env = make_env(fake_tree)
    backup = Path(testmode.enter(env, ["core"]).backup_dir)
    testmode.exit_session(env)
    assert (backup / "manifest.json").is_file()
    assert (backup / "saves/st_1/save3.hg").is_file()


def test_exit_flags_a_changed_main_save(fake_tree):
    env = make_env(fake_tree)
    testmode.enter(env, ["core"])
    (fake_tree["saves"] / "st_1/save3.hg").write_bytes(b"overwritten")

    result = testmode.exit_session(env)

    assert not result.ok
    assert any("save3.hg" in f for f in result.failures)
    st = testmode.status(env)
    assert not st.ok


def test_exit_flags_a_deleted_save(fake_tree):
    env = make_env(fake_tree)
    testmode.enter(env, ["core"])
    (fake_tree["saves"] / "st_1/save9.hg").unlink()

    result = testmode.exit_session(env)

    assert not result.ok
    assert any("save9.hg" in f for f in result.failures)


def test_exit_flags_a_change_in_another_profile(fake_tree):
    env = make_env(fake_tree)
    testmode.enter(env, ["core"])
    (fake_tree["saves"] / "st_2/storage.hg").write_bytes(b"changed")

    result = testmode.exit_session(env)

    assert not result.ok
    assert any("storage.hg" in f for f in result.failures)


def test_exit_flags_a_changed_user_mod_file(fake_tree):
    env = make_env(fake_tree)
    testmode.enter(env, ["core"])
    (env.mods_dir / "User Mod A/GLOBALS/GCBUILDINGGLOBALS.GLOBAL.EXML").write_text("<Data changed='yes' />")

    result = testmode.exit_session(env)

    assert not result.ok
    assert any("User Mod A" in f for f in result.failures)


def test_exit_flags_a_new_file_outside_dev_folders(fake_tree):
    env = make_env(fake_tree)
    testmode.enter(env, ["core"])
    (env.mods_dir / "Surprise").mkdir()
    (env.mods_dir / "Surprise/x.EXML").write_text("x")

    result = testmode.exit_session(env)

    assert not result.ok
    assert any("Surprise" in f for f in result.failures)


def test_first_session_learns_the_new_test_slot(fake_tree):
    env = make_env(fake_tree)
    testmode.enter(env, ["core"])
    profile = fake_tree["saves"] / "st_1"
    (profile / "save11.hg").write_bytes(b"creative")
    (profile / "save12.hg").write_bytes(b"creative2")
    (profile / "mf_save11.hg").write_bytes(b"m11")
    (profile / "mf_save12.hg").write_bytes(b"m12")
    (profile / "accountdata.hg").write_bytes(b"acct changed")
    (profile / "mf_accountdata.hg").write_bytes(b"macct changed")
    (profile / "cache/b.DDS").write_bytes(b"new cache")

    result = testmode.exit_session(env)

    assert result.ok, result.failures
    assert result.test_slot == 6
    assert json.loads(env.local_file.read_text())["test_slot"] == 6
    copied = {p.name for p in env.saves_copy_dir.iterdir()}
    assert {"save11.hg", "save12.hg"} <= copied


def test_first_session_refuses_to_learn_a_slot_below_six(fake_tree):
    env = make_env(fake_tree)
    testmode.enter(env, ["core"])
    (fake_tree["saves"] / "st_1/save4.hg").write_bytes(b"main save overwritten")

    result = testmode.exit_session(env)

    assert not result.ok
    assert result.test_slot is None
    assert not env.local_file.exists()


def test_later_session_allows_only_the_recorded_slot(fake_tree):
    env = make_env(fake_tree)
    env.local_file.write_text(json.dumps({"test_slot": 6}))
    profile = fake_tree["saves"] / "st_1"
    (profile / "save11.hg").write_bytes(b"creative")
    testmode.enter(env, ["core"])
    (profile / "save11.hg").write_bytes(b"creative, played")
    (profile / "save13.hg").write_bytes(b"another new game")

    result = testmode.exit_session(env)

    assert not result.ok
    assert any("save13.hg" in f for f in result.failures)
    assert not any("save11.hg" in f for f in result.failures)


# --- status ------------------------------------------------------------------


def test_status_tracks_a_clean_session(fake_tree):
    env = make_env(fake_tree)
    assert not testmode.status(env).open

    testmode.enter(env, ["core"])
    assert testmode.status(env).open

    testmode.exit_session(env)
    st = testmode.status(env)
    assert not st.open
    assert st.ok


def test_status_flags_dev_folders_left_without_a_session(fake_tree):
    env = make_env(fake_tree)
    (env.mods_dir / "_OTDEV_CORE").mkdir()
    st = testmode.status(env)
    assert not st.ok
    assert any("_OTDEV_CORE" in p for p in st.problems)


# --- helpers -----------------------------------------------------------------


@pytest.mark.parametrize(
    "name,slot",
    [
        ("save.hg", 1),
        ("save2.hg", 1),
        ("mf_save.hg", 1),
        ("save3.hg", 2),
        ("save4.hg", 2),
        ("save11.hg", 6),
        ("mf_save12.hg", 6),
        ("accountdata.hg", None),
        ("storage.hg", None),
        ("steam_autocloud.vdf", None),
    ],
)
def test_slot_of(name, slot):
    assert testmode.slot_of(name) == slot


def test_unchanged_gcmodsettings_round_trips_byte_for_byte(fake_tree):
    original = gcmodsettings(fake_tree).read_bytes()
    assert testmode.rewrite_mod_settings(original, [], keep_user_mods=True) == original
