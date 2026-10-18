"""Build dist/<Module>-<version>.zip for every shipped module, and the all-in-one bundle, for Nexus.

Each zip holds the module folder itself, so a player (or Vortex) extracts it straight into
GAMEDATA/MODS. Only files the game's mod loader reads go in: .EXML patches, .MBIN files and
the root LocTable.MXML.

The bundle zip holds every module it lists, file for file as in their own zips.
Versions come from versions.json at the repo root.

Usage: package.py [--out DIR] [--changed]
"""

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

import versions

REPO = Path(__file__).resolve().parent.parent

# Shipped modules are the ones versioned in versions.json, in its order.
SHIPPED = list(json.loads((REPO / "versions.json").read_text(encoding="utf-8"))["modules"])
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
    "OverseersToolkit-LedgerSetup",
    "OverseersToolkit-LedgerRising",
]

VERSION_RE = re.compile(r"\d+\.\d+\.\d+")
ZIP_DATE = (1980, 1, 1, 0, 0, 0)
BUNDLE_NAME = "OverseersToolkit-AllInOne"


class PackageError(Exception):
    pass


def _loader_reads(rel):
    suffix = rel.suffix.upper()
    if suffix == ".MXML":
        return rel.as_posix().upper() == "LOCTABLE.MXML"
    return suffix in (".EXML", ".MBIN")


def _plan(mod_root, name):
    folder = Path(mod_root) / name
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
    return name, folder, files


def _check_version(version):
    if not VERSION_RE.fullmatch(version):
        raise PackageError(f"version {version!r} is not MAJOR.MINOR.PATCH")


def _write(target, plans):
    with zipfile.ZipFile(target, "w") as z:
        for name, folder, files in plans:
            for path in files:
                # A fixed timestamp and mode, so two builds of one commit give the same zip.
                info = zipfile.ZipInfo(f"{name}/{path.relative_to(folder).as_posix()}", ZIP_DATE)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                z.writestr(info, path.read_bytes())
    return target


def build(mod_root, out_dir, version, modules):
    """One zip per module, each holding its module folder."""
    _check_version(version)
    plans = [_plan(mod_root, name) for name in modules]
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    return [_write(Path(out_dir) / f"{plan[0]}-{version}.zip", [plan]) for plan in plans]


def build_bundle(mod_root, out_dir, version, modules):
    """One zip holding every listed module folder, file for file as in the module zips."""
    _check_version(version)
    plans = [_plan(mod_root, name) for name in modules]
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    return _write(Path(out_dir) / f"{BUNDLE_NAME}-{version}.zip", plans)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default=str(REPO / "dist"))
    parser.add_argument("--changed", action="store_true", help="only modules whose version moved since the last release")
    args = parser.parse_args(argv)
    try:
        data = versions.load(REPO / "versions.json")
        names = versions.changed(data, REPO) if args.changed else list(data["modules"])
        bundle = data["bundle"]
        made = [path for name in names for path in build(REPO / "mod", Path(args.out), data["modules"][name], [name])]
        # The bundle moves whenever a module in it does, so it ships with any of them.
        if not args.changed or set(names) & set(bundle["modules"]):
            made.append(build_bundle(REPO / "mod", Path(args.out), bundle["version"], bundle["modules"]))
    except (PackageError, versions.VersionError) as e:
        print(f"refused: {e}", file=sys.stderr)
        return 1
    for path in made:
        print(f"wrote {path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
