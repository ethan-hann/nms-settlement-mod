import os
import subprocess
import zipfile
from pathlib import Path

import pytest

import package

REPO = Path(__file__).resolve().parent.parent


def make_module(root, name, files):
    for rel, text in files.items():
        path = root / name / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def names_in(zip_path):
    with zipfile.ZipFile(zip_path) as z:
        return sorted(z.namelist())


def test_each_module_becomes_one_zip_named_with_the_version(tmp_path):
    mods = tmp_path / "mod"
    make_module(mods, "Alpha", {"LocTable.MXML": "<a/>"})
    make_module(mods, "Beta", {"GLOBALS/X.EXML": "<b/>"})
    made = package.build(mods, tmp_path / "dist", "1.2.3", ["Alpha", "Beta"])
    assert sorted(p.name for p in made) == ["Alpha-1.2.3.zip", "Beta-1.2.3.zip"]


def test_a_zip_holds_the_module_folder_so_it_extracts_straight_into_mods(tmp_path):
    mods = tmp_path / "mod"
    make_module(mods, "Alpha", {"LocTable.MXML": "<a/>", "METADATA/T/X.EXML": "<x/>"})
    (zip_path,) = package.build(mods, tmp_path / "dist", "1.0.0", ["Alpha"])
    assert names_in(zip_path) == ["Alpha/LocTable.MXML", "Alpha/METADATA/T/X.EXML"]
    with zipfile.ZipFile(zip_path) as z:
        assert z.read("Alpha/METADATA/T/X.EXML") == b"<x/>"


def test_files_the_game_does_not_read_are_left_out(tmp_path):
    mods = tmp_path / "mod"
    make_module(mods, "Alpha", {"X.EXML": "<x/>", "notes.txt": "hi", "__pycache__/a.pyc": "", ".gitkeep": ""})
    (zip_path,) = package.build(mods, tmp_path / "dist", "1.0.0", ["Alpha"])
    assert names_in(zip_path) == ["Alpha/X.EXML"]


@pytest.mark.parametrize("bad", ["1.0", "v1.0.0", "1.0.0-", "", "1.0.0 "])
def test_a_malformed_version_is_refused(tmp_path, bad):
    mods = tmp_path / "mod"
    make_module(mods, "Alpha", {"X.EXML": "<x/>"})
    with pytest.raises(package.PackageError):
        package.build(mods, tmp_path / "dist", bad, ["Alpha"])


def test_a_missing_or_empty_module_is_refused(tmp_path):
    mods = tmp_path / "mod"
    make_module(mods, "Alpha", {"notes.txt": "hi"})
    with pytest.raises(package.PackageError):
        package.build(mods, tmp_path / "dist", "1.0.0", ["Alpha"])
    with pytest.raises(package.PackageError):
        package.build(mods, tmp_path / "dist", "1.0.0", ["Missing"])


def test_rebuilding_replaces_the_old_zip(tmp_path):
    mods = tmp_path / "mod"
    make_module(mods, "Alpha", {"X.EXML": "<x/>", "Y.EXML": "<y/>"})
    package.build(mods, tmp_path / "dist", "1.0.0", ["Alpha"])
    (mods / "Alpha" / "Y.EXML").unlink()
    (zip_path,) = package.build(mods, tmp_path / "dist", "1.0.0", ["Alpha"])
    assert names_in(zip_path) == ["Alpha/X.EXML"]


@pytest.mark.parametrize("rel", ["X.EXML", "LocTable.MXML"])
def test_a_text_file_with_crlf_line_endings_is_refused(tmp_path, rel):
    mods = tmp_path / "mod"
    path = mods / "Alpha" / rel
    path.parent.mkdir(parents=True)
    path.write_bytes(b"<x>\r\n</x>\r\n")
    with pytest.raises(package.PackageError, match=rel):
        package.build(mods, tmp_path / "dist", "1.0.0", ["Alpha"])


def test_a_binary_file_may_hold_carriage_returns(tmp_path):
    mods = tmp_path / "mod"
    path = mods / "Alpha" / "X.MBIN"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"\x00\r\n\x01")
    (zip_path,) = package.build(mods, tmp_path / "dist", "1.0.0", ["Alpha"])
    with zipfile.ZipFile(zip_path) as z:
        assert z.read("Alpha/X.MBIN") == b"\x00\r\n\x01"


def test_two_builds_of_the_same_files_are_byte_identical(tmp_path):
    mods = tmp_path / "mod"
    make_module(mods, "Alpha", {"X.EXML": "<x/>", "Y.EXML": "<y/>"})
    (first,) = package.build(mods, tmp_path / "a", "1.0.0", ["Alpha"])
    for path in (mods / "Alpha").iterdir():
        os.utime(path, (1_700_000_000, 1_700_000_000))
    (second,) = package.build(mods, tmp_path / "b", "1.0.0", ["Alpha"])
    assert first.read_bytes() == second.read_bytes()


def test_shipped_module_files_on_disk_match_the_committed_bytes():
    # A checkout that converts line endings would make the release zips differ from the repo.
    files = sorted(
        p.relative_to(REPO).as_posix()
        for name in package.SHIPPED
        for p in (REPO / "mod" / name).rglob("*")
        if p.is_file()
    )
    staged = subprocess.run(
        ["git", "ls-files", "-s", "--", *files], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout
    committed = {line.split("\t", 1)[1]: line.split()[1] for line in staged.splitlines()}
    on_disk = subprocess.run(
        ["git", "hash-object", "--no-filters", "--stdin-paths"],
        cwd=REPO, input="\n".join(files), capture_output=True, text=True, check=True,
    ).stdout.split()
    differ = [f for f, sha in zip(files, on_disk) if committed.get(f) != sha]
    assert not differ, f"differ from the committed bytes: {differ}"


def test_test_only_modules_are_never_shipped():
    test_only = {
        "OverseersToolkit-TestTuning",
        "OverseersToolkit-Probes",
        "OverseersToolkit-StoryTuning",
        "OverseersToolkit-RewardProbes",
        "OverseersToolkit-BrokenProbe",
        "OverseersToolkit-TemplateProbe",
        "OverseersToolkit-MissingIdProbe",
        "OverseersToolkit-LedgerProbes",
        "OverseersToolkit-SignProbes",
        "OverseersToolkit-LedgerSetup",
    }
    assert set(package.TEST_ONLY) == test_only
    assert not test_only & set(package.SHIPPED)


def test_the_shipped_modules_are_the_released_ones_and_fair_ledger():
    assert set(package.SHIPPED) == {
        "OverseersToolkit",
        "OverseersToolkit-Defense",
        "OverseersToolkit-SettlementDecor",
        "OverseersToolkit-SettlerStories",
        "OverseersToolkit-FairLedger",
        "OverseersToolkit-FairLedger-Rebalance",
    }


def test_every_module_in_the_repo_is_either_shipped_or_marked_test_only():
    modules = {p.name for p in (REPO / "mod").iterdir() if p.is_dir()}
    assert modules == set(package.SHIPPED) | set(package.TEST_ONLY)
    assert not set(package.SHIPPED) & set(package.TEST_ONLY)


def test_the_repo_version_is_well_formed():
    assert package.read_version(REPO / "VERSION") == "1.1.0"
