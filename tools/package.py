"""Build dist/<Module>-<version>.zip for every shipped module, ready to upload to Nexus.

Each zip holds the module folder itself, so a player (or Vortex) extracts it straight into
GAMEDATA/MODS. Only files the game's mod loader reads go in: .EXML patches, .MBIN files and
the root LocTable.MXML.

Usage: package.py [--out DIR]   (version from VERSION at the repo root)
"""

import argparse
import re
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

SHIPPED = [
    "OverseersToolkit",
    "OverseersToolkit-Defense",
    "OverseersToolkit-SettlementDecor",
    "OverseersToolkit-SettlerStories",
]
# Kept in the repo for test sessions; installing them changes how the game plays.
TEST_ONLY = [
    "OverseersToolkit-Probes",
    "OverseersToolkit-TestTuning",
    "OverseersToolkit-StoryTuning",
    "OverseersToolkit-RewardProbes",
    "OverseersToolkit-BrokenProbe",
    "OverseersToolkit-TemplateProbe",
    "OverseersToolkit-MissingIdProbe",
    "OverseersToolkit-LedgerProbes",
    "OverseersToolkit-SignProbes",
]

VERSION_RE = re.compile(r"\d+\.\d+\.\d+")
ZIP_DATE = (1980, 1, 1, 0, 0, 0)


class PackageError(Exception):
    pass


def read_version(path):
    return Path(path).read_text(encoding="utf-8").strip()


def _loader_reads(rel):
    suffix = rel.suffix.upper()
    if suffix == ".MXML":
        return rel.as_posix().upper() == "LOCTABLE.MXML"
    return suffix in (".EXML", ".MBIN")


def build(mod_root, out_dir, version, modules):
    if not VERSION_RE.fullmatch(version):
        raise PackageError(f"version {version!r} is not MAJOR.MINOR.PATCH")
    mod_root, out_dir = Path(mod_root), Path(out_dir)
    plans = []
    for name in modules:
        folder = mod_root / name
        if not folder.is_dir():
            raise PackageError(f"{name}: no module folder at {folder}")
        files = sorted(
            (p for p in folder.rglob("*") if p.is_file() and _loader_reads(p.relative_to(folder))),
            key=lambda p: p.relative_to(folder).as_posix(),
        )
        if not files:
            raise PackageError(f"{name}: no files the game would load")
        for path in files:
            if path.suffix.upper() != ".MBIN" and b"\r" in path.read_bytes():
                rel = path.relative_to(folder).as_posix()
                raise PackageError(f"{name}: {rel} has CRLF line endings; the repo stores LF (see .gitattributes)")
        plans.append((name, folder, files))
    out_dir.mkdir(parents=True, exist_ok=True)
    made = []
    for name, folder, files in plans:
        target = out_dir / f"{name}-{version}.zip"
        with zipfile.ZipFile(target, "w") as z:
            for path in files:
                # A fixed timestamp and mode, so two builds of one commit give the same zip.
                info = zipfile.ZipInfo(f"{name}/{path.relative_to(folder).as_posix()}", ZIP_DATE)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                z.writestr(info, path.read_bytes())
        made.append(target)
    return made


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default=str(REPO / "dist"))
    args = parser.parse_args(argv)
    try:
        made = build(REPO / "mod", Path(args.out), read_version(REPO / "VERSION"), SHIPPED)
    except PackageError as e:
        print(f"refused: {e}", file=sys.stderr)
        return 1
    for path in made:
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
