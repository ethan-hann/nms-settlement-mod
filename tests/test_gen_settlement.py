import copy
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

import gen_settlement
from gen_parts import SpecError

STAT_CHANGE = """<Property name="StatChanges" value="GcSettlementStatChange" _index="{i}">
  <Property name="Stat" value="GcSettlementStatType">
    <Property name="SettlementStatType" value="{stat}" />
  </Property>
  <Property name="Strength" value="GcSettlementStatStrength">
    <Property name="SettlementStatStrength" value="{strength}" />
  </Property>
  <Property name="DirectlyChangePopulation" value="false" />
</Property>"""

PERKS = f"""<Data template="cGcSettlementPerksTable">
  <Property name="Table">
    <Property name="Table" value="GcSettlementPerkData" _id="SENT_QUAR" _index="0">
      <Property name="ID" value="SENT_QUAR" />
      <Property name="Name" value="UI_SENT_MISS_PERK2" />
      <Property name="Description" value="UI_SENT_MISS_PERK2_DESC" />
      <Property name="IsNegative" value="false" />
      <Property name="IsStarter" value="false" />
      <Property name="IsProc" value="false" />
      <Property name="IsJob" value="false" />
      <Property name="IsBlessing" value="true" />
      <Property name="StatChanges">
        {STAT_CHANGE.format(i=0, stat="Debt", strength="PositiveSmall")}
      </Property>
      <Property name="AssociatedBuildings" />
    </Property>
    <Property name="Table" value="GcSettlementPerkData" _id="STARTING_POS1" _index="1">
      <Property name="ID" value="STARTING_POS1" />
      <Property name="IsStarter" value="true" />
    </Property>
  </Property>
</Data>
"""

OPTION = """<Property name="Option{n}List">
  <Property name="Option{n}List" value="GcSettlementJudgementOption" _index="0">
    <Property name="OptionText" value="SOURCE_OPT_{n}" />
    <Property name="AltOptionText" />
    <Property name="Perks">
      <Property name="Perks" value="GcSettlementJudgementPerkOption" _index="0">
        <Property name="Perk" value="STARTING_POS1" />
        <Property name="PerkChance" value="1.000000" />
      </Property>
    </Property>
    <Property name="HidePerkInJudgement" value="false" />
    <Property name="StatChanges">
      {changes}
    </Property>
    <Property name="AdditionalRewards">
      <Property name="AdditionalRewards" value="R_SOURCE" _index="0" />
    </Property>
    <Property name="ChainedJudgementID" value="{chain}" />
    <Property name="UsePolicyPerk" value="false" />
    <Property name="UsePolicyStat" value="false" />
    <Property name="UseGiftReward" value="false" />
    <Property name="UseTechPerk" value="false" />
    <Property name="JudgementOptionStanding" value="None" />
    <Property name="OptionIsPositiveForNPC" value="{positive}" />
  </Property>
</Property>"""


def judgement(index, type_, weight, chain="", policy_perk="false"):
    option1 = OPTION.format(
        n=1, changes=STAT_CHANGE.format(i=0, stat="Happiness", strength="PositiveLarge"), chain=chain, positive="true"
    ).replace('"UsePolicyPerk" value="false"', f'"UsePolicyPerk" value="{policy_perk}"')
    option2 = OPTION.format(n=2, changes="", chain="", positive="false")
    return f"""<Property name="Judgements" value="GcSettlementJudgementData" _index="{index}">
  <Property name="JudgementType" value="GcSettlementJudgementType">
    <Property name="SettlementJudgementType" value="{type_}" />
  </Property>
  <Property name="Weighting" value="{weight}" />
  <Property name="HeaderOverride" value="" />
  <Property name="Title" value="SOURCE_TITLE" />
  <Property name="NPCTitle" value="UI_DILEMMA_BOT_TITLE" />
  <Property name="QuestionText" value="SOURCE_QUESTION" />
  <Property name="DilemmaText" value="SOURCE_DILEMMA" />
  <Property name="DilemmaTextIsAlien" value="false" />
  {option1}
  {option2}
  <Property name="Option3List" />
  <Property name="Option4List" />
  <Property name="NPC1CustomId" value="NPC_JUDGEMENT" />
  <Property name="NPCs" value="One" />
</Property>"""


def strength_table(stat, extra=()):
    ranges = "".join(
        f'<Property name="{name}" value="GcSettlementStatStrengthRanges">'
        f'<Property name="AmountMin" value="{lo}" /><Property name="AmountMax" value="{hi}" /></Property>'
        for name, lo, hi in (
            ("PositiveSmall", -300, -100),
            ("PositiveMedium", -500, -300),
            ("NegativeSmall", 10, 50),
            ("NegativeMedium", 100, 200),
            *extra,
        )
    )
    return (
        f'<Property name="{stat}" value="GcSettlementStatStrengthData">'
        f'<Property name="PerkStatStrengthValues">{ranges}</Property></Property>'
    )


