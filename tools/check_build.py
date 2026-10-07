"""Compare the installed game, MBINCompiler and the latest NMS.py with tools.lock.json.

Exit 0 when the game and tools match the lock, 1 when something blocks.
NMS.py lagging behind the game is a warning, since only the runtime module needs it.
"""

import argparse
import ctypes
import json
import re
import subprocess
import sys
import urllib.request
from ctypes import wintypes
from dataclasses import dataclass, field
from pathlib import Path

import nmsenv

LOCK_PATH = Path(__file__).resolve().parent / "tools.lock.json"


@dataclass
class Report:
    blocking: list = field(default_factory=list)
    warnings: list = field(default_factory=list)


def read_acf_buildid(path):
    data = nmsenv.parse_vdf(Path(path).read_text(encoding="utf-8"))
    return data["AppState"]["buildid"]


def nmspy_target_build(version):
    return version.split(".", 1)[0]


def exe_file_version(path):
    """The FileVersion string from a Windows executable's version resource."""
    version = ctypes.WinDLL("version")
    version.GetFileVersionInfoSizeW.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(wintypes.DWORD)]
    version.GetFileVersionInfoW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p]
    version.VerQueryValueW.argtypes = [
        ctypes.c_void_p,
        wintypes.LPCWSTR,
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(wintypes.UINT),
    ]
    size = version.GetFileVersionInfoSizeW(str(path), None)
    if not size:
        raise OSError(f"no version resource in {path}")
    buf = ctypes.create_string_buffer(size)
    if not version.GetFileVersionInfoW(str(path), 0, size, buf):
        raise OSError(f"cannot read version resource of {path}")
    ptr = ctypes.c_void_p()
    length = wintypes.UINT()
    if not version.VerQueryValueW(buf, r"\VarFileInfo\Translation", ctypes.byref(ptr), ctypes.byref(length)):
        raise OSError(f"no translation table in {path}")
    lang, codepage = ctypes.cast(ptr, ctypes.POINTER(wintypes.WORD * 2)).contents
    key = rf"\StringFileInfo\{lang:04x}{codepage:04x}\FileVersion"
    if not version.VerQueryValueW(buf, key, ctypes.byref(ptr), ctypes.byref(length)):
        raise OSError(f"no FileVersion in {path}")
    return ctypes.wstring_at(ptr, length.value).rstrip("\0")


def mbincompiler_version(exe):
    out = subprocess.run([str(exe), "version"], capture_output=True, text=True).stdout
    m = re.search(r"v\d+\.\d+\.\d+(?:-\S+)?", out)
    return m.group(0) if m else None


def latest_nmspy():
    try:
        with urllib.request.urlopen("https://pypi.org/pypi/nmspy/json", timeout=15) as resp:
            return json.load(resp)["info"]["version"]
    except OSError:
        return None


def compare(lock, observed):
    report = Report()
    game = lock["game"]
    if observed["exe_file_version"] != game["exe_file_version"]:
        report.blocking.append(
            f"NMS.exe is build {observed['exe_file_version']}, lock expects {game['exe_file_version']}: "
            "update tools, re-extract and rerun tests"
        )
    if observed["steam_buildid"] != game["steam_buildid"]:
        report.blocking.append(
            f"Steam buildid is {observed['steam_buildid']}, lock expects {game['steam_buildid']}"
        )
    want_mbin = lock["mbincompiler"]["version"]
    if observed["mbincompiler_version"] != want_mbin:
        report.blocking.append(
            f"MBINCompiler is {observed['mbincompiler_version']}, lock expects {want_mbin}: run bootstrap.ps1"
        )
    nmspy = observed.get("nmspy_latest")
    if nmspy is None:
        report.warnings.append("could not read the latest NMS.py version from PyPI")
    elif nmspy_target_build(nmspy) != observed["exe_file_version"]:
        report.warnings.append(
            f"latest NMS.py {nmspy} targets build {nmspy_target_build(nmspy)}, "
            f"game is {observed['exe_file_version']}: the runtime module must wait"
        )
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-root")
    args = parser.parse_args(argv)
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    game_root = nmsenv.find_game_root(explicit=args.game_root)
    acf = game_root.parent.parent / f"appmanifest_{nmsenv.STEAM_APPID}.acf"
    mbin_exe = nmsenv.REPO_ROOT / lock["mbincompiler"]["dir"] / "MBINCompiler.exe"
    observed = {
        "steam_buildid": read_acf_buildid(acf),
        "exe_file_version": exe_file_version(game_root / "Binaries" / "NMS.exe"),
        "mbincompiler_version": mbincompiler_version(mbin_exe) if mbin_exe.is_file() else None,
        "nmspy_latest": latest_nmspy(),
    }
    report = compare(lock, observed)
    for k, v in observed.items():
        print(f"{k}: {v}")
    for w in report.warnings:
        print(f"warning: {w}")
    for b in report.blocking:
        print(f"BLOCKING: {b}")
    print("ok" if not report.blocking else "mismatch")
    return 0 if not report.blocking else 1


if __name__ == "__main__":
    sys.exit(main())
