"""Locate the game install and check whether the game is running."""

import csv
import json
import os
import re
import subprocess
from pathlib import Path

STEAM_APPID = "275850"
GAME_FOLDER = "No Man's Sky"
REPO_ROOT = Path(__file__).resolve().parent.parent

_TOKEN = re.compile(r'"((?:[^"\\]|\\.)*)"|([{}])')


class GameNotFound(Exception):
    pass


def parse_vdf(text):
    """Parse Valve's KeyValues text format into nested dicts."""
    root = {}
    stack = [root]
    key = None
    for m in _TOKEN.finditer(text):
        quoted, brace = m.groups()
        if brace == "{":
            child = {}
            stack[-1][key] = child
            stack.append(child)
            key = None
        elif brace == "}":
            stack.pop()
        elif key is None:
            key = quoted.replace("\\\\", "\\")
        else:
            stack[-1][key] = quoted.replace("\\\\", "\\")
            key = None
    return root


def library_for_app(data, appid):
    for lib in data.get("libraryfolders", {}).values():
        if isinstance(lib, dict) and appid in lib.get("apps", {}):
            return Path(lib["path"])
    return None


def _steam_path():
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as key:
            return Path(winreg.QueryValueEx(key, "SteamPath")[0])
    except OSError:
        return Path(r"C:\Program Files (x86)\Steam")


def _is_game(path):
    return path is not None and (Path(path) / "Binaries").is_dir()


def find_game_root(explicit=None, repo_root=None, steam_path=None):
    """Explicit path, then NMS_GAME_ROOT, then scratch/testmode.local.json, then Steam's library list."""
    repo_root = Path(repo_root or REPO_ROOT)
    candidates = [explicit, os.environ.get("NMS_GAME_ROOT")]
    local = repo_root / "scratch" / "testmode.local.json"
    if local.is_file():
        candidates.append(json.loads(local.read_text(encoding="utf-8")).get("game_root"))
    vdf = Path(steam_path or _steam_path()) / "steamapps" / "libraryfolders.vdf"
    if vdf.is_file():
        library = library_for_app(parse_vdf(vdf.read_text(encoding="utf-8")), STEAM_APPID)
        if library is not None:
            candidates.append(library / "steamapps" / "common" / GAME_FOLDER)
    for candidate in candidates:
        if candidate and _is_game(candidate):
            return Path(candidate)
    raise GameNotFound("No Man's Sky install not found; pass --game-root or set NMS_GAME_ROOT")


def game_running(process_name="NMS.exe"):
    """True if a process with this image name runs. Raises if the process list can't be read."""
    proc = subprocess.run(
        ["tasklist", "/FO", "CSV", "/NH", "/FI", f"IMAGENAME eq {process_name}"],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"cannot list processes (tasklist exit {proc.returncode})")
    for row in csv.reader(proc.stdout.splitlines()):
        if row and row[0].lower() == process_name.lower():
            return True
    return False