GLOBALS = f"""<Data template="cGcSettlementGlobals">
  <Property name="JudgementSelectionWeights">
    <Property name="None" value="0.000000" />
    <Property name="Policy" value="0.250000" />
    <Property name="Request" value="0.330000" />
  </Property>
  <Property name="Judgements">
    {judgement(0, "Policy", "1.000000")}
    {judgement(1, "Request", "1.000000")}
    {judgement(2, "Request", "0.500000", chain="J_CHAINED")}
    {judgement(3, "Request", "0.500000", policy_perk="true")}
  </Property>
  <Property name="StatsMaxValues">
    <Property name="Happiness" value="180" />
    <Property name="Debt" value="10000000" />
    <Property name="Alert" value="1000" />
    <Property name="Sentinels" value="100" />
  </Property>
  <Property name="PerkStatStrengthValues">
    {strength_table("Happiness")}
    {strength_table("Debt")}
    {strength_table("Alert")}
    {strength_table("Sentinels", extra=[("NegativeLarge", 5, 10)])}
  </Property>
</Data>
"""


@pytest.fixture
def vanilla(tmp_path):
    (tmp_path / "metadata/reality/tables").mkdir(parents=True)
    (tmp_path / "metadata/reality/tables/settlementperkstable.MXML").write_text(PERKS)
    (tmp_path / "gcsettlementglobals.MXML").write_text(GLOBALS)
    return tmp_path


PERK_FILE = "METADATA/REALITY/TABLES/SETTLEMENTPERKSTABLE.EXML"
GLOBALS_FILE = "GCSETTLEMENTGLOBALS.EXML"


class Out(dict):
    def __missing__(self, key):
        pytest.fail(f"{key} was not generated")


def files(spec, vanilla):
    return Out((str(k).replace("\\", "/"), ET.fromstring(v)) for k, v in gen_settlement.build(spec, vanilla).items())


def shape(node):
    return (node.tag, dict(node.attrib), [shape(c) for c in node])


def get(node, name):
    return node.find(f"Property[@name='{name}']")


def value(node, name):
    return get(node, name).get("value")


def changes(node):
    return [
        (value(c.find("Property[@name='Stat']"), "SettlementStatType"), value(c.find("Property[@name='Strength']"), "SettlementStatStrength"))
        for c in get(node, "StatChanges")
    ]


NEW_PERK = {
    "perks": [
        {
            "id": "OT_WATCH",
            "copy_from": "SENT_QUAR",
            "name": "OT_WATCH_NAME",
            "description": "OT_WATCH_DESC",
            "stat_changes": [["Alert", "PositiveMedium"], ["Sentinels", "NegativeSmall"]],
        }
    ]
}

NEW_JUDGEMENT = {
    "perks": NEW_PERK["perks"],
    "judgements": [
        {
            "name": "OT_J_FORTIFY",
            "copy_from": 1,
            "type": "Request",
            "weighting": 1.0,
            "title": "OT_FORT_TITLE",
            "question": "OT_FORT_QUESTION",
            "dilemma": "OT_FORT_DILEMMA",
            "options": [
                {"text": "OT_FORT_OPT1", "perks": [["OT_WATCH", 1.0]], "stat_changes": [["Debt", "NegativeMedium"]]},
                {"text": "OT_FORT_OPT2", "stat_changes": [["Happiness", "PositiveSmall"]]},
            ],
        }
    ],
}


def new_judgement(out):
    return out[GLOBALS_FILE].find("Property[@name='Judgements']/Property")


def test_perk_copies_the_source_under_its_own_id(vanilla):
    out = files(NEW_PERK, vanilla)
    entry = out[PERK_FILE].find("Property[@name='Table']/Property[@_id='OT_WATCH']")
    assert value(entry, "ID") == "OT_WATCH"
    assert value(entry, "Name") == "OT_WATCH_NAME"
    assert value(entry, "Description") == "OT_WATCH_DESC"
    assert value(entry, "IsBlessing") == "true"
    assert out[PERK_FILE].find("Property[@name='Table']/Property[@_id='SENT_QUAR']") is None
    assert out[PERK_FILE].get("template") == "cGcSettlementPerksTable"


def test_perk_stat_changes_replace_the_source_changes_in_order(vanilla):
    entry = files(NEW_PERK, vanilla)[PERK_FILE].find("Property[@name='Table']/Property[@_id='OT_WATCH']")
    assert changes(entry) == [("Alert", "PositiveMedium"), ("Sentinels", "NegativeSmall")]


