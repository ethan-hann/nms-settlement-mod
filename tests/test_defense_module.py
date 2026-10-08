"""What the Defense and TestTuning modules must do, read in vanilla's own sign conventions."""

import functools
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

import gen_parts
import gen_settlement
import merge_preview

REPO = Path(__file__).resolve().parent.parent
SPECS = REPO / "specs"
MODS = REPO / "mod"
EXTRACTED = merge_preview.EXTRACTED
ALL_FILES = REPO / "scratch" / "all_files.txt"

DEFENSE = "OverseersToolkit-Defense"
TUNING = "OverseersToolkit-TestTuning"
WATCH = "OT_WATCH"
TOWER = "OT_TOWER"
PERKS = "METADATA/REALITY/TABLES/SETTLEMENTPERKSTABLE.EXML"
GLOBALS = "GLOBALS/GCSETTLEMENTGLOBALS.EXML"
OBJECTS = "METADATA/REALITY/TABLES/BASEBUILDINGOBJECTSTABLE.EXML"
PRODUCTS = "METADATA/REALITY/TABLES/NMS_BASEPARTPRODUCTS.EXML"

pytestmark = pytest.mark.skipif(
    not (EXTRACTED / "gcsettlementglobals.MXML").is_file()
    or not (EXTRACTED / "metadata/reality/tables/basebuildingobjectstable.MXML").is_file()
    or not ALL_FILES.is_file(),
    reason="run tools/bootstrap.ps1 and tools/extract.py first",
)


@functools.cache
def vanilla_globals():
    return ET.parse(EXTRACTED / "gcsettlementglobals.MXML").getroot()


def spec_text():
    path = SPECS / f"{DEFENSE}.json"
    if not path.is_file():
        pytest.fail(f"{path.name} is missing")
    return path.read_text(encoding="utf-8")


def load_spec():
    return json.loads(spec_text())


@functools.cache
def build_from(text):
    out = {}
    for builder in (gen_parts.build, gen_settlement.build):
        for rel, built in builder(json.loads(text)).items():
            out[str(rel).replace("\\", "/")] = ET.fromstring(built)
    return out


def generated():
    """{posix path: parsed file} from both generators, built on the real vanilla data."""
    return build_from(spec_text())


def generated_file(name):
    out = generated()
    if name not in out:
        pytest.fail(f"{name} is not generated; the spec needs the matching keys")
    return out[name]


def field(node, name):
    return node.find(f"Property[@name='{name}']")


def value(node, name):
    return field(node, name).get("value")


def table(name):
    return {c.get("name"): c for c in vanilla_globals().find(f"Property[@name='{name}']")}


def amounts(stat, strength):
    """The (min, max) a strength means for a stat, with the sign the game applies."""
    ranges = table("PerkStatStrengthValues")[stat].find("Property[@name='PerkStatStrengthValues']")
    node = ranges.find(f"Property[@name='{strength}']")
    return float(value(node, "AmountMin")), float(value(node, "AmountMax"))


def good_when_positive(stat):
    return value(vanilla_globals().find("Property[@name='StatIsGoodWhenPositive']"), stat) == "true"


def stat_changes(node):
    return [
        (value(c.find("Property[@name='Stat']"), "SettlementStatType"), value(c.find("Property[@name='Strength']"), "SettlementStatStrength"))
        for c in field(node, "StatChanges")
    ]


def skeleton(node):
    """Field names and struct type names, without leaf values or indexes."""
    return (node.get("name"), node.get("value") if len(node) else None, [skeleton(c) for c in node])


def vanilla_judgement(index):
    return vanilla_globals().find(f"Property[@name='Judgements']/Property[@_index='{index}']")


def judgement_type(node):
    return value(field(node, "JudgementType"), "SettlementJudgementType")


def vanilla_weights(type_):
    return [
        float(value(j, "Weighting"))
        for j in vanilla_globals().find("Property[@name='Judgements']")
        if judgement_type(j) == type_
    ]


def fortify():
    root = generated_file(GLOBALS)
    entries = root.find("Property[@name='Judgements']")
    assert entries is not None and len(entries) == 1, "the module appends exactly one judgement"
    return entries[0]


def perk():
    entry = generated_file(PERKS).find(f"Property[@name='Table']/Property[@_id='{WATCH}']")
    assert entry is not None, f"{WATCH} is not in the perk patch"
    return entry


