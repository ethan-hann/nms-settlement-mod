"""Decode a copied save file and report the facts a test session should have produced.

Only ever point this at copies in scratch/saves/, never at the live save folder.
The container is LZ4 blocks, each behind a 16-byte header starting with
0xFEEDA1E5; keys are obfuscated and restored with MBINCompiler's mapping.json.
"""

import argparse
import json
import math
import re
import struct
import sys
from collections import Counter
from pathlib import Path

import lz4.block

MAGIC = 0xFEEDA1E5
MAPPING = Path(__file__).resolve().parent / "mbincompiler" / "mapping.json"

# Part IDs worth counting in every base: this mod's parts plus the vanilla parts the probes use.
WATCHED_PREFIXES = ("OT_",)
WATCHED_IDS = {"DECALPATH", "BUILDPAVING", "BUILDPAVING_BIG", "S_FLOOR_Q", "S_TRIFLOOR_Q"}


def load_mapping(path=MAPPING):
    return {e["Key"]: e["Value"] for e in json.loads(Path(path).read_text(encoding="utf-8"))["Mapping"]}


def _decode_keys(value, mapping):
    if isinstance(value, dict):
        return {mapping.get(k, k): _decode_keys(v, mapping) for k, v in value.items()}
    if isinstance(value, list):
        return [_decode_keys(v, mapping) for v in value]
    return value


def read_save(path, mapping=None):
    data = Path(path).read_bytes()
    if data.lstrip()[:1] == b"{":
        raw = data
    else:
        chunks = []
        pos = 0
        while pos < len(data):
            if len(data) - pos < 16:
                raise ValueError(f"truncated chunk header at byte {pos}")
            magic, packed, size, _ = struct.unpack_from("<4I", data, pos)
            if magic != MAGIC:
                raise ValueError(f"bad chunk magic {magic:#x} at byte {pos}")
            pos += 16
            chunks.append(lz4.block.decompress(data[pos : pos + packed], uncompressed_size=size))
            pos += packed
        raw = b"".join(chunks)
    obj = json.loads(raw.rstrip(b"\0").decode("utf-8", errors="surrogateescape"))
    return _decode_keys(obj, mapping if mapping is not None else load_mapping())


def find_key(tree, key):
    """First value stored under key anywhere in the tree, depth first."""
    if isinstance(tree, dict):
        if key in tree:
            return tree[key]
        children = tree.values()
    elif isinstance(tree, list):
        children = tree
    else:
        return None
    for child in children:
        found = find_key(child, key)
        if found is not None:
            return found
    return None


def _strip(id_):
    return id_[1:] if isinstance(id_, str) and id_.startswith("^") else id_


def _address(value):
    """Normalize the address forms seen in saves (int, hex string, nested dict) to an int."""
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value, 16) if value.lower().startswith("0x") else int(value)
        except ValueError:
            return None
    if isinstance(value, dict):
        inner = value.get("GalacticAddress", value)
        if isinstance(inner, dict) and "PlanetIndex" in inner:
            # Unverified: assumes the bit layout save editors document for the 0x... form.
            return (
                (inner.get("PlanetIndex", 0) & 0xF) << 52
                | (inner.get("SolarSystemIndex", 0) & 0xFFF) << 40
                | (inner.get("VoxelY", 0) & 0xFF) << 32
                | (inner.get("VoxelZ", 0) & 0xFFF) << 20
                | (inner.get("VoxelX", 0) & 0xFFF) << 8
            ) | (value.get("RealityIndex", 0) & 0xFF)
        return _address(inner) if inner is not value else None
    return None


def _is_watched(part_id):
    return part_id in WATCHED_IDS or part_id.startswith(WATCHED_PREFIXES)


def report(save):
    bases_raw = find_key(save, "PersistentPlayerBases") or []
    settlements_raw = find_key(save, "SettlementStatesV2") or []

    settlements = []
    for s in settlements_raw:
        settlements.append(
            {
                "name": s.get("Name"),
                "address": _address(s.get("UniverseAddress")),
                "position": s.get("Position"),
                "stats": s.get("Stats"),
                "perks": [_strip(p) for p in s.get("Perks") or []],
                "pending_judgement": find_key(s.get("PendingJudgementType"), "SettlementJudgementType"),
                "pending_custom_judgement": s.get("PendingCustomJudgementID"),
                "owner": s.get("Owner"),
            }
        )

    bases = []
    for b in bases_raw:
        objects = b.get("Objects") or []
        ids = Counter(_strip(o.get("ObjectID")) for o in objects)
        address = _address(b.get("GalacticAddress"))
        position = b.get("Position")
        nearest = None
        for s in settlements:
            if address is None or s["address"] != address or not position or not s["position"]:
                continue
            distance = math.dist(position, s["position"])
            if nearest is None or distance < nearest["distance"]:
                nearest = {"name": s["name"], "distance": distance}
        bases.append(
            {
                "name": b.get("Name"),
                "type": find_key(b.get("BaseType"), "PersistentBaseTypes"),
                "address": address,
                "position": position,
                "object_count": len(objects),
                "watched_parts": {k: v for k, v in sorted(ids.items()) if _is_watched(k)},
                "nearest_settlement": nearest,
            }
        )

    return {
        "save_name": find_key(save, "SaveName"),
        "game_mode": find_key(save, "GameMode"),
        "bases": bases,
        "settlements": settlements,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("save", help="a copied save file, e.g. scratch/saves/save11.hg")
    parser.add_argument("--json", action="store_true", help="print the report as JSON")
    parser.add_argument("--dump", help="also write the fully decoded save to this JSON file")
    args = parser.parse_args(argv)

    path = Path(args.save).resolve()
    if re.search(r"HelloGames[\\/]NMS", str(path), re.IGNORECASE):
        print("Refused: inspect a copy in scratch/saves, never the live save folder.", file=sys.stderr)
        return 3
    save = read_save(path)
    if args.dump:
        Path(args.dump).write_text(json.dumps(save, indent=1), encoding="utf-8")
    rep = report(save)
    if args.json:
        print(json.dumps(rep, indent=1))
        return 0
    print(f"save: {rep['save_name']}  mode: {rep['game_mode']}")
    for b in rep["bases"]:
        near = b["nearest_settlement"]
        where = f"{near['distance']:.0f}u from {near['name']}" if near else "no settlement on this planet"
        print(f"base {b['name']!r} ({b['type']}): {b['object_count']} objects, {where}")
        for part, n in b["watched_parts"].items():
            print(f"  {part}: {n}")
    for s in rep["settlements"]:
        print(f"settlement {s['name']!r}: perks {s['perks']}, stats {s['stats']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
