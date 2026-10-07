import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

import gen_parts
from gen_parts import SpecError

OBJECTS = """<Data template="cGcBaseBuildingTable">
  <Property name="Objects">
    <Property name="Objects" value="GcBaseBuildingEntry" _id="S_FLOOR_Q">
      <Property name="ID" value="S_FLOOR_Q" />
      <Property name="PlacementScene" value="TkModelResource">
        <Property name="Filename" value="MODELS/FLOOR.SCENE.MBIN" />
      </Property>
      <Property name="PlanetBaseLimit" value="0" />
      <Property name="EditsTerrain" value="true" />
      <Property name="Groups">
        <Property name="Groups" value="GcBaseBuildingEntryGroup" _index="0">
          <Property name="Group" value="BASIC_S" />
          <Property name="SubGroupName" value="S_FLOORS" />
          <Property name="SubGroup" value="0" />
        </Property>
      </Property>
    </Property>
    <Property name="Objects" value="GcBaseBuildingEntry" _id="DECALPATH">
      <Property name="ID" value="DECALPATH" />
      <Property name="PlanetBaseLimit" value="50" />
      <Property name="Groups" />
    </Property>
  </Property>
  <Property name="Groups">
    <Property name="Groups" value="GcBaseBuildingGroup" _id="MOD">
      <Property name="ID" value="MOD" />
      <Property name="SubGroups">
        <Property name="SubGroups" value="GcBaseBuildingSubGroup" _id="MODGROUP0">
          <Property name="Id" value="MODGROUP0" />
          <Property name="Name" value="SUBGROUP0" />
        </Property>
      </Property>
    </Property>
  </Property>
</Data>
"""

COSTS = """<Data template="cGcBaseBuildingCostsTable">
  <Property name="ObjectCosts">
    <Property name="ObjectCosts" value="GcBaseBuildingEntryCosts" _id="S_FLOOR_Q">
      <Property name="ID" value="S_FLOOR_Q" />
      <Property name="ActiveTotalNodes" value="2" />
    </Property>
  </Property>
</Data>
"""

PRODUCTS = """<Data template="cGcProductTable">
  <Property name="Table">
    <Property name="Table" value="GcProductData" _id="S_FLOOR_Q">
      <Property name="ID" value="S_FLOOR_Q" />
      <Property name="Name" value="BLD_S_FLOOR_Q_NAME" />
      <Property name="NameLower" value="BLD_S_FLOOR_Q_NAME_L" />
      <Property name="Description" value="BLD_BASIC_STONE_DESC" />
      <Property name="Icon" value="TkTextureResource">
        <Property name="Filename" value="TEXTURES/STONE.DDS" />
      </Property>
      <Property name="Requirements">
        <Property name="Requirements" value="GcTechnologyRequirement" _id="SAND1">
          <Property name="ID" value="SAND1" />
          <Property name="Amount" value="5" />
        </Property>
      </Property>
    </Property>
  </Property>
</Data>
"""


@pytest.fixture
def vanilla(tmp_path):
    tables = tmp_path / "metadata/reality/tables"
    tables.mkdir(parents=True)
    (tables / "basebuildingobjectstable.MXML").write_text(OBJECTS)
    (tables / "basebuildingcoststable.MXML").write_text(COSTS)
    (tables / "nms_basepartproducts.MXML").write_text(PRODUCTS)
    return tmp_path


def files(spec, vanilla):
    return {str(k).replace("\\", "/"): ET.fromstring(v) for k, v in gen_parts.build(spec, vanilla).items()}


OBJ = "METADATA/REALITY/TABLES/BASEBUILDINGOBJECTSTABLE.EXML"
COST = "METADATA/REALITY/TABLES/BASEBUILDINGCOSTSTABLE.EXML"
PROD = "METADATA/REALITY/TABLES/NMS_BASEPARTPRODUCTS.EXML"


def get(node, name):
    return node.find(f"Property[@name='{name}']")


def item(root, list_name, id_):
    return root.find(f"Property[@name='{list_name}']/Property[@_id='{id_}']")


NEW_PART = {
    "parts": [
        {
            "id": "OT_PATH_TILE",
            "copy_from": "S_FLOOR_Q",
            "object": {"EditsTerrain": "false", "PlanetBaseLimit": "300"},
            "groups": [["MOD", "OT_SETTLEMENT"]],
            "product": {"Name": "OT_PATH_TILE_NAME", "Icon.Filename": "TEXTURES/PATH.DDS"},
        }
    ]
}


def test_new_part_copies_the_vanilla_entry_under_its_own_id(vanilla):
    out = files(NEW_PART, vanilla)
    entry = item(out[OBJ], "Objects", "OT_PATH_TILE")
    assert get(entry, "ID").get("value") == "OT_PATH_TILE"
    assert get(get(entry, "PlacementScene"), "Filename").get("value") == "MODELS/FLOOR.SCENE.MBIN"
    assert get(entry, "EditsTerrain").get("value") == "false"
    assert get(entry, "PlanetBaseLimit").get("value") == "300"
    assert item(out[OBJ], "Objects", "S_FLOOR_Q") is None