@pytest.fixture(scope="module")
def vanilla_loc_keys():
    keys = set()
    for f in (EXTRACTED / "language").glob("*english.MXML"):
        keys.update(re.findall(r'TkLocalisationEntry" _id="([^"]+)"', f.read_text(encoding="utf-8")))
    return keys


def test_watch_lowers_alert_in_the_sign_the_game_applies():
    changes = dict(stat_changes(perk()))
    assert "Alert" in changes, "OT_WATCH has no Alert change"
    assert not good_when_positive("Alert")
    low, high = amounts("Alert", changes["Alert"])
    assert high < 0, f"Alert strength {changes['Alert']} applies {low}..{high}; it must be negative to lower Alert"


def test_watch_lowers_the_sentinel_alert_level_in_the_sign_the_game_applies():
    # The Sentinels stat is what the settlement screen calls "Sentinel Alert Level", so lower is better.
    changes = dict(stat_changes(perk()))
    assert "Sentinels" in changes, "OT_WATCH has no Sentinels change"
    assert not good_when_positive("Sentinels")
    low, high = amounts("Sentinels", changes["Sentinels"])
    assert high < 0, f"Sentinels strength {changes['Sentinels']} applies {low}..{high}; it must be negative to lower it"


def test_watch_changes_only_alert_and_sentinels():
    assert sorted(s for s, _ in stat_changes(perk())) == ["Alert", "Sentinels"]


def test_watch_alert_drop_is_below_a_full_reset_and_the_sentinel_drop_is_modest():
    changes = dict(stat_changes(perk()))
    alert_max = float(table("StatsMaxValues")["Alert"].get("value"))
    sentinels_max = float(table("StatsMaxValues")["Sentinels"].get("value"))
    assert abs(amounts("Alert", changes["Alert"])[1]) < alert_max, "a persistent perk must not equal a full Alert reset"
    assert abs(amounts("Sentinels", changes["Sentinels"])[0]) <= 0.10 * sentinels_max


def test_watch_is_a_plain_perk_like_the_ones_judgements_grant():
    entry = perk()
    assert [value(entry, f) for f in ("IsNegative", "IsStarter", "IsProc", "IsJob", "IsBlessing")] == ["false"] * 5


def test_fortify_is_appended_as_a_request():
    entry = fortify()
    assert "_id" not in entry.attrib and "_index" not in entry.attrib
    assert judgement_type(entry) == "Request"


def test_without_tuning_fortify_comes_up_about_once_every_twelve_to_twenty_four_hours():
    # Rare enough that repeats after the perk is owned stay a minor nuisance, common enough to be seen.
    # BuildingChoice is left out of the type draw: it needs a building waiting to be chosen.
    root = vanilla_globals()
    mean_wait = (float(value(root, "JudgementWaitTimeMin")) + float(value(root, "JudgementWaitTimeMax"))) / 2
    type_weights = {n: float(c.get("value")) for n, c in table("JudgementSelectionWeights").items()}
    type_weights.pop("BuildingChoice")
    own = float(value(fortify(), "Weighting"))
    chance = type_weights["Request"] / sum(type_weights.values()) * own / (own + sum(vanilla_weights("Request")))
    hours = mean_wait / chance / 3600
    assert 12 <= hours <= 24, f"fortify comes up about once every {hours:.0f} hours"


def test_fortify_copies_a_vanilla_request_judgement():
    source = load_spec()["judgements"][0]["copy_from"]
    assert judgement_type(vanilla_judgement(source)) == "Request"


def test_option_one_grants_the_watch_perk_every_time():
    option = field(fortify(), "Option1List")[0]
    perks = [(value(p, "Perk"), float(value(p, "PerkChance"))) for p in field(option, "Perks")]
    assert perks == [(WATCH, 1.0)]


def test_option_one_costs_debt_in_the_sign_that_adds_debt():
    option = field(fortify(), "Option1List")[0]
    costs = [(s, g) for s, g in stat_changes(option) if s == "Debt"]
    assert costs, "option 1 has no Debt change"
    assert not good_when_positive("Debt")
    for stat, strength in costs:
        low, _ = amounts(stat, strength)
        assert low > 0, f"Debt strength {strength} must raise debt, but it applies {amounts(stat, strength)}"


def test_option_one_names_its_cost_in_english():
    key = value(field(fortify(), "Option1List")[0], "OptionText")
    assert "debt" in load_spec()["text"][key].lower()


