"""Apply a module's partial EXML patches to vanilla MXML and compile the result.

This models how the game merges EXML files from GAMEDATA/MODS, as seen in
installed mods:

- a list item with _id="X" edits the vanilla item with that _id, or is appended if none has it
- a list item with _index="N" edits the Nth vanilla item
- a list item with neither is appended
- _overwrite="true" on a list replaces its items
- any other property names a struct field, which must exist in vanilla

The merged MXML is then compiled with the pinned MBINCompiler, which rejects
unknown fields and malformed values. That catches patches broken by a game update.
Full .MXML files (for example LocTable.MXML) have no vanilla counterpart and are
compiled as they are.
"""

import argparse
import copy
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EXTRACTED = REPO / "scratch" / "extracted"
MBIN = REPO / "tools" / "mbincompiler" / "MBINCompiler.exe"
MOD_ROOT = REPO / "mod"
LIST_KEYS = ("_id", "_index")


class PatchError(Exception):
    pass


@dataclass
class Result:
    patch: Path
    ok: bool
    message: str = ""
    edits: list = field(default_factory=list)
    merged: Path | None = None


def _is_item(node):
    return any(k in node.attrib for k in LIST_KEYS)


def _label(node):
    if "_id" in node.attrib:
        return f"[{node.get('_id')}]"
    if "_index" in node.attrib:
        return f"[{node.get('_index')}]"
    return "[+]"


def _clean(node):
    """Copy a patch subtree into the merged tree, dropping merge directives."""
    out = copy.deepcopy(node)
    for n in out.iter():
        n.attrib.pop("_overwrite", None)
        n.tail = None
        n.text = None
    return out


def _append(parent, node):
    item = _clean(node)
    if "_id" not in item.attrib:
        item.set("_index", str(len(parent)))
    parent.append(item)


def _merge_into(target, patch, path, edits):
    """Merge the children of patch into target (both are Property-like elements)."""
    if patch.get("_overwrite") == "true":
        for child in list(target):
            target.remove(child)
        for child in patch:
            _append(target, child)
        edits.append({"path": path, "kind": "overwritten"})
        return

    for pc in patch:
        name = pc.get("name")
        if "_id" in pc.attrib:
            match = next((t for t in target if t.get("_id") == pc.get("_id")), None)
            here = f"{path}[{pc.get('_id')}]"
            if match is None:
                _append(target, pc)
                edits.append({"path": here, "kind": "added"})
            else:
                _merge_node(match, pc, here, edits)
        elif "_index" in pc.attrib:
            idx = int(pc.get("_index"))
            items = [t for t in target if _is_item(t)]
            if idx >= len(items):
                raise PatchError(f"{path}: _index {idx} out of range ({len(items)} items)")
            _merge_node(items[idx], pc, f"{path}[{idx}]", edits)
        else:
            field_match = next((t for t in target if t.get("name") == name and not _is_item(t)), None)
            if field_match is not None:
                _merge_node(field_match, pc, f"{path}.{name}" if path else name, edits)
            elif name is None or name == target.get("name") or any(_is_item(t) for t in target):
                # A list item with no key: the game appends it.
                _append(target, pc)
                edits.append({"path": f"{path}[+]", "kind": "added"})
            else:
                raise PatchError(f"{path}: no field named {name!r} in vanilla")


def _merge_node(target, patch, path, edits):
    if len(patch) == 0 and "value" in patch.attrib and len(target) == 0:
        old = target.get("value")
        new = patch.get("value")
        target.set("value", new)
        edits.append({"path": path, "kind": "changed" if old != new else "unchanged", "old": old, "new": new})
        return
    if "value" in patch.attrib and patch.get("value") != target.get("value") and len(target):
        # Struct type names must agree; a different one means the patch targets another shape.
        raise PatchError(f"{path}: type {patch.get('value')!r} does not match vanilla {target.get('value')!r}")
    _merge_into(target, patch, path, edits)


