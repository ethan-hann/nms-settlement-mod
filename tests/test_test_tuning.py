"""TestTuning is test-only: it speeds up decisions and asks the game to export its merged data."""

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

import merge_preview

MODULE = Path(__file__).resolve().parent.parent / "mod" / "OverseersToolkit-TestTuning"
DEBUG = MODULE / "GLOBALS" / "GCDEBUGOPTIONS.GLOBAL.EXML"


def test_the_game_is_asked_to_export_merged_mod_data_and_nothing_else_in_debug_options():
    vanilla = merge_preview.EXTRACTED / "gcdebugoptions.global.MXML"
    if not vanilla.is_file():
        pytest.skip("run tools/extract.py first")
    _, edits = merge_preview.merge(ET.parse(vanilla).getroot(), ET.parse(DEBUG).getroot())
    assert {(e["path"], e["new"]) for e in edits} == {("SaveOutModdedMetadata", "true")}
