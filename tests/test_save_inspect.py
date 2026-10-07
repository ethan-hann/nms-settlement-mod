import json
import struct

import lz4.block
import pytest

import save_inspect

MAGIC = 0xFEEDA1E5

READABLE = {
    "Version": 4720,
    "BaseContext": {
        "GameMode": 3,
        "PlayerStateData": {
            "SaveName": "Overseer test",
            "PersistentPlayerBases": [
                {
                    "Name": "Path test",
                    "BaseType": {"PersistentBaseTypes": "HomePlanetBase"},
                    "GalacticAddress": "0x10640001BD75A8",
                    "Position": [100.0, 50.0, 0.0],
                    "Objects": [
                        {"ObjectID": "^DECALPATH", "Position": [1.0, 0.0, 0.0]},
                        {"ObjectID": "^DECALPATH", "Position": [2.0, 0.0, 0.0]},
                        {"ObjectID": "^OT_PROBE", "Position": [3.0, 0.0, 0.0]},
                        {"ObjectID": "^BASE_FLAG", "Position": [0.0, 0.0, 0.0]},
                    ],
                },
                {
                    "Name": "Freighter",
                    "BaseType": {"PersistentBaseTypes": "FreighterBase"},
                    "GalacticAddress": "0x0",
                    "Position": [0.0, 0.0, 0.0],
                    "Objects": [],
                },
            ],
            "SettlementStatesV2": [
                {
                    "Name": "Gersfiel Colony",
                    "UniverseAddress": "0x10640001BD75A8",
                    "Position": [103.0, 54.0, 0.0],
                    "Stats": [10, 20, 30, 40, 50, 60, 70],
                    "Perks": ["^STARTING_NEG1", "^OT_WATCH"],
                    "PendingJudgementType": {"SettlementJudgementType": "None"},
                }
            ],
        },
    },
}


def obfuscate(value, reverse):
    if isinstance(value, dict):
        return {reverse.get(k, k): obfuscate(v, reverse) for k, v in value.items()}
    if isinstance(value, list):
        return [obfuscate(v, reverse) for v in value]
    return value


def encode_save(readable, chunk=64):
    """Write the game's container: LZ4 blocks, each behind a 16-byte header."""
    mapping = save_inspect.load_mapping()
    reverse = {v: k for k, v in mapping.items()}
    raw = json.dumps(obfuscate(readable, reverse)).encode("utf-8") + b"\0"
    out = b""
    for start in range(0, len(raw), chunk):
        block = raw[start : start + chunk]
        packed = lz4.block.compress(block, store_size=False)
        out += struct.pack("<4I", MAGIC, len(packed), len(block), 0) + packed
    return out


@pytest.fixture
def save_file(tmp_path):
    path = tmp_path / "save11.hg"
    path.write_bytes(encode_save(READABLE))
    return path


def test_fixture_really_is_obfuscated():
    reverse = {v: k for k, v in save_inspect.load_mapping().items()}
    dumped = json.dumps(obfuscate(READABLE, reverse))
    for key in ("PersistentPlayerBases", "SettlementStatesV2", "ObjectID"):
        assert key not in dumped


def test_read_save_decodes_chunks_and_restores_key_names(save_file):
    assert save_inspect.read_save(save_file) == READABLE


def test_read_save_accepts_plain_json(tmp_path):
    path = tmp_path / "save.hg"
    path.write_bytes(json.dumps({"Version": 1}).encode() + b"\0")
    assert save_inspect.read_save(path) == {"Version": 1}


def test_read_save_rejects_a_bad_chunk_header(tmp_path):
    path = tmp_path / "bad.hg"
    path.write_bytes(struct.pack("<4I", 0xDEADBEEF, 1, 1, 0) + b"x")
    with pytest.raises(ValueError):
        save_inspect.read_save(path)


def test_report_counts_mod_and_path_parts_per_base(save_file):
    report = save_inspect.report(save_inspect.read_save(save_file))
    base = report["bases"][0]
    assert base["name"] == "Path test"
    assert base["watched_parts"] == {"DECALPATH": 2, "OT_PROBE": 1}
    assert base["object_count"] == 4


def test_report_lists_settlements_with_perks_and_stats(save_file):
    report = save_inspect.report(save_inspect.read_save(save_file))
    settlement = report["settlements"][0]
    assert settlement["name"] == "Gersfiel Colony"
    assert settlement["perks"] == ["STARTING_NEG1", "OT_WATCH"]
    assert settlement["stats"] == [10, 20, 30, 40, 50, 60, 70]


def test_report_measures_base_to_settlement_distance_on_the_same_planet(save_file):
    report = save_inspect.report(save_inspect.read_save(save_file))
    near = report["bases"][0]["nearest_settlement"]
    assert near["name"] == "Gersfiel Colony"
    assert near["distance"] == pytest.approx(5.0)
    assert report["bases"][1]["nearest_settlement"] is None
