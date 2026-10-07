"""Checks every data module against the extracted vanilla data and the pinned compiler."""

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

import gen_parts
import merge_preview

REPO = Path(__file__).resolve().parent.parent
SPECS = REPO / "specs"
MODS = REPO / "mod"
EXTRACTED = merge_preview.EXTRACTED
ALL_FILES = REPO / "scratch" / "all_files.txt"

EXPECTED_MODULES = ["OverseersToolkit-Probes"]

pytestmark = pytest.mark.skipif(
    not (EXTRACTED / "metadata/reality/tables/basebuildingobjectstable.MXML").is_file()
    or not merge_preview.MBIN.is_file()
    or not ALL_FILES.is_file(),
    reason="run tools/bootstrap.ps1 and tools/extract.py first",
)


def spec_of(module):
    return json.loads((SPECS / f"{module}.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def game_files():
    names = set()
    for line in ALL_FILES.read_text(encoding="utf-8", errors="replace").splitlines():
        names.add(line.strip().lower())
    return names


@pytest.fixture(scope="module")
def vanilla_loc_keys():
    keys = set()
    for f in (EXTRACTED / "language").glob("*english.MXML"):
        keys.update(re.findall(r'TkLocalisationEntry" _id="([^"]+)"', f.read_text(encoding="utf-8")))
    return keys


def module_loc_keys(module):
    keys = set(spec_of(module).get("text", {}))
    for f in (MODS / module).rglob("*.EXML"):
        if f.parent.name.upper() == "LANGUAGE":
            keys.update(re.findall(r'_id="([^"]+)"', f.read_text(encoding="utf-8")))
    return keys


@pytest.mark.parametrize("module", EXPECTED_MODULES)
def test_generated_files_match_the_spec(module):
    for rel, text in gen_parts.build(spec_of(module)).items():
        on_disk = (MODS / module / rel).read_text(encoding="utf-8")
        assert on_disk == text, f"{rel} is stale; rerun tools/gen_parts.py"


@pytest.mark.parametrize("module", EXPECTED_MODULES)
def test_every_patch_merges_and_compiles(module, tmp_path):
    results = merge_preview.preview_module(MODS / module, tmp_path)
    assert results, f"{module} has no patches"
    failures = [f"{r.patch.name}: {r.message}" for r in results if not r.ok]
    assert not failures


@pytest.mark.parametrize("module", EXPECTED_MODULES)
def test_new_parts_are_complete(module, game_files, vanilla_loc_keys):
    spec = spec_of(module)
    out = {str(k).replace("\\", "/"): ET.fromstring(v) for k, v in gen_parts.build(spec).items()}
    objects = out.get("METADATA/REALITY/TABLES/BASEBUILDINGOBJECTSTABLE.EXML")
    costs = out.get("METADATA/REALITY/TABLES/BASEBUILDINGCOSTSTABLE.EXML")
    products = out.get("METADATA/REALITY/TABLES/NMS_BASEPARTPRODUCTS.EXML")
    known_text = vanilla_loc_keys | module_loc_keys(module)
    for part in spec.get("parts", []):
        id_ = part["id"]
        assert id_.startswith("OT_"), id_
        entry = objects.find(f"Property[@name='Objects']/Property[@_id='{id_}']")
        scene = entry.find("Property[@name='PlacementScene']/Property[@name='Filename']").get("value")
        assert scene.lower() in game_files, f"{id_}: scene {scene} is not in the game files"
        groups = entry.find("Property[@name='Groups']")
        assert len(groups) > 0, f"{id_} has no build-menu group"
        assert costs.find(f"Property[@name='ObjectCosts']/Property[@_id='{id_}']") is not None
        product = products.find(f"Property[@name='Table']/Property[@_id='{id_}']")
        assert product is not None, f"{id_} has no product"
        for field in ("Name", "NameLower", "Description"):
            key = product.find(f"Property[@name='{field}']").get("value")
            assert key in known_text, f"{id_}.{field}: no text for {key}"


@pytest.mark.parametrize("module", EXPECTED_MODULES)
def test_ids_are_unique_across_modules(module):
    ids = {}
    for spec_file in SPECS.glob("*.json"):
        spec = json.loads(spec_file.read_text(encoding="utf-8"))
        for item in spec.get("parts", []):
            assert item["id"] not in ids, f"{item['id']} defined in {ids.get(item['id'])} and {spec_file.stem}"
            ids[item["id"]] = spec_file.stem