def test_option_two_declines_without_the_perk_or_any_reward():
    option = field(fortify(), "Option2List")[0]
    assert len(field(option, "Perks")) == 0
    assert len(field(option, "AdditionalRewards")) == 0
    assert len(field(fortify(), "Option3List")) == 0


def test_generated_perk_option_and_stat_change_have_the_vanilla_structure():
    # Vanilla judgement 24 grants a perk and changes stats in option 1.
    vanilla_option = field(vanilla_judgement(24), "Option1List")[0]
    option = field(fortify(), "Option1List")[0]
    assert skeleton(field(option, "Perks")[0]) == skeleton(field(vanilla_option, "Perks")[0])
    assert skeleton(field(option, "StatChanges")[0]) == skeleton(field(vanilla_option, "StatChanges")[0])
    assert skeleton(perk()) == skeleton(vanilla_perk("SENT_QUAR"))


def vanilla_perk(id_):
    root = ET.parse(EXTRACTED / "metadata/reality/tables/settlementperkstable.MXML").getroot()
    return root.find(f"Property[@name='Table']/Property[@_id='{id_}']")


def used_text_keys():
    keys = set()
    entry = perk()
    keys |= {value(entry, "Name"), value(entry, "Description")}
    judgement = fortify()
    keys |= {value(judgement, f) for f in ("Title", "NPCTitle", "QuestionText", "DilemmaText")}
    for n in (1, 2):
        keys.add(value(field(judgement, f"Option{n}List")[0], "OptionText"))
    for product in generated_file(PRODUCTS).find("Property[@name='Table']"):
        keys |= {value(product, f) for f in ("Name", "NameLower", "Description")}
    return keys


def test_every_text_key_the_module_uses_has_english(vanilla_loc_keys):
    spec_text = load_spec()["text"]
    missing = sorted(k for k in used_text_keys() if k not in vanilla_loc_keys and k not in spec_text)
    assert not missing, f"no text for {missing}"


def test_every_text_entry_is_used_and_plain_ascii():
    spec_text = load_spec()["text"]
    assert not sorted(set(spec_text) - used_text_keys()), "text entries nothing refers to"
    for key, english in spec_text.items():
        assert english.strip() and english.isascii(), f"{key}: text must be non-empty ASCII"


def test_tower_is_a_decoration_in_the_vanilla_exterior_group_with_no_new_subgroup():
    spec = load_spec()
    part = next((p for p in spec.get("parts", []) if p["id"] == TOWER), None)
    assert part is not None, f"{TOWER} is not in the spec"
    assert part["groups"] == [["DECORATION", "DECOEXTERIOR"]]
    assert "subgroups" not in spec


def test_tower_reuses_a_vanilla_scene_that_exists_and_is_placeable_on_a_planet_base():
    source_id = next(p for p in load_spec()["parts"] if p["id"] == TOWER)["copy_from"]
    vanilla = ET.parse(EXTRACTED / "metadata/reality/tables/basebuildingobjectstable.MXML").getroot()
    source = vanilla.find(f"Property[@name='Objects']/Property[@_id='{source_id}']")
    assert value(source, "BuildableOnPlanetBase") == "true"
    assert value(source, "IsPlaceable") == "true"
    scene = value(field(source, "PlacementScene"), "Filename")
    assert scene.upper().endswith("_PLACEMENT.SCENE.MBIN")
    new = generated_file(OBJECTS).find(f"Property[@name='Objects']/Property[@_id='{TOWER}']")
    assert value(field(new, "PlacementScene"), "Filename") == scene
    files = {l.strip().lower() for l in ALL_FILES.read_text(encoding="utf-8", errors="replace").splitlines()}
    assert scene.lower() in files


def test_tower_shows_in_the_overseer_build_menu():
    # The settlement's own build menu lists only parts that can be built outside a base.
    new = generated_file(OBJECTS).find(f"Property[@name='Objects']/Property[@_id='{TOWER}']")
    assert value(new, "BuildableOnPlanet") == "true"


def test_tower_is_craftable_and_learned_only_at_s_class():
    product = generated_file(PRODUCTS).find(f"Property[@name='Table']/Property[@_id='{TOWER}']")
    assert product is not None, f"{TOWER} has no product"
    assert value(product, "IsCraftable") == "true"
    names = [p.name.upper() for p in (MODS / DEFENSE).rglob("*") if p.is_file()]
    assert not [n for n in names if "UNLOCKABLEITEMTREES" in n or "BLUEPRINT" in n]
    assert [(u["min_class"], u["recipes"]) for u in load_spec()["unlocks"]] == [("S", [TOWER])]


