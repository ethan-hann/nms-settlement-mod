import os
from pathlib import Path

import check_build

LOCK = {
    "game": {"steam_buildid": "25732212", "exe_file_version": "180836"},
    "mbincompiler": {"version": "v7.04.1-pre3"},
    "nmspy": {"validated_version": None},
}

ACF = '''"AppState"
{
	"appid"		"275850"
	"buildid"		"25732212"
	"TargetBuildID"		"25732212"
}
'''


def test_read_acf_buildid(tmp_path):
    acf = tmp_path / "appmanifest_275850.acf"
    acf.write_text(ACF)
    assert check_build.read_acf_buildid(acf) == "25732212"


def test_nmspy_target_build_is_the_major_version():
    assert check_build.nmspy_target_build("180383.0") == "180383"
    assert check_build.nmspy_target_build("180836.2") == "180836"


def test_exe_file_version_reads_the_version_resource():
    ping = Path(os.environ["SystemRoot"]) / "System32" / "PING.EXE"
    assert check_build.exe_file_version(ping).startswith("10.0.")


def observed(**overrides):
    base = {
        "steam_buildid": "25732212",
        "exe_file_version": "180836",
        "mbincompiler_version": "v7.04.1-pre3",
        "nmspy_latest": "180836.0",
    }
    base.update(overrides)
    return base


def test_everything_matching_reports_no_problems():
    report = check_build.compare(LOCK, observed())
    assert report.blocking == []
    assert report.warnings == []


def test_a_new_game_build_is_blocking_and_names_both_versions():
    report = check_build.compare(LOCK, observed(exe_file_version="181000", steam_buildid="26000000"))
    assert any("180836" in p and "181000" in p for p in report.blocking)
    assert any("26000000" in p for p in report.blocking)


def test_a_different_mbincompiler_is_blocking():
    report = check_build.compare(LOCK, observed(mbincompiler_version="v7.05.0"))
    assert any("v7.05.0" in p for p in report.blocking)


def test_nmspy_behind_the_game_is_a_warning_only():
    report = check_build.compare(LOCK, observed(nmspy_latest="180383.0"))
    assert report.blocking == []
    assert any("180383" in w for w in report.warnings)


def test_unknown_nmspy_version_is_a_warning():
    report = check_build.compare(LOCK, observed(nmspy_latest=None))
    assert report.blocking == []
    assert report.warnings
