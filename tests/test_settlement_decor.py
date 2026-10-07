"""SettlementDecor: every vanilla decoration part can be built in a settlement."""

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

import gen_parts
import merge_preview
import testmode

REPO = Path(__file__).resolve().parent.parent
NAME = "OverseersToolkit-SettlementDecor"
SPEC_FILE = REPO / "specs" / f"{NAME}.json"
MODULE = REPO / "mod" / NAME
OBJ = "METADATA/REALITY/TABLES/BASEBUILDINGOBJECTSTABLE.EXML"
VANILLA = merge_preview.EXTRACTED / "metadata/reality/tables/basebuildingobjectstable.MXML"
DECOR_GROUPS = {"DECORATION", "EXOTICS", "WALL_ART"}

pytestmark = pytest.mark.skipif(not VANILLA.is_file(), reason="run tools/extract.py first")


def load_spec():
    return json.loads(SPEC_FILE.read_text(encoding="utf-8")) if SPEC_FILE.is_file() else {}


@pytest.fixture(scope="module")
def vanilla():
    root = ET.parse(VANILLA).getroot()
    return {e.get("_id"): e for e in root.find("Property[@name='Objects']")}


@pytest.fixture(scope="module")
def edited():
    patch = MODULE / OBJ
    assert patch.is_file(), f"{NAME} has no {OBJ}"
    root = ET.parse(patch).getroot()
    return {e.get("_id"): e for e in root.find("Property[@name='Objects']")}


def groups_of(entry):
    return {g.find("Property[@name='Group']").get("value") for g in entry.find("Property[@name='Groups']")}


def value(entry, dotted):
    node = entry
    for part in dotted.split("."):
        node = node.find(f"Property[@name='{part}']")
    return node.get("value")


def test_the_spec_opens_the_decoration_groups_and_nothing_else():
    assert load_spec().get("group_edits") == [
        {"groups": sorted(DECOR_GROUPS), "object": {"BuildableOnPlanet": "true"}, "unpowered_only": True}
    ]
    assert set(load_spec()) == {"group_edits"}


def test_the_module_ships_only_the_generated_object_table():
    files = sorted(str(p.relative_to(MODULE)).replace("\\", "/") for p in MODULE.rglob("*") if p.is_file())
    assert files == [OBJ]
    on_disk = (MODULE / OBJ).read_text(encoding="utf-8")
    assert on_disk == gen_parts.build(load_spec())[Path(OBJ)], "stale; rerun tools/gen_parts.py"


def test_every_edit_only_lets_a_decoration_part_be_built_outside_a_base(edited, vanilla):
    assert len(edited) > 400
    for id_, entry in edited.items():
        assert [(c.get("name"), c.get("value")) for c in entry] == [("BuildableOnPlanet", "true")], id_
        assert groups_of(vanilla[id_]) & DECOR_GROUPS, f"{id_} is not a decoration part"


def test_walls_floors_rooms_and_tech_stay_base_only(edited):
    for id_ in ("S_FLOOR_Q", "S_WALL_Q_H", "S_TRIFLOOR_Q"):
        assert id_ not in edited


def test_signs_numbers_plants_and_posters_are_opened(edited, vanilla):
    for id_ in ("S_SIGN_BAR0", "BUILDDECALNUM1", "S_STREETLAMP0"):
        assert id_ in edited, id_
    for group in ("EXOTICS", "WALL_ART"):
        assert any(group in groups_of(vanilla[i]) for i in edited), f"nothing from {group}"


def test_lights_that_need_power_are_left_out(edited, vanilla):
    # A settlement has no power grid, so these would sit dark.
    assert "CEILINGLIGHT" not in edited and "BUILDLIGHT2" not in edited
    for id_ in edited:
        assert value(vanilla[id_], "LinkGridData.Rate") == "0", id_


def test_test_mode_can_enable_the_module():
    assert testmode.MODULES.get("decor") == NAME
