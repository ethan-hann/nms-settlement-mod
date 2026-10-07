import xml.etree.ElementTree as ET

import pytest

import gen_unlocks
from gen_unlocks import SpecError

# A trimmed copy of vanilla STORAGE_FIX: auto-starts, skips if the first recipe is known,
# waits a moment, then grants every recipe silently with one visible reward message.
TEMPLATE = """<Data template="cGcMissionTable">
  <Property name="Missions">
    <Property name="Missions" value="GcGenericMissionSequence" _id="STORAGE_FIX">
      <Property name="MissionID" value="STORAGE_FIX" />
      <Property name="AutoStart" value="AllModes" />
      <Property name="Rewards">
        <Property name="Rewards" value="GcGenericRewardTableEntry" _id="SPACE_STORE_BP">
          <Property name="Id" value="SPACE_STORE_BP" />
          <Property name="List" value="GcRewardTableItemList">
            <Property name="RewardChoice" value="GiveAll" />
            <Property name="List">
              <Property name="List" value="GcRewardTableItem" _index="0">
                <Property name="PercentageChance" value="100.000000" />
                <Property name="Reward" value="GcRewardSpecificProductRecipe">
                  <Property name="GcRewardSpecificProductRecipe">
                    <Property name="ID" value="FRE_ROOM_STORE0" />
                    <Property name="Silent" value="true" />
                  </Property>
                </Property>
              </Property>
              <Property name="List" value="GcRewardTableItem" _index="1">
                <Property name="PercentageChance" value="100.000000" />
                <Property name="Reward" value="GcRewardSpecificProductRecipe">
                  <Property name="GcRewardSpecificProductRecipe">
                    <Property name="ID" value="FRE_ROOM_STORE1" />
                    <Property name="Silent" value="true" />
                  </Property>
                </Property>
              </Property>
            </Property>
          </Property>
        </Property>
      </Property>
      <Property name="StartConditionTest" value="GcMissionConditionTest">
        <Property name="ConditionTest" value="AnyFalse" />
      </Property>
      <Property name="StartingConditions" />
      <Property name="Stages">
        <Property name="Stages" value="GcGenericMissionStage" _index="0">
          <Property name="Stage" value="GcMissionSequenceGroup">
            <Property name="GcMissionSequenceGroup">
              <Property name="Silent" value="true" />
              <Property name="DebugText" value="only do this if you don't know it" />
              <Property name="Conditions">
                <Property name="Conditions" value="GcMissionConditionProductKnown" _index="0">
                  <Property name="GcMissionConditionProductKnown">
                    <Property name="Product" value="FRE_ROOM_STORE0" />
                  </Property>
                </Property>
              </Property>
              <Property name="Stages">
                <Property name="Stages" value="GcGenericMissionStage" _index="0">
                  <Property name="Stage" value="GcMissionSequenceWait">
                    <Property name="GcMissionSequenceWait">
                      <Property name="Time" value="1.000000" />
                      <Property name="DebugText" value="small wait" />
                    </Property>
                  </Property>
                </Property>
                <Property name="Stages" value="GcGenericMissionStage" _index="1">
                  <Property name="Stage" value="GcMissionSequenceReward">
                    <Property name="GcMissionSequenceReward">
                      <Property name="Reward" value="SPACE_STORE_BP" />
                      <Property name="Silent" value="false" />
                      <Property name="DebugText" value="give all the storage BPs" />
                    </Property>
                  </Property>
                </Property>
              </Property>
            </Property>
          </Property>
        </Property>
      </Property>
    </Property>
  </Property>
</Data>
"""

PRODUCTS = """<Data template="cGcProductTable">
  <Property name="Table">
    <Property name="Table" value="GcProductData" _id="BUILDPAVING"><Property name="ID" value="BUILDPAVING" /></Property>
  </Property>
</Data>
"""

DIFFICULTY = """<Data template="cGcDifficultyConfig">
  <Property name="StartWithAllItemsKnownEnabledData" value="GcDifficultyStartWithAllItemsKnownOptionData">
    <Property name="InitialKnownThings" value="GcKnownThingsPreset">
      <Property name="KnownProducts">
        <Property name="KnownProducts" value="BUILDPAVING" _index="0" />
      </Property>
    </Property>
  </Property>
</Data>
"""

MISSIONS = "METADATA/SIMULATION/MISSIONS/TABLES/NPCMISSIONTABLE.EXML"
DIFF = "METADATA/GAMESTATE/DIFFICULTYCONFIG.EXML"


@pytest.fixture
def vanilla(tmp_path):
    tables = tmp_path / "metadata/simulation/missions/tables"
    tables.mkdir(parents=True)
    (tables / "fleetmissiontable.MXML").write_text(TEMPLATE)
    reality = tmp_path / "metadata/reality/tables"
    reality.mkdir(parents=True)
    (reality / "nms_basepartproducts.MXML").write_text(PRODUCTS)
    (reality / "nms_reality_gcproducttable.MXML").write_text(PRODUCTS.replace("BUILDPAVING", "CASING"))
    gamestate = tmp_path / "metadata/gamestate"
    gamestate.mkdir(parents=True)
    (gamestate / "difficultyconfig.MXML").write_text(DIFFICULTY)
    return tmp_path


