import json
import os
from pathlib import Path

import pytest

import nmsenv

LIBRARY_VDF = r'''"libraryfolders"
{
	"0"
	{
		"path"		"C:\\Program Files (x86)\\Steam"
		"apps"
		{
			"228980"		"1275240571"
		}
	}
	"1"
	{
		"path"		"X:\\SteamLibrary"
		"apps"
		{
			"275850"		"33471534235"
			"620"		"12759257499"
		}
	}
}
'''


def test_parse_vdf_reads_nested_blocks_and_unescapes_paths():
    data = nmsenv.parse_vdf(LIBRARY_VDF)
    assert data["libraryfolders"]["1"]["path"] == "X:\\SteamLibrary"
    assert data["libraryfolders"]["1"]["apps"]["275850"] == "33471534235"


def test_library_for_app_finds_the_library_holding_the_game():
    data = nmsenv.parse_vdf(LIBRARY_VDF)
    assert nmsenv.library_for_app(data, "275850") == Path("X:\\SteamLibrary")
    assert nmsenv.library_for_app(data, "999") is None


def test_find_game_root_prefers_an_explicit_path(tmp_path):
    game = tmp_path / "game"
    (game / "Binaries").mkdir(parents=True)
    assert nmsenv.find_game_root(explicit=game, repo_root=tmp_path, steam_path=tmp_path) == game


def test_find_game_root_uses_local_config(tmp_path):
    game = tmp_path / "configured"
    (game / "Binaries").mkdir(parents=True)
    (tmp_path / "scratch").mkdir()
    (tmp_path / "scratch/testmode.local.json").write_text(json.dumps({"game_root": str(game)}))
    assert nmsenv.find_game_root(repo_root=tmp_path, steam_path=tmp_path / "nosteam") == game


def test_find_game_root_discovers_the_steam_library(tmp_path):
    library = tmp_path / "lib"
    game = library / "steamapps/common/No Man's Sky"
    (game / "Binaries").mkdir(parents=True)
    steam = tmp_path / "steam"
    (steam / "steamapps").mkdir(parents=True)
    vdf = LIBRARY_VDF.replace("X:\\\\SteamLibrary", str(library).replace("\\", "\\\\"))
    (steam / "steamapps/libraryfolders.vdf").write_text(vdf)
    assert nmsenv.find_game_root(repo_root=tmp_path, steam_path=steam) == game


def test_find_game_root_fails_loudly_when_nothing_matches(tmp_path, monkeypatch):
    monkeypatch.delenv("NMS_GAME_ROOT", raising=False)
    with pytest.raises(nmsenv.GameNotFound):
        nmsenv.find_game_root(repo_root=tmp_path, steam_path=tmp_path / "nosteam")


def test_game_running_sees_a_process_by_image_name(fake_process):
    assert not nmsenv.game_running("OTFAKE_PROBE.exe")
    fake_process("OTFAKE_PROBE.exe")
    assert nmsenv.game_running("OTFAKE_PROBE.exe")
