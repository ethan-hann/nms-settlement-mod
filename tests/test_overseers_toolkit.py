"""Behavior the core module promises, beyond what the generic module checks cover."""

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

import gen_parts
import merge_preview

REPO = Path(__file__).resolve().parent.parent
SPEC_FILE = REPO / "specs" / "OverseersToolkit.json"
EXTRACTED = merge_preview.EXTRACTED
ALL_FILES = REPO / "scratch" / "all_files.txt"

pytestmark = pytest.mark.skipif(
    not (EXTRACTED / "metadata/reality/tables/basebuildingobjectstable.MXML").is_file()
    or not ALL_FILES.is_file(),
    reason="run tools/bootstrap.ps1 and tools/extract.py first",
)

OBJ = "METADATA/REALITY/TABLES/BASEBUILDINGOBJECTSTABLE.EXML"
PROD = "METADATA/REALITY/TABLES/NMS_BASEPARTPRODUCTS.EXML"
SUBGROUP = ("DECORATION", "OT_SETTLEMENT")
PATH_SOURCES = {
    "OT_PATH_TILE": "S_FLOOR_Q",
    "OT_PATH_TRI": "S_TRIFLOOR_Q",
    "OT_CURB": "S_WALL_Q_H",
    "OT_LAMP": "S_STREETLAMP0",
}
SIGN_SOURCES = {
    "OT_SIGN_BAR": "S_SIGN_BAR0",
    "OT_SIGN_STAND": "STANDINGSIGN",
    "OT_BILLBOARD": "BILLBOARD",
    "OT_HOLO_SMALL1": "HOLO_SMALL1",
    "OT_HOLO_SMALL2": "HOLO_SMALL2",
    "OT_HOLO_SMALL3": "HOLO_SMALL3",
    "OT_HOLO_MED1": "HOLO_MED1",
    "OT_HOLO_MED2": "HOLO_MED2",
    "OT_HOLO_GEK": "HOLO_TRA",
    "OT_HOLO_KORVAX": "HOLO_EXP",
    "OT_HOLO_VYKEEN": "HOLO_WAR",
    "OT_DECAL_VYKEEN": "BUILDDECALVIS1",
    "OT_DECAL_GEK": "BUILDDECALVIS2",
    "OT_DECAL_KORVAX": "BUILDDECALVIS3",
    **{f"OT_DECAL_NUM{n}": f"BUILDDECALNUM{n}" for n in range(10)},
}
KIT_SOURCES = {**PATH_SOURCES, **SIGN_SOURCES}


def load_spec():
    # A missing spec reads as empty so the checks below fail on content, not on the file.
    return json.loads(SPEC_FILE.read_text(encoding="utf-8")) if SPEC_FILE.is_file() else {}


@pytest.fixture(scope="module")
def spec():
    return load_spec()


@pytest.fixture(scope="module")
def built(spec):
    return {str(k).replace("\\", "/"): ET.fromstring(v) for k, v in gen_parts.build(spec).items()} if spec else {}


@pytest.fixture(scope="module")
def game_files():
    return {l.strip().lower() for l in ALL_FILES.read_text(encoding="utf-8", errors="replace").splitlines()}


def vanilla_object(id_):
    root = ET.parse(EXTRACTED / "metadata/reality/tables/basebuildingobjectstable.MXML").getroot()
    return root.find(f"Property[@name='Objects']/Property[@_id='{id_}']")


def field(entry, dotted):
    node = entry
    for part in dotted.split("."):
        node = node.find(f"Property[@name='{part}']")
    return node.get("value")


def table(built, path):
    assert path in built, f"the module generates no {path}"
    return built[path]


def part_entry(built, id_):
    entry = table(built, OBJ).find(f"Property[@name='Objects']/Property[@_id='{id_}']")
    assert entry is not None, f"{id_} is not in the generated object table"
    return entry


def group_pairs(entry):
    return [
        (g.find("Property[@name='Group']").get("value"), g.find("Property[@name='SubGroupName']").get("value"))
        for g in entry.find("Property[@name='Groups']")
    ]


def products(built):
    return {p.get("_id"): p for p in table(built, PROD).find("Property[@name='Table']")}


def product_of(built, id_):
    product = products(built).get(id_)
    assert product is not None, f"{id_} has no generated product"
    return product


def label(spec, key):
    assert key in spec.get("text", {}), f"no text for {key}"
    return spec["text"][key]