SPEC = {
    "parts": [{"id": "OT_PATH_TILE", "copy_from": "S_FLOOR_Q"}],
    "unlocks": [
        {"id": "OT_UNLOCK_B", "min_class": "B", "reward": "R_OT_UNLOCK_B", "recipes": ["OT_PATH_TILE", "BUILDPAVING"]}
    ],
}


def build(spec, vanilla):
    return {str(k).replace("\\", "/"): ET.fromstring(v) for k, v in gen_unlocks.build(spec, vanilla).items()}


def mission(out, id_):
    return out[MISSIONS].find(f"Property[@name='Missions']/Property[@_id='{id_}']")


def val(node, dotted):
    for part in dotted.split("."):
        node = node.find(f"Property[@name='{part}']")
    return node.get("value")


def test_each_unlock_becomes_a_mission_keyed_by_its_id(vanilla):
    m = mission(build(SPEC, vanilla), "OT_UNLOCK_B")
    assert m is not None
    assert val(m, "MissionID") == "OT_UNLOCK_B"
    assert val(m, "AutoStart") == "AllModes"


def test_the_mission_starts_once_any_settlement_building_reaches_the_class(vanilla):
    m = mission(build(SPEC, vanilla), "OT_UNLOCK_B")
    (cond,) = list(m.find("Property[@name='StartingConditions']"))
    assert cond.get("value") == "GcMissionConditionHasSettlementBuilding"
    inner = cond.find("Property[@name='GcMissionConditionHasSettlementBuilding']")
    assert val(inner, "MinimumClass.InventoryClass") == "B"
    assert val(inner, "AnyBuildingClass") == "true"
    assert val(inner, "RequireComplete") == "true"
    assert val(inner, "CheckAllSettlements") == "true"
    assert val(m, "StartConditionTest.ConditionTest") == "AnyFalse"


def test_the_reward_teaches_every_recipe_silently_under_one_message(vanilla):
    m = mission(build(SPEC, vanilla), "OT_UNLOCK_B")
    reward = m.find("Property[@name='Rewards']/Property[@_id='R_OT_UNLOCK_B']")
    assert val(reward, "Id") == "R_OT_UNLOCK_B"
    recipes = [r for r in reward.iter() if r.get("name") == "GcRewardSpecificProductRecipe"]
    assert [val(r, "ID") for r in recipes] == ["OT_PATH_TILE", "BUILDPAVING"]
    assert {val(r, "Silent") for r in recipes} == {"true"}
    stage = m.find(".//Property[@name='GcMissionSequenceReward']")
    assert val(stage, "Reward") == "R_OT_UNLOCK_B"
    assert val(stage, "Silent") == "false"


def test_the_mission_skips_players_who_already_know_the_first_recipe(vanilla):
    m = mission(build(SPEC, vanilla), "OT_UNLOCK_B")
    known = m.find(".//Property[@name='GcMissionConditionProductKnown']")
    assert val(known, "Product") == "OT_PATH_TILE"


def test_the_copy_carries_no_index_attributes(vanilla):
    out = build(SPEC, vanilla)
    assert all("_index" not in n.attrib for n in out[MISSIONS].iter())


def test_creative_known_products_are_appended_for_new_creative_games(vanilla):
    out = build({**SPEC, "creative_known": ["OT_PATH_TILE"]}, vanilla)
    known = out[DIFF].find(
        "Property[@name='StartWithAllItemsKnownEnabledData']/Property[@name='InitialKnownThings']"
        "/Property[@name='KnownProducts']"
    )
    assert [k.get("value") for k in known] == ["OT_PATH_TILE"]
    assert all("_index" not in k.attrib for k in known)


def test_no_unlocks_means_no_files(vanilla):
    assert gen_unlocks.build({"parts": []}, vanilla) == {}


@pytest.mark.parametrize("klass", ["C", "X", ""])
def test_only_b_a_and_s_classes_are_accepted(vanilla, klass):
    bad = {"unlocks": [{**SPEC["unlocks"][0], "min_class": klass}], "parts": SPEC["parts"]}
    with pytest.raises(SpecError, match="class"):
        gen_unlocks.build(bad, vanilla)


def test_ids_longer_than_fifteen_characters_are_rejected(vanilla):
    bad = {"unlocks": [{**SPEC["unlocks"][0], "id": "OT_UNLOCK_TOOLONG"}], "parts": SPEC["parts"]}
    with pytest.raises(SpecError, match="15"):
        gen_unlocks.build(bad, vanilla)


def test_unknown_recipes_are_rejected(vanilla):
    bad = {"unlocks": [{**SPEC["unlocks"][0], "recipes": ["NOT_A_PRODUCT"]}], "parts": SPEC["parts"]}
    with pytest.raises(SpecError, match="NOT_A_PRODUCT"):
        gen_unlocks.build(bad, vanilla)


def test_products_added_by_an_edit_count_as_known_recipes(vanilla):
    spec = {
        "edits": [{"id": "DECALPATH", "new_product": {"copy_from": "BUILDPAVING"}}],
        "unlocks": [{**SPEC["unlocks"][0], "recipes": ["DECALPATH"]}],
    }
    assert MISSIONS in {str(k).replace("\\", "/") for k in gen_unlocks.build(spec, vanilla)}


def test_creative_known_rejects_unknown_products(vanilla):
    with pytest.raises(SpecError, match="NOPE"):
        gen_unlocks.build({**SPEC, "creative_known": ["NOPE"]}, vanilla)