def test_new_part_groups_replace_the_source_groups_and_carry_no_index(vanilla):
    out = files(NEW_PART, vanilla)
    groups = list(get(item(out[OBJ], "Objects", "OT_PATH_TILE"), "Groups"))
    assert [(get(g, "Group").get("value"), get(g, "SubGroupName").get("value")) for g in groups] == [
        ("MOD", "OT_SETTLEMENT")
    ]
    assert all("_index" not in n.attrib for n in out[OBJ].iter())


def test_new_part_gets_cost_and_product_entries(vanilla):
    out = files(NEW_PART, vanilla)
    cost = item(out[COST], "ObjectCosts", "OT_PATH_TILE")
    assert get(cost, "ID").get("value") == "OT_PATH_TILE"
    assert get(cost, "ActiveTotalNodes").get("value") == "2"
    product = item(out[PROD], "Table", "OT_PATH_TILE")
    assert get(product, "ID").get("value") == "OT_PATH_TILE"
    assert get(product, "Name").get("value") == "OT_PATH_TILE_NAME"
    assert get(get(product, "Icon"), "Filename").get("value") == "TEXTURES/PATH.DDS"
    assert get(product, "Requirements").find("Property[@_id='SAND1']") is not None


def test_edit_touches_only_named_fields_and_appends_groups(vanilla):
    spec = {
        "edits": [
            {
                "id": "DECALPATH",
                "object": {"PlanetBaseLimit": "200"},
                "add_groups": [["MOD", "OT_SETTLEMENT"]],
                "new_product": {"copy_from": "S_FLOOR_Q", "fields": {"Name": "OT_DECALPATH_NAME"}},
            }
        ]
    }
    out = files(spec, vanilla)
    entry = item(out[OBJ], "Objects", "DECALPATH")
    assert [c.get("name") for c in entry] == ["PlanetBaseLimit", "Groups"]
    assert get(entry, "PlanetBaseLimit").get("value") == "200"
    added = list(get(entry, "Groups"))
    assert len(added) == 1 and "_id" not in added[0].attrib and "_index" not in added[0].attrib
    product = item(out[PROD], "Table", "DECALPATH")
    assert get(product, "Name").get("value") == "OT_DECALPATH_NAME"
    assert COST not in out


def test_subgroup_is_appended_to_an_existing_group(vanilla):
    out = files({"subgroups": [{"group": "MOD", "id": "OT_SETTLEMENT", "name": "OT_SETTLEMENT_SUB"}]}, vanilla)
    group = item(out[OBJ], "Groups", "MOD")
    assert [c.get("name") for c in group] == ["SubGroups"]
    sub = get(group, "SubGroups").find("Property[@_id='OT_SETTLEMENT']")
    assert get(sub, "Id").get("value") == "OT_SETTLEMENT"
    assert get(sub, "Name").get("value") == "OT_SETTLEMENT_SUB"


def test_text_becomes_a_loc_table_in_english_and_us_english(vanilla):
    out = files({"text": {"OT_PATH_TILE_NAME": "Path Tile"}}, vanilla)
    table = out["LocTable.MXML"]
    assert table.get("template") == "cTkLocalisationTable"
    entry = get(table, "Table").find("Property[@_id='OT_PATH_TILE_NAME']")
    assert get(entry, "Id").get("value") == "OT_PATH_TILE_NAME"
    assert get(entry, "English").get("value") == "Path Tile"
    assert get(entry, "USEnglish").get("value") == "Path Tile"


def test_unknown_source_part_is_an_error(vanilla):
    with pytest.raises(SpecError, match="NOPE"):
        gen_parts.build({"parts": [{"id": "OT_X", "copy_from": "NOPE"}]}, vanilla)


def test_unknown_override_field_is_an_error(vanilla):
    with pytest.raises(SpecError, match="Bogus"):
        gen_parts.build({"parts": [{"id": "OT_X", "copy_from": "S_FLOOR_Q", "object": {"Bogus": "1"}}]}, vanilla)


def test_ids_longer_than_sixteen_characters_are_rejected(vanilla):
    with pytest.raises(SpecError, match="16"):
        gen_parts.build({"parts": [{"id": "OT_THIS_IS_TOO_LONG", "copy_from": "S_FLOOR_Q"}]}, vanilla)


def test_duplicate_ids_are_rejected(vanilla):
    part = {"id": "OT_X", "copy_from": "S_FLOOR_Q"}
    with pytest.raises(SpecError, match="OT_X"):
        gen_parts.build({"parts": [part, dict(part)]}, vanilla)