def test_perk_ids_and_text_keys_are_unique_across_modules():
    perks, keys = {}, {}
    for path in sorted(SPECS.glob("*.json")):
        spec = json.loads(path.read_text(encoding="utf-8"))
        for item in spec.get("perks", []):
            assert item["id"] not in perks, f"{item['id']} is in {perks[item['id']]} and {path.stem}"
            perks[item["id"]] = path.stem
        for key in spec.get("text", {}):
            assert key not in keys, f"text key {key} is in {keys[key]} and {path.stem}"
            keys[key] = path.stem


def tuning():
    path = MODS / TUNING / GLOBALS
    if not path.is_file():
        pytest.fail(f"mod/{TUNING}/{GLOBALS} is missing")
    return ET.parse(path).getroot()


def test_tuning_makes_judgements_arrive_within_a_couple_of_minutes():
    root = tuning()
    low, high = int(value(root, "JudgementWaitTimeMin")), int(value(root, "JudgementWaitTimeMax"))
    assert 0 < low <= high <= 180


def test_tuning_zeroes_every_vanilla_request_judgement_and_nothing_else_in_the_pool():
    root = tuning()
    tuned = {
        int(j.get("_index")): float(value(j, "Weighting")) for j in root.find("Property[@name='Judgements']")
    }
    request_indexes = {
        int(j.get("_index"))
        for j in vanilla_globals().find("Property[@name='Judgements']")
        if judgement_type(j) == "Request"
    }
    assert set(tuned) == request_indexes, "the tuned indexes must be exactly the vanilla Request judgements"
    assert set(tuned.values()) == {0.0}
    for j in root.find("Property[@name='Judgements']"):
        assert [c.get("name") for c in j] == ["Weighting"]


def test_tuning_changes_only_timers_pool_weights_and_the_request_type_weight():
    root = tuning()
    assert [c.get("name") for c in root] == [
        "JudgementWaitTimeMin",
        "JudgementWaitTimeMax",
        "JudgementSelectionWeights",
        "Judgements",
    ]
    assert [c.get("name") for c in field(root, "JudgementSelectionWeights")] == ["Request"]


def test_with_tuning_most_judgements_in_a_session_are_the_fortify_decision():
    # Type is drawn by JudgementSelectionWeights, then a judgement of that type by Weighting.
    root = tuning()
    type_weights = {n: float(c.get("value")) for n, c in table("JudgementSelectionWeights").items()}
    type_weights["Request"] = float(value(field(root, "JudgementSelectionWeights"), "Request"))
    request = {
        int(j.get("_index")): float(value(j, "Weighting"))
        for j in vanilla_globals().find("Property[@name='Judgements']")
        if judgement_type(j) == "Request"
    }
    request.update({int(j.get("_index")): float(value(j, "Weighting")) for j in root.find("Property[@name='Judgements']")})
    own = float(value(fortify(), "Weighting"))
    chance = type_weights["Request"] / sum(type_weights.values()) * own / (own + sum(request.values()))
    assert chance >= 0.9, f"fortify is {chance:.0%} of draws"


def test_defense_and_tuning_merge_together_in_either_order_and_compile(tmp_path):
    vanilla = vanilla_globals()
    defense = ET.parse(MODS / DEFENSE / GLOBALS).getroot()
    tuning_patch = tuning()
    vanilla_count = len(vanilla.find("Property[@name='Judgements']"))
    for n, order in enumerate(((defense, tuning_patch), (tuning_patch, defense))):
        merged = vanilla
        for patch in order:
            merged, _ = merge_preview.merge(merged, patch)
        entries = merged.find("Property[@name='Judgements']")
        assert len(entries) == vanilla_count + 1
        assert value(entries[-1], "Title") == "OT_FORT_TITLE"
        assert float(value(entries[-1], "Weighting")) > 0, "tuning must not zero the fortify judgement"
        assert [float(value(e, "Weighting")) for e in entries if judgement_type(e) == "Request"][:4] == [0.0] * 4
        out = tmp_path / str(n) / "gcsettlementglobals.MXML"
        merge_preview._write(merged, out)
        ok, log = merge_preview.compile_mxml(out, out.parent)
        assert ok, log
