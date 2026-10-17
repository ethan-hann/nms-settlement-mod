import fnmatch
from pathlib import Path

import extract

# The 17 columns of a vanilla TkLocalisationEntry.
LANGUAGES = [
    "English", "French", "Italian", "German", "Spanish", "Russian", "Polish", "Dutch", "Portuguese",
    "LatinAmericanSpanish", "BrazilianPortuguese", "SimplifiedChinese", "TraditionalChinese", "TencentChinese",
    "Korean", "Japanese", "USEnglish",
]


def test_filters_cover_the_tables_the_mod_patches():
    needed = [
        "gcbuildingglobals*",
        "gcsettlementglobals*",
        "metadata/reality/tables/basebuilding*",
        "metadata/reality/tables/nms_basepartproducts*",
        "metadata/reality/tables/nms_reality_gcproducttable*",
        "metadata/reality/tables/settlementperkstable*",
        "gcdebugoptions*",
        "metadata/simulation/missions/tables/missiontable*",
        "metadata/simulation/missions/tables/modmissiontable*",
        "metadata/gamestate/difficultyconfig*",
        "metadata/gamestate/defaultsavedata*",
        "metadata/simulation/missions/tables/npcmissiontable*",
        "metadata/simulation/missions/tables/fleetmissiontable*",
        "metadata/reality/tables/costtable*",
        "metadata/reality/tables/rewardtable*",
        "metadata/reality/tables/nms_dialog_gcalienpuzzletable*",
    ]
    for pattern in needed:
        assert pattern in extract.FILTERS


def test_filters_cover_every_game_language():
    # The translation glossary reads the vanilla text of every language the game ships.
    for lang in LANGUAGES:
        name = f"language/nms_loc1_{lang.lower()}.mbin"
        assert any(fnmatch.fnmatch(name, pattern) for pattern in extract.FILTERS), name


def test_extract_command_uses_windows_paths_and_ors_every_filter():
    cmd = extract.extract_command(Path("X:/Game/GAMEDATA/PCBANKS"), Path("F:/repo/scratch/extracted"))
    assert "/" not in cmd[-1] and cmd[-1].endswith("PCBANKS")
    assert cmd[cmd.index("-O") + 1] == str(Path("F:/repo/scratch/extracted"))
    filters = [cmd[i + 1] for i, arg in enumerate(cmd) if arg == "-f"]
    assert filters == extract.FILTERS
