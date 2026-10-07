"""Rebuild scratch/extracted (decompiled MXML) and scratch/all_files.txt from the installed game.

Reads the game's .pak archives; never writes under the game folder.
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import nmsenv

REPO = nmsenv.REPO_ROOT
VENV_PY = REPO / "tools" / ".venv" / "Scripts" / "python.exe"
MBIN = REPO / "tools" / "mbincompiler" / "MBINCompiler.exe"

FILTERS = [
    "gcbuildingglobals*",
    "gcsettlementglobals*",
    "gcplacementglobals*",
    "gcterrainglobals*",
    "gcnavigationglobals*",
    "gcmultiplayerglobals*",
    "gcgameplayglobals*",
    "gcdebugoptions*",
    "metadata/reality/tables/basebuilding*",
    "metadata/reality/tables/settlementperkstable*",
    "metadata/reality/tables/nms_basepartproducts*",
    "metadata/reality/tables/nms_reality_gcproducttable*",
    "metadata/reality/tables/purchaseablebuildingblueprints*",
    "metadata/reality/tables/unlockableitemtrees*",
    "metadata/reality/tables/legacybasebuildingtable*",
    "metadata/reality/tables/rewardtable*",
    "metadata/reality/tables/costtable*",
    "metadata/simulation/npcs/npcsettlementbehaviours*",
    "metadata/simulation/solarsystem/wfcbuildings/*",
    "metadata/simulation/environment/planetbuildingtable*",
    "metadata/simulation/missions/tables/sentinelsettlementmissiontable*",
    "metadata/simulation/missions/tables/missiontable*",
    "metadata/simulation/missions/tables/modmissiontable*",
    "metadata/reality/cataloguebuilding*",
    "metadata/gamestate/difficultyconfig*",
    "language/*english*",
]


def _hgpaktool():
    return [str(VENV_PY), "-m", "hgpaktool.cli"]


def extract_command(pcbanks, out):
    """hgpaktool needs native Windows paths; filters are OR'd."""
    cmd = _hgpaktool() + ["-O", str(Path(out))]
    for pattern in FILTERS:
        cmd += ["-f", pattern]
    return cmd + [str(Path(pcbanks))]


def run(cmd, cwd=None):
    print("+ " + " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=cwd, check=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-root")
    parser.add_argument("--skip-list", action="store_true", help="do not regenerate all_files.txt")
    args = parser.parse_args(argv)

    if nmsenv.game_running():
        print("Refused: NMS.exe is running.", file=sys.stderr)
        return 3
    game = nmsenv.find_game_root(explicit=args.game_root)
    pcbanks = game / "GAMEDATA" / "PCBANKS"
    scratch = REPO / "scratch"
    out = scratch / "extracted"
    scratch.mkdir(exist_ok=True)

    if not args.skip_list:
        # hgpaktool -L writes filenames.txt into the working directory.
        run(_hgpaktool() + ["-L", "-p", str(pcbanks)], cwd=scratch)
        shutil.move(scratch / "filenames.txt", scratch / "all_files.txt")

    run(extract_command(pcbanks, out))
    run([str(MBIN), "convert", "-y", "-q", "-f", "--input-format=MBIN", str(out)])
    count = sum(1 for _ in out.rglob("*.MXML"))
    print(f"{count} MXML files in {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
