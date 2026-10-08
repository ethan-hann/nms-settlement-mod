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


def test_test_only_modules_are_never_shipped():
    assert "OverseersToolkit-TestTuning" not in package.SHIPPED
    assert "OverseersToolkit-Probes" not in package.SHIPPED


def test_every_module_in_the_repo_is_either_shipped_or_marked_test_only():
    modules = {p.name for p in (REPO / "mod").iterdir() if p.is_dir()}
    assert modules == set(package.SHIPPED) | set(package.TEST_ONLY)
    assert not set(package.SHIPPED) & set(package.TEST_ONLY)


def test_the_repo_version_is_well_formed():
    assert package.read_version(REPO / "VERSION") == "1.0.0"
