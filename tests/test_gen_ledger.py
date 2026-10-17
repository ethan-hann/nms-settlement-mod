import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

import gen_ledger
from gen_parts import SpecError

COSTS = """<Data template="cGcCostTable">
  <Property name="InteractionTable">
    <Property name="InteractionTable" value="GcCostTableEntry" _id="C_FLT_TRADE_9" _index="0">
      <Property name="Id" value="C_FLT_TRADE_9" />
      <Property name="DisplayCost" value="true" />
      <Property name="RemoveOptionIfCantAfford" value="false" />
      <Property name="Cost" value="GcCostMoney">
        <Property name="GcCostMoney">
          <Property name="Cost" value="50000" />
          <Property name="CostCurrency" value="GcCurrency">
            <Property name="Currency" value="Units" />
          </Property>
        </Property>
      </Property>
    </Property>
  </Property>
</Data>
"""

ADMIN_OPTION = """<Property name="Options" value="GcAlienPuzzleOption" _index="{i}">
  <Property name="Name" value="{name}" />
  <Property name="Cost" value="C_SETTL_JUDGE" />
  <Property name="Rewards">
    <Property name="Rewards" value="R_OPEN_SETJUDGE" _index="0" />
  </Property>
  <Property name="KeepOpen" value="false" />
  <Property name="DisplayCost" value="false" />
  <Property name="DisablingConditions">
    <Property name="DisablingConditions" value="GcMissionConditionIsPlayerInBase" _index="0" />
  </Property>
</Property>"""

DIALOG = """<Data template="cGcAlienPuzzleTable">
  <Property name="Table">
    <Property name="Table" value="GcAlienPuzzleEntry" _id="SETTLEMENT_ADMIN" _index="0">
      <Property name="Id" value="SETTLEMENT_ADMIN" />
      <Property name="Options">
        {options}
      </Property>
    </Property>
  </Property>
</Data>
"""

RANGE = """<Property name="{list}" value="GcSettlementStatValueRange" _index="{i}">
  <Property name="Type" value="GcSettlementStatType">
    <Property name="SettlementStatType" value="{stat}" />
  </Property>
  <Property name="MinValue" value="{lo}" />
  <Property name="MaxValue" value="{hi}" />
</Property>"""


def building(name, base, upgrade=()):
    ranges = "".join(RANGE.format(list="Base", i=i, stat=s, lo=lo, hi=hi) for i, (s, lo, hi) in enumerate(base))
    ups = "".join(RANGE.format(list="Upgrade1", i=i, stat=s, lo=lo, hi=hi) for i, (s, lo, hi) in enumerate(upgrade))
    return f"""<Property name="{name}" value="GcSettlementBuildingContribution">
  <Property name="Base">{ranges}</Property>
  <Property name="Upgrade1">{ups}</Property>
</Property>"""


def strength(name, lo, hi):
    return f"""<Property name="{name}" value="GcSettlementStatStrengthRanges">
  <Property name="AmountMin" value="{lo}" />
  <Property name="AmountMax" value="{hi}" />
</Property>"""


GLOBALS = """<Data template="cGcSettlementGlobals">
  <Property name="PerkStatStrengthValues">
    <Property name="Debt" value="GcSettlementStatStrengthData">
      <Property name="PerkStatStrengthValues">
        {debt}
      </Property>
    </Property>
  </Property>
  <Property name="SettlementBuildingContributions">
    {buildings}
  </Property>
</Data>
"""

ENGLISH = """<Data template="cTkLocalisationTable">
  <Property name="Table">
    <Property name="Table" value="TkLocalisationEntry" _id="UI_SETTLEMENT_PROD_DEBT_TIP">
      <Property name="Id" value="UI_SETTLEMENT_PROD_DEBT_TIP" />
      <Property name="English" value="Reduce debt by constructing buildings" />
    </Property>
  </Property>
</Data>
"""

FACTORY = [("Production", 20000, 30000), ("MaxPopulation", 1, 1), ("Happiness", -1, -1), ("Upkeep", 40000, 50000)]
FARM = [("Production", 15000, 25000), ("Upkeep", 30000, 40000)]


@pytest.fixture
def vanilla(tmp_path):
    tables = tmp_path / "metadata/reality/tables"
    tables.mkdir(parents=True)
    (tables / "costtable.MXML").write_text(COSTS, encoding="utf-8")
    names = ["UI_SETTLEMENT_JUDGE_OPT", "UI_SETTLEMENT_ADMIN_OPT_ALT", "UI_SETTLEMENT_ADMIN_OPT_ALL", "ALL_REQUEST_LEAVE"]
    options = "".join(ADMIN_OPTION.format(i=i, name=n) for i, n in enumerate(names))
    (tables / "nms_dialog_gcalienpuzzletable.MXML").write_text(DIALOG.format(options=options), encoding="utf-8")
    debt = strength("PositiveLarge", -100000, -50000) + strength("NegativeSmall", 5000, 10000)
    buildings = building("Settlement_Factory", FACTORY, [("Upkeep", 1, 2)]) + building("Settlement_Farm", FARM)
    buildings += building("Settlement_Hab", [("Production", 1000, 1500)])
    (tmp_path / "gcsettlementglobals.MXML").write_text(GLOBALS.format(debt=debt, buildings=buildings), encoding="utf-8")
    (tmp_path / "language").mkdir()
    (tmp_path / "language/nms_loc7_english.MXML").write_text(ENGLISH, encoding="utf-8")
    return tmp_path


