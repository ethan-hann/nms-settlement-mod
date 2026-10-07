import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

GCMODSETTINGS_TEMPLATE = (
    '﻿<?xml version="1.0" encoding="utf-8"?>\r\n'
    '<Data template="GcModSettings">\r\n'
    '\t<Property name="DisableAllMods" value="false" />\r\n'
    '\t<Property name="Data">\r\n'
    "{entries}"
    "\t</Property>\r\n"
    "</Data>"
)

GCMODSETTINGS_ENTRY = (
    '\t\t<Property name="Data" value="GcModSettingsInfo" _index="{index}">\r\n'
    '\t\t\t<Property name="Name" value="{name}" />\r\n'
    '\t\t\t<Property name="Author" value="" />\r\n'
    '\t\t\t<Property name="ID" value="0" />\r\n'
    '\t\t\t<Property name="AuthorID" value="0" />\r\n'
    '\t\t\t<Property name="LastUpdated" value="0" />\r\n'
    '\t\t\t<Property name="ModPriority" value="{index}" />\r\n'
    '\t\t\t<Property name="Enabled" value="{enabled}" />\r\n'
    '\t\t\t<Property name="EnabledVR" value="{enabled}" />\r\n'
    '\t\t\t<Property name="Dependencies" />\r\n'
    "\t\t</Property>\r\n"
)


def gcmodsettings_bytes(mods):
    """mods: list of (name, enabled) tuples."""
    entries = "".join(
        GCMODSETTINGS_ENTRY.format(index=i, name=name, enabled="true" if on else "false")
        for i, (name, on) in enumerate(mods)
    )
    return GCMODSETTINGS_TEMPLATE.format(entries=entries).encode("utf-8")


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, str):
        data = data.encode("utf-8")
    path.write_bytes(data)


@pytest.fixture
def fake_tree(tmp_path):
    """A throwaway game install, save folder, backup root and repo checkout."""
    game = tmp_path / "game"
    write(
        game / "Binaries/SETTINGS/GCMODSETTINGS.MXML",
        gcmodsettings_bytes([("USER MOD A", True), ("USER MOD B", False), ("IT'S A MOD", True)]),
    )
    write(game / "Binaries/SETTINGS/TKGRAPHICSSETTINGS.MXML", "<Data />")
    write(game / "GAMEDATA/PCBANKS/NMSARC.fake.pak", b"HGPA")
    mods = game / "GAMEDATA/MODS"
    write(mods / "User Mod A/GLOBALS/GCBUILDINGGLOBALS.GLOBAL.EXML", "<Data a='1' />")
    write(mods / "User Mod B/METADATA/X.MBIN", b"\x00\x01")
    write(mods / "It's A Mod/LocTable.MXML", "<Data />")
    write(mods / "vortex.deployment.json", "{}")
    write(mods / "Notes.txt", "readme")

    saves = tmp_path / "saves"
    profile = saves / "st_1"
    write(profile / "save.hg", b"slot1a")
    write(profile / "save2.hg", b"slot1b")
    write(profile / "mf_save.hg", b"m")
    write(profile / "mf_save2.hg", b"m")
    for k in range(3, 11):
        write(profile / f"save{k}.hg", f"save{k}".encode())
        write(profile / f"mf_save{k}.hg", f"mf{k}".encode())
    write(profile / "accountdata.hg", b"acct")
    write(profile / "mf_accountdata.hg", b"macct")
    write(profile / "steam_autocloud.vdf", b"cloud")
    write(profile / "cache/a.DDS", b"dds")
    write(saves / "st_2/storage.hg", b"other profile")

    repo = tmp_path / "repo"
    write(repo / "mod/OverseersToolkit/METADATA/REALITY/TABLES/BASEBUILDINGOBJECTSTABLE.EXML", "<Data />")
    write(repo / "mod/OverseersToolkit-Probes/LocTable.MXML", "<Data />")
    (repo / "scratch").mkdir(parents=True)

    return {
        "game": game,
        "saves": saves,
        "profile": "st_1",
        "backups": tmp_path / "backups",
        "repo": repo,
        "tmp": tmp_path,
    }


def _tasklist_has(name):
    out = subprocess.run(
        ["tasklist", "/FO", "CSV", "/NH", "/FI", f"IMAGENAME eq {name}"],
        capture_output=True,
        text=True,
    ).stdout
    return name.lower() in out.lower()


@pytest.fixture
def fake_process(tmp_path):
    """Start a harmless process with a chosen image name (a copy of ping.exe)."""
    procs = []

    def start(name):
        exe_dir = tmp_path / "fakeproc"
        exe_dir.mkdir(exist_ok=True)
        exe = exe_dir / name
        shutil.copy(Path(os.environ["SystemRoot"]) / "System32" / "PING.EXE", exe)
        proc = subprocess.Popen(
            [str(exe), "-n", "120", "127.0.0.1"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        procs.append(proc)
        deadline = time.time() + 10
        while not _tasklist_has(name):
            if time.time() > deadline:
                raise RuntimeError(f"fake process {name} never appeared")
            time.sleep(0.2)
        return proc

    yield start
    for proc in procs:
        proc.kill()
        proc.wait()
