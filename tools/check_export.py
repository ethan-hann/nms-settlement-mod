"""Check the game's merged-data export against what each module meant to change.

With the test-only SaveOutModdedMetadata flag on, the game writes the data it merged from
all mods to GAMEDATA/MODS/EXPORTED; testmode moves it to scratch/exported/<session>. For
every edit merge_preview predicts (changed fields, added entries, list appends), this looks
the result up in the export and reports what did not land.

Usage: check_export.py <exported folder> [module ...]   (default: every module under mod/)
"""

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

import merge_preview
from merge_preview import vanilla_relpath

REPO = Path(__file__).resolve().parent.parent
SEGMENT = re.compile(r"([^.\[\]]+)(?:\[([^\]]+)\])?")
ID_FIELDS = ("ID", "Id", "MissionID", "PartID")


@dataclass
class Report:
    checked: int = 0
    missing: list = field(default_factory=list)


def _segments(path):
    return [(m.group(1), m.group(2)) for m in SEGMENT.finditer(path)]


def _item(container, key):
    """A list item by _id, by an ID-like field, or by position."""
    for item in container:
        if item.get("_id") == key:
            return item
        for name in ID_FIELDS:
            f = item.find(f"Property[@name='{name}']")
            if f is not None and f.get("value") == key:
                return item
    if key.isdigit():
        items = list(container)
        index = int(key)
        return items[index] if index < len(items) else None
    return None


def resolve(root, path):
    """Follow an edit path such as Objects[DECALPATH].PlanetBaseLimit; None if absent."""
    node = root
    for name, key in _segments(path):
        node = node.find(f"Property[@name='{name}']")
        if node is None:
            return None
        if key is not None and key != "+":
            node = _item(node, key)
            if node is None:
                return None
    return node


def _same(a, b):
    try:
        return float(a) == float(b)
    except (TypeError, ValueError):
        return a == b


def find_export(exported_dir, rel):
    """The exported file for a patched game file, matched on its path without extension."""
    want = vanilla_relpath(Path(rel)).with_suffix("").as_posix().lower()
    for p in Path(exported_dir).rglob("*"):
        if not p.is_file():
            continue
        got = p.relative_to(exported_dir).with_suffix("").as_posix().lower()
        if got == want or got.endswith("/" + want):
            return p
    return None


def check_module(module_dir, exported_dir, vanilla_dir=merge_preview.EXTRACTED):
    report = Report()
    module_dir = Path(module_dir)
    for patch in sorted(module_dir.rglob("*.EXML")):
        rel = patch.relative_to(module_dir).as_posix()
        vanilla_path = Path(vanilla_dir) / vanilla_relpath(Path(rel))
        vanilla = ET.parse(vanilla_path).getroot()
        _, edits = merge_preview.merge(vanilla, ET.parse(patch).getroot())
        exported_path = find_export(exported_dir, rel)
        if exported_path is None:
            report.missing.append(f"{rel}: not in the export")
            continue
        exported = ET.parse(exported_path).getroot()
        appends = {}
        for e in edits:
            if e["kind"] == "added" and e["path"].endswith("[+]"):
                appends[e["path"][:-3]] = appends.get(e["path"][:-3], 0) + 1
        for e in edits:
            kind, path = e["kind"], e["path"]
            if kind == "unchanged" or path.endswith("[+]"):
                continue
            report.checked += 1
            node = resolve(exported, path)
            if kind == "changed":
                found = None if node is None else node.get("value")
                if not _same(found, e["new"]):
                    report.missing.append(f"{rel}: {path} expected {e['new']}, found {found}")
            elif node is None:
                report.missing.append(f"{rel}: {path} not found")
        for container, count in appends.items():
            report.checked += 1
            before = resolve(vanilla, container)
            after = resolve(exported, container)
            have = 0 if after is None else len(after)
            need = (0 if before is None else len(before)) + count
            if have < need:
                report.missing.append(f"{rel}: {container} has {have} items, expected at least {need}")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("exported")
    parser.add_argument("modules", nargs="*")
    args = parser.parse_args(argv)
    names = args.modules or sorted(p.name for p in (REPO / "mod").iterdir() if p.is_dir())
    failed = 0
    for name in names:
        report = check_module(REPO / "mod" / name, Path(args.exported))
        status = "ok  " if not report.missing else "MISS"
        print(f"{status} {name}: {report.checked} edits checked, {len(report.missing)} missing")
        for m in report.missing:
            print("       " + m)
        failed += bool(report.missing)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