def option(id_, key, steps):
    return {"id": id_, "text": key, "debt_steps": steps}


def ledger_spec(*options, step=100000):
    return {
        "debt_step": step,
        "terminal_options": list(options),
        "text": {o["text"]: "Pay" for o in options if o.get("text")},
    }


TWO = (option("PAY1", "OT_FL_PAY_S", 1), option("PAY10", "OT_FL_PAY_L", 10))


def parse(out, name):
    (rel,) = [r for r in out if Path(r).name == name]
    return ET.fromstring(out[rel])


def costs_by_id(out):
    return {e.get("_id"): e for e in parse(out, "COSTTABLE.EXML").find("Property[@name='InteractionTable']")}


def rewards_by_id(out):
    return {e.get("_id"): e for e in parse(out, "REWARDTABLE.EXML").find("Property[@name='SettlementTable']")}


def appended_options(out):
    admin = parse(out, "NMS_DIALOG_GCALIENPUZZLETABLE.EXML").find(
        "Property[@name='Table']/Property[@_id='SETTLEMENT_ADMIN']/Property[@name='Options']"
    )
    return list(admin)


def value(node, name):
    return node.find(f".//Property[@name='{name}']").get("value")


def test_a_spec_without_ledger_keys_writes_nothing(vanilla):
    assert gen_ledger.build({"text": {"OT_X": "x"}}, vanilla) == {}


def test_each_option_costs_two_units_per_debt_it_clears(vanilla):
    out = gen_ledger.build(ledger_spec(*TWO), vanilla)
    costs, rewards = costs_by_id(out), rewards_by_id(out)
    for opt in appended_options(out):
        cost_id = value(opt, "Cost")
        (reward,) = opt.find("Property[@name='Rewards']")
        steps = 0
        for item in rewards[reward.get("value")].iter("Property"):
            if item.get("name") == "StatToAward":
                assert value(item, "SettlementStatType") == "Debt"
                assert value(item, "SettlementStatStrength") == "PositiveLarge"
                steps += 1
        money = costs[cost_id].find("Property[@name='Cost']/Property[@name='GcCostMoney']")
        assert value(money, "Currency") == "Units"
        assert int(money.find("Property[@name='Cost']").get("value")) == 2 * 100000 * steps
    assert sorted(costs) == ["C_OT_FL_PAY1", "C_OT_FL_PAY10"]
    assert sorted(rewards) == ["R_OT_FL_DEBT1", "R_OT_FL_DEBT10"]


def test_a_cost_copies_the_vanilla_entry_under_its_own_id(vanilla):
    cost = costs_by_id(gen_ledger.build(ledger_spec(TWO[0]), vanilla))["C_OT_FL_PAY1"]
    assert value(cost, "Id") == "C_OT_FL_PAY1"
    assert value(cost, "DisplayCost") == "true"
    assert all("_index" not in n.attrib for n in cost.iter())


def test_rewards_change_the_stat_out_loud(vanilla):
    reward = rewards_by_id(gen_ledger.build(ledger_spec(TWO[0]), vanilla))["R_OT_FL_DEBT1"]
    assert value(reward, "Id") == "R_OT_FL_DEBT1"
    assert value(reward, "RewardChoice") == "GiveAll"
    assert value(reward, "Silent") == "false"


def test_options_copy_the_first_admin_option_with_their_own_text_cost_and_reward(vanilla):
    first, second = appended_options(gen_ledger.build(ledger_spec(*TWO), vanilla))
    assert value(first, "Name") == "OT_FL_PAY_S"
    assert value(first, "Cost") == "C_OT_FL_PAY1"
    assert [r.get("value") for r in first.find("Property[@name='Rewards']")] == ["R_OT_FL_DEBT1"]
    assert value(second, "Name") == "OT_FL_PAY_L"
    # The terminal stays open for repeat payments, and Session 6 showed disabling conditions do nothing here.
    assert value(first, "KeepOpen") == "true"
    assert value(first, "DisplayCost") == "true"
    assert len(first.find("Property[@name='DisablingConditions']")) == 0
    # Appended without a key, so they land after the vanilla options.
    assert all("_index" not in n.attrib for n in first.iter())