def test_generated_stat_changes_have_the_vanilla_shape_without_indexes(vanilla):
    entry = files(NEW_PERK, vanilla)[PERK_FILE].find("Property[@name='Table']/Property[@_id='OT_WATCH']")
    made = get(entry, "StatChanges")[0]
    source = ET.fromstring(STAT_CHANGE.format(i=0, stat="Alert", strength="PositiveMedium"))
    source.attrib.pop("_index")
    assert shape(made) == shape(source)


def test_no_generated_node_carries_an_index(vanilla):
    out = files(NEW_JUDGEMENT, vanilla)
    assert not [n for root in out.values() for n in root.iter() if "_index" in n.attrib]


def test_a_spec_without_perks_or_judgements_makes_no_files(vanilla):
    assert gen_settlement.build({}, vanilla) == {}
    assert gen_settlement.build({"text": {"OT_X": "x"}}, vanilla) == {}


def test_judgement_is_appended_without_a_key(vanilla):
    out = files(NEW_JUDGEMENT, vanilla)
    root = out[GLOBALS_FILE]
    assert root.get("template") == "cGcSettlementGlobals"
    assert [c.get("name") for c in root] == ["Judgements"]
    entry = new_judgement(out)
    assert entry.get("value") == "GcSettlementJudgementData"
    assert "_id" not in entry.attrib and "_index" not in entry.attrib
    assert len(root.find("Property[@name='Judgements']")) == 1


def test_judgement_sets_type_weighting_and_text_and_copies_the_rest(vanilla):
    entry = new_judgement(files(NEW_JUDGEMENT, vanilla))
    assert value(get(entry, "JudgementType"), "SettlementJudgementType") == "Request"
    assert value(entry, "Weighting") == "1.000000"
    assert value(entry, "Title") == "OT_FORT_TITLE"
    assert value(entry, "QuestionText") == "OT_FORT_QUESTION"
    assert value(entry, "DilemmaText") == "OT_FORT_DILEMMA"
    assert value(entry, "NPCTitle") == "UI_DILEMMA_BOT_TITLE"
    assert value(entry, "NPC1CustomId") == "NPC_JUDGEMENT"
    assert value(entry, "NPCs") == "One"


def test_judgement_type_can_differ_from_the_source(vanilla):
    spec = copy.deepcopy(NEW_JUDGEMENT)
    spec["judgements"][0]["type"] = "Policy"
    entry = new_judgement(files(spec, vanilla))
    assert value(get(entry, "JudgementType"), "SettlementJudgementType") == "Policy"


def test_option_perks_use_the_vanilla_perk_option_struct(vanilla):
    entry = new_judgement(files(NEW_JUDGEMENT, vanilla))
    option = get(entry, "Option1List")[0]
    perks = get(option, "Perks")
    assert len(perks) == 1
    assert perks[0].get("value") == "GcSettlementJudgementPerkOption"
    assert [(c.get("name"), c.get("value")) for c in perks[0]] == [("Perk", "OT_WATCH"), ("PerkChance", "1.000000")]


def test_option_text_perks_and_changes_come_from_the_spec(vanilla):
    entry = new_judgement(files(NEW_JUDGEMENT, vanilla))
    one, two = get(entry, "Option1List")[0], get(entry, "Option2List")[0]
    assert (value(one, "OptionText"), changes(one)) == ("OT_FORT_OPT1", [("Debt", "NegativeMedium")])
    assert (value(two, "OptionText"), changes(two)) == ("OT_FORT_OPT2", [("Happiness", "PositiveSmall")])
    assert len(get(two, "Perks")) == 0


def test_options_never_inherit_rewards_or_perks_from_the_source(vanilla):
    entry = new_judgement(files(NEW_JUDGEMENT, vanilla))
    for n in (1, 2):
        option = get(entry, f"Option{n}List")[0]
        assert len(get(option, "AdditionalRewards")) == 0
    assert "R_SOURCE" not in ET.tostring(entry, encoding="unicode")
    assert "STARTING_POS1" not in ET.tostring(entry, encoding="unicode")


def test_option_flags_are_copied_from_the_source(vanilla):
    entry = new_judgement(files(NEW_JUDGEMENT, vanilla))
    assert value(get(entry, "Option1List")[0], "OptionIsPositiveForNPC") == "true"
    assert value(get(entry, "Option2List")[0], "OptionIsPositiveForNPC") == "false"


def build(spec, vanilla):
    return gen_settlement.build(spec, vanilla)


def with_perk(**changes_):
    spec = copy.deepcopy(NEW_PERK)
    spec["perks"][0].update(changes_)
    return spec


def with_judgement(**changes_):
    spec = copy.deepcopy(NEW_JUDGEMENT)
    spec["judgements"][0].update(changes_)
    return spec


