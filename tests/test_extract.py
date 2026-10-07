from pathlib import Path

import extract


def test_filters_cover_the_tables_the_mod_patches():
    needed = [
        "gcbuildingglobals*",
        "gcsettlementglobals*",
        "metadata/reality/tables/basebuilding*",
        "metadata/reality/tables/nms_basepartproducts*",
        "metadata/reality/tables/nms_reality_gcproducttable*",
        "metadata/reality/tables/settlementperkstable*",
        "language/*english*",
        "metadata/simulation/missions/tables/missiontable*",
        "metadata/simulation/missions/tables/modmissiontable*",
        "metadata/gamestate/difficultyconfig*",
    ]
    for pattern in needed:
        assert pattern in extract.FILTERS


def test_extract_command_uses_windows_paths_and_ors_every_filter():
    cmd = extract.extract_command(Path("X:/Game/GAMEDATA/PCBANKS"), Path("F:/repo/scratch/extracted"))
    assert "/" not in cmd[-1] and cmd[-1].endswith("PCBANKS")
    assert cmd[cmd.index("-O") + 1] == str(Path("F:/repo/scratch/extracted"))
    filters = [cmd[i + 1] for i, arg in enumerate(cmd) if arg == "-f"]
    assert filters == extract.FILTERS