def merge(vanilla, patch):
    """Return (merged copy of vanilla, list of edits). Raises PatchError on a bad patch."""
    if patch.tag != "Data" or vanilla.tag != "Data":
        raise PatchError("patch and vanilla must both be <Data> documents")
    if patch.get("template") != vanilla.get("template"):
        raise PatchError(
            f"template {patch.get('template')!r} does not match vanilla {vanilla.get('template')!r}"
        )
    result = copy.deepcopy(vanilla)
    edits = []
    _merge_into(result, patch, "", edits)
    for e in edits:
        e["path"] = e["path"].lstrip(".")
    return result, edits


def vanilla_relpath(rel):
    """Mod paths are upper case with .EXML; extracted vanilla files are lower case with .MXML."""
    rel = Path(rel)
    name = rel.name.lower()
    stem = name[: -len(rel.suffix)] if rel.suffix else name
    return Path(*[p.lower() for p in rel.parent.parts], stem + ".MXML")


def compile_mxml(mxml, out_dir):
    proc = subprocess.run(
        [str(MBIN), "convert", "-y", "-f", "--input-format=MXML", f"--output-dir={out_dir}", str(mxml)],
        capture_output=True,
        text=True,
    )
    log = "\n".join(l for l in (proc.stdout + proc.stderr).splitlines() if "ERROR" in l or "WARN" in l)
    return proc.returncode == 0, log


def _write(tree_root, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(tree_root, space="\t")
    body = ET.tostring(tree_root, encoding="unicode")
    path.write_text('<?xml version="1.0" encoding="utf-8"?>\n' + body + "\n", encoding="utf-8")


def preview_file(patch_path, rel, out_dir, extracted=EXTRACTED):
    out_dir = Path(out_dir)
    target_rel = vanilla_relpath(rel)
    merged_path = out_dir / target_rel
    if patch_path.suffix.upper() == ".MXML":
        merged_path.parent.mkdir(parents=True, exist_ok=True)
        merged_path.write_bytes(patch_path.read_bytes())
        edits = []
    else:
        vanilla_path = Path(extracted) / target_rel
        if not vanilla_path.is_file():
            return Result(patch_path, False, f"no vanilla file at {vanilla_path}")
        try:
            merged, edits = merge(ET.parse(vanilla_path).getroot(), ET.parse(patch_path).getroot())
        except (PatchError, ET.ParseError) as e:
            return Result(patch_path, False, str(e))
        _write(merged, merged_path)
    ok, log = compile_mxml(merged_path, merged_path.parent)
    return Result(patch_path, ok, log, edits, merged_path)


def module_patches(module_dir):
    module_dir = Path(module_dir)
    for p in sorted(module_dir.rglob("*")):
        if p.is_file() and p.suffix.upper() in (".EXML", ".MXML"):
            yield p, p.relative_to(module_dir)


def preview_module(module_dir, out_dir, extracted=EXTRACTED):
    return [preview_file(p, rel, out_dir, extracted) for p, rel in module_patches(module_dir)]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("modules", nargs="*", help="module folders under mod/ (default: all)")
    args = parser.parse_args(argv)
    names = args.modules or sorted(p.name for p in MOD_ROOT.iterdir() if p.is_dir())
    failed = 0
    for name in names:
        out = REPO / "scratch" / "merged" / name
        for r in preview_module(MOD_ROOT / name, out):
            status = "ok  " if r.ok else "FAIL"
            changed = sum(1 for e in r.edits if e["kind"] != "unchanged")
            print(f"{status} {name}/{r.patch.relative_to(MOD_ROOT / name)} ({changed} edits)")
            for e in r.edits:
                if e["kind"] == "unchanged":
                    print(f"       note: {e['path']} already {e['new']} in vanilla")
            if not r.ok:
                failed += 1
                print("       " + r.message.replace("\n", "\n       "))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