def test_kit_is_the_path_parts_lamp_and_signs_copied_from_their_vanilla_sources(spec):
    assert {p["id"]: p["copy_from"] for p in spec.get("parts", [])} == KIT_SOURCES


def test_every_kit_part_is_only_in_the_settlement_subgroup(spec, built):
    for id_ in KIT_SOURCES:
        assert group_pairs(part_entry(built, id_)) == [SUBGROUP], id_


def test_settlement_subgroup_is_appended_to_the_decoration_group_with_a_label(spec, built):
    assert [(s["group"], s["id"]) for s in spec.get("subgroups", [])] == [SUBGROUP]
    path = "Property[@name='Groups']/Property[@_id='DECORATION']/Property[@name='SubGroups']/Property[@_id='OT_SETTLEMENT']"
    sub = table(built, OBJ).find(path)
    assert sub is not None, "OT_SETTLEMENT is not in the generated DECORATION group"
    assert label(spec, field(sub, "Name")) == "SETTLEMENT"


def test_every_kit_part_shows_in_the_overseer_build_menu(built):
    # The settlement's own build menu lists only parts that can be built outside a base.
    for id_ in KIT_SOURCES:
        assert field(part_entry(built, id_), "BuildableOnPlanet") == "true", id_


def test_decal_path_is_left_vanilla(spec, built):
    # Its scene is an empty marker that settlements draw paths around, so a placed copy renders nothing.
    assert "DECALPATH" not in [e["id"] for e in spec.get("edits", [])]
    assert table(built, OBJ).find("Property[@name='Objects']/Property[@_id='DECALPATH']") is None
    assert "DECALPATH" not in products(built)


def test_lamp_lights_without_power_like_the_vanilla_street_lamp(built):
    # A powered lamp's bulb sits under its connected-state node, so cutting its power use leaves it dark.
    lamp = part_entry(built, "OT_LAMP")
    street = vanilla_object("S_STREETLAMP0")
    for dotted in (
        "PlacementScene.Filename",
        "LinkGridData.Rate",
        "LinkGridData.Connection.NetworkSubGroup",
        "LinkGridData.Connection.NetworkMask",
    ):
        assert field(lamp, dotted) == field(street, dotted), dotted
    assert field(lamp, "LinkGridData.Rate") == "0"


def test_every_new_product_is_craftable(built):
    for id_ in KIT_SOURCES:
        assert field(product_of(built, id_), "IsCraftable") == "true", id_


def test_new_product_icons_exist_in_the_game_files(built, game_files):
    for id_, product in products(built).items():
        icon = field(product, "Icon.Filename")
        assert icon.lower() in game_files, f"{id_}: icon {icon} is not in the game files"


def test_signs_keep_their_vanilla_names_so_every_game_language_has_them(built):
    vanilla = ET.parse(EXTRACTED / "metadata/reality/tables/nms_basepartproducts.MXML").getroot()
    for id_, src in SIGN_SOURCES.items():
        source = vanilla.find(f"Property[@name='Table']/Property[@_id='{src}']")
        for name in ("Name", "NameLower", "Description", "Icon.Filename"):
            assert field(product_of(built, id_), name) == field(source, name), f"{id_}.{name}"


def test_no_kit_sign_draws_power(built):
    # A settlement has no power grid to connect to.
    for id_ in SIGN_SOURCES:
        assert field(part_entry(built, id_), "LinkGridData.Rate") == "0", id_


def test_text_is_plain_player_facing_english(spec):
    assert spec.get("text"), "the spec has no text"
    for key, value in spec.get("text", {}).items():
        assert re.search(r"\b(probe|test)", value, re.I) is None, f"{key}: {value!r}"
        assert value.isascii(), key


def test_names_follow_the_vanilla_casing(spec, built):
    for id_ in PATH_SOURCES:
        product = product_of(built, id_)
        name, lower = label(spec, field(product, "Name")), label(spec, field(product, "NameLower"))
        assert name == name.upper(), f"{id_}: {name!r}"
        assert lower != lower.upper() and lower.upper() == name, f"{id_}: {lower!r}"


def test_text_keys_do_not_collide_with_other_modules(spec):
    mine = set(spec.get("text", {}))
    assert mine, "the spec has no text"
    for other in (REPO / "specs").glob("*.json"):
        if other == SPEC_FILE:
            continue
        shared = mine & set(json.loads(other.read_text(encoding="utf-8")).get("text", {}))
        assert not shared, f"{sorted(shared)} also defined by {other.stem}"