def test_unknown_source_perk_is_an_error(vanilla):
    with pytest.raises(SpecError, match="NO_SUCH_PERK"):
        build(with_perk(copy_from="NO_SUCH_PERK"), vanilla)


def test_unknown_source_judgement_is_an_error(vanilla):
    with pytest.raises(SpecError, match="99"):
        build(with_judgement(copy_from=99), vanilla)


def test_unknown_stat_is_an_error(vanilla):
    with pytest.raises(SpecError, match="Bogus"):
        build(with_perk(stat_changes=[["Bogus", "PositiveSmall"]]), vanilla)


def test_unknown_strength_is_an_error(vanilla):
    with pytest.raises(SpecError, match="PositiveHuge"):
        build(with_perk(stat_changes=[["Alert", "PositiveHuge"]]), vanilla)


def test_a_strength_the_stat_has_no_range_for_is_an_error(vanilla):
    # NegativeLarge exists for Sentinels in the fixture but not for Alert, so the game would have no amount to apply.
    build(with_perk(stat_changes=[["Sentinels", "NegativeLarge"]]), vanilla)
    with pytest.raises(SpecError, match="NegativeLarge"):
        build(with_perk(stat_changes=[["Alert", "NegativeLarge"]]), vanilla)


def test_unknown_judgement_type_is_an_error(vanilla):
    with pytest.raises(SpecError, match="Bogus"):
        build(with_judgement(type="Bogus"), vanilla)


def test_perk_ids_longer_than_sixteen_characters_are_rejected(vanilla):
    with pytest.raises(SpecError, match="16"):
        build(with_perk(id="OT_THIS_IS_TOO_LONG"), vanilla)


def test_a_perk_id_that_exists_in_vanilla_is_rejected(vanilla):
    with pytest.raises(SpecError, match="STARTING_POS1"):
        build(with_perk(id="STARTING_POS1"), vanilla)


def test_duplicate_perk_ids_are_rejected(vanilla):
    spec = copy.deepcopy(NEW_PERK)
    spec["perks"].append(dict(spec["perks"][0]))
    with pytest.raises(SpecError, match="OT_WATCH"):
        build(spec, vanilla)


def test_an_option_cannot_grant_a_perk_that_does_not_exist(vanilla):
    spec = with_judgement()
    spec["judgements"][0]["options"][0]["perks"] = [["OT_MISSING", 1.0]]
    with pytest.raises(SpecError, match="OT_MISSING"):
        build(spec, vanilla)


def test_an_option_can_grant_a_vanilla_perk(vanilla):
    spec = with_judgement()
    spec["judgements"][0]["options"][0]["perks"] = [["STARTING_POS1", 0.5]]
    option = get(new_judgement(files(spec, vanilla)), "Option1List")[0]
    assert get(option, "Perks")[0].find("Property[@name='PerkChance']").get("value") == "0.500000"


def test_more_options_than_the_source_are_rejected(vanilla):
    spec = with_judgement()
    spec["judgements"][0]["options"].append({"text": "OT_FORT_OPT3"})
    with pytest.raises(SpecError, match=r"3 options.*source has 2"):
        build(spec, vanilla)


def test_fewer_options_than_the_source_are_rejected(vanilla):
    spec = with_judgement()
    del spec["judgements"][0]["options"][1]
    with pytest.raises(SpecError, match=r"1 options.*source has 2"):
        build(spec, vanilla)


def test_a_source_that_chains_to_another_judgement_is_rejected(vanilla):
    with pytest.raises(SpecError, match="J_CHAINED"):
        build(with_judgement(copy_from=2), vanilla)


def test_a_source_that_picks_its_own_perk_is_rejected(vanilla):
    with pytest.raises(SpecError, match="UsePolicyPerk"):
        build(with_judgement(copy_from=3), vanilla)


def test_loc_keys_over_the_vanilla_maximum_are_rejected(vanilla):
    with pytest.raises(SpecError, match="OT_" + "X" * 40):
        build(with_perk(name="OT_" + "X" * 40), vanilla)


def test_a_non_positive_weighting_is_rejected(vanilla):
    with pytest.raises(SpecError, match="weighting"):
        build(with_judgement(weighting=0), vanilla)


def test_write_puts_each_file_under_the_module_folder(vanilla, tmp_path):
    module = tmp_path / "module"
    written = gen_settlement.write(NEW_JUDGEMENT, module, vanilla)
    assert sorted(p.relative_to(module).as_posix() for p in written) == [GLOBALS_FILE, PERK_FILE]
    assert (module / PERK_FILE).read_text(encoding="utf-8").startswith('<?xml version="1.0" encoding="utf-8"?>\n')