def test_debt_positive_large_becomes_a_flat_step(vanilla):
    out = gen_ledger.build(ledger_spec(*TWO, step=100000), vanilla)
    large = parse(out, "GCSETTLEMENTGLOBALS.EXML").find(
        "Property[@name='PerkStatStrengthValues']/Property[@name='Debt']"
        "/Property[@name='PerkStatStrengthValues']/Property[@name='PositiveLarge']"
    )
    assert [value(large, "AmountMin"), value(large, "AmountMax")] == ["-100000", "-100000"]


def test_the_terminal_never_gets_more_than_six_options(vanilla):
    three = TWO + (option("PAY5", "OT_FL_PAY_M", 5),)
    with pytest.raises(SpecError, match="six"):
        gen_ledger.build(ledger_spec(*three), vanilla)


@pytest.mark.parametrize(
    "bad, message",
    [
        (option("PAY1_TOO_LONG", "OT_FL_PAY_S", 1), "15"),
        (option("PAY1", "OT_PAY_S", 1), "OT_FL_"),
        (option("PAY1", "OT_FL_PAY_S", 0), "debt_steps"),
    ],
)
def test_option_ids_and_steps_are_checked(vanilla, bad, message):
    with pytest.raises(SpecError, match=message):
        gen_ledger.build(ledger_spec(bad), vanilla)


def test_two_options_may_not_share_an_id(vanilla):
    with pytest.raises(SpecError, match="twice"):
        gen_ledger.build(ledger_spec(option("PAY1", "OT_FL_A", 1), option("PAY1", "OT_FL_B", 2)), vanilla)


def test_an_option_without_text_fails(vanilla):
    spec = ledger_spec(TWO[0])
    spec["text"] = {}
    with pytest.raises(SpecError, match="no text"):
        gen_ledger.build(spec, vanilla)


def test_options_need_a_debt_step(vanilla):
    spec = ledger_spec(TWO[0])
    del spec["debt_step"]
    with pytest.raises(SpecError, match="debt_step"):
        gen_ledger.build(spec, vanilla)


def test_overrides_must_name_vanilla_keys_that_have_text(vanilla):
    spec = ledger_spec(TWO[0])
    spec["text"]["UI_SETTLEMENT_PROD_DEBT_TIP"] = "Tip"
    spec["text_overrides"] = ["UI_SETTLEMENT_PROD_DEBT_TIP"]
    assert gen_ledger.build(spec, vanilla)
    spec["text_overrides"] = ["UI_NO_SUCH_KEY"]
    spec["text"]["UI_NO_SUCH_KEY"] = "x"
    with pytest.raises(SpecError, match="UI_NO_SUCH_KEY"):
        gen_ledger.build(spec, vanilla)
    spec["text_overrides"] = ["UI_SETTLEMENT_PROD_DEBT_TIP"]
    del spec["text"]["UI_NO_SUCH_KEY"]
    del spec["text"]["UI_SETTLEMENT_PROD_DEBT_TIP"]
    with pytest.raises(SpecError, match="UI_SETTLEMENT_PROD_DEBT_TIP"):
        gen_ledger.build(spec, vanilla)


def test_text_keys_are_new_ones_or_declared_overrides(vanilla):
    spec = ledger_spec(TWO[0])
    spec["text"]["UI_SETTLEMENT_PROD_DEBT_TIP"] = "Tip"
    with pytest.raises(SpecError, match="text_overrides"):
        gen_ledger.build(spec, vanilla)


def upkeep_patch(out):
    return parse(out, "GCSETTLEMENTGLOBALS.EXML").find("Property[@name='SettlementBuildingContributions']")


def test_upkeep_matches_production_for_the_listed_buildings_only(vanilla):
    out = gen_ledger.build({"match_upkeep_to_production": ["Settlement_Factory", "Settlement_Farm"]}, vanilla)
    contributions = upkeep_patch(out)
    assert [b.get("name") for b in contributions] == ["Settlement_Factory", "Settlement_Farm"]
    expected = {"Settlement_Factory": ("3", "20000", "30000"), "Settlement_Farm": ("1", "15000", "25000")}
    for b in contributions:
        # Only the Base list is touched, and only its Upkeep item, found by stat type.
        assert [c.get("name") for c in b] == ["Base"]
        (item,) = b.find("Property[@name='Base']")
        assert (item.get("_index"), value(item, "MinValue"), value(item, "MaxValue")) == expected[b.get("name")]
        assert [c.get("name") for c in item] == ["MinValue", "MaxValue"]
    assert parse(out, "GCSETTLEMENTGLOBALS.EXML").find("Property[@name='PerkStatStrengthValues']") is None


def test_a_listed_building_without_upkeep_fails(vanilla):
    with pytest.raises(SpecError, match="Settlement_Hab.*Upkeep"):
        gen_ledger.build({"match_upkeep_to_production": ["Settlement_Hab"]}, vanilla)


def test_an_unknown_building_fails(vanilla):
    with pytest.raises(SpecError, match="Settlement_Nowhere"):
        gen_ledger.build({"match_upkeep_to_production": ["Settlement_Nowhere"]}, vanilla)
