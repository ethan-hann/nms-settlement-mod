"""Generate class-gated unlock missions and new-creative-game knowledge from a module spec.

Spec keys (all optional):
  unlocks:        [{id, min_class, reward, recipes: [product IDs]}]
  creative_known: [product IDs]

Each unlock is a copy of vanilla STORAGE_FIX (fleetmissiontable), a mission that starts by
itself, skips players who already know the first recipe, waits a moment, then teaches every
recipe silently under one reward message. Ours starts once any settlement building the
player oversees reaches min_class (B, A or S): the only class check vanilla data offers.
The copies are appended to npcmissiontable, a populated table that public mods append
missions to on this build; an EXML append to the empty modmissiontable crashed in testing.

creative_known appends to the creative preset's KnownProducts, which new creative games
start with; creative games otherwise never know parts added by mods.

Usage: gen_unlocks.py <spec.json> <module folder>
"""

import argparse
import copy
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EXTRACTED = REPO / "scratch" / "extracted"

TEMPLATE_TABLE = "metadata/simulation/missions/tables/fleetmissiontable.MXML"
TEMPLATE_MISSION = "STORAGE_FIX"
MISSIONS_OUT = Path("METADATA/SIMULATION/MISSIONS/TABLES/NPCMISSIONTABLE.EXML")
DIFFICULTY_OUT = Path("METADATA/GAMESTATE/DIFFICULTYCONFIG.EXML")
PRODUCT_TABLES = (
    "metadata/reality/tables/nms_basepartproducts.MXML",
    "metadata/reality/tables/nms_reality_gcproducttable.MXML",
)
CLASSES = ("B", "A", "S")
MAX_ID = 15  # mission and reward IDs are 16-byte strings with a terminator


class SpecError(Exception):
    pass


def P(attrs, *children):
    node = ET.Element("Property", attrs)
    node.extend(children)
    return node


def P_data(template, *children):
    root = ET.Element("Data", {"template": template})
    root.extend(children)
    return root


def _field(node, name):
    found = node.find(f"Property[@name='{name}']")
    if found is None:
        raise SpecError(f"template lacks {name}; the vanilla mission changed shape")
    return found


def _known_products(spec, vanilla_dir):
    known = set()
    for rel in PRODUCT_TABLES:
        path = Path(vanilla_dir) / rel
        if path.is_file():
            root = ET.parse(path).getroot()
            known.update(e.get("_id") for e in root.find("Property[@name='Table']"))
    known.update(p["id"] for p in spec.get("parts", []))
    known.update(e["id"] for e in spec.get("edits", []) if "new_product" in e)
    return known


def _condition(min_class):
    return P(
        {"name": "StartingConditions", "value": "GcMissionConditionHasSettlementBuilding"},
        P(
            {"name": "GcMissionConditionHasSettlementBuilding"},
            P({"name": "BuildingClass", "value": "GcBuildingClassification"}, P({"name": "BuildingClass", "value": "None"})),
            P({"name": "AnyBuildingClass", "value": "true"}),
            P({"name": "MinimumClass", "value": "GcInventoryClass"}, P({"name": "InventoryClass", "value": min_class})),
            P({"name": "RequireComplete", "value": "true"}),
            P({"name": "CheckAllSettlements", "value": "true"}),
        ),
    )


def _mission(template, unlock):
    m = copy.deepcopy(template)
    for node in m.iter():
        node.attrib.pop("_index", None)
    m.set("_id", unlock["id"])
    _field(m, "MissionID").set("value", unlock["id"])

    rewards = _field(m, "Rewards")
    entry = rewards[0]
    for extra in list(rewards)[1:]:
        rewards.remove(extra)
    entry.set("_id", unlock["reward"])
    _field(entry, "Id").set("value", unlock["reward"])
    items = _field(_field(entry, "List"), "List")
    item_template = copy.deepcopy(items[0])
    for item in list(items):
        items.remove(item)
    for recipe_id in unlock["recipes"]:
        item = copy.deepcopy(item_template)
        recipe = item.find(".//Property[@name='GcRewardSpecificProductRecipe']")
        _field(recipe, "ID").set("value", recipe_id)
        _field(recipe, "Silent").set("value", "true")
        items.append(item)

    starting = _field(m, "StartingConditions")
    for c in list(starting):
        starting.remove(c)
    starting.append(_condition(unlock["min_class"]))

    known = m.find(".//Property[@name='GcMissionConditionProductKnown']")
    if known is None:
        raise SpecError("template lacks its already-known check")
    _field(known, "Product").set("value", unlock["recipes"][0])
    stage = m.find(".//Property[@name='GcMissionSequenceReward']")
    if stage is None:
        raise SpecError("template lacks its reward stage")
    _field(stage, "Reward").set("value", unlock["reward"])
    _field(stage, "DebugText").set("value", f"teach the class {unlock['min_class']} settlement parts")
    return m


def _check(spec, known):
    seen = set()
    for unlock in spec.get("unlocks", []):
        for key in ("id", "reward"):
            if len(unlock[key]) > MAX_ID:
                raise SpecError(f"{unlock[key]} is longer than {MAX_ID} characters")
            if unlock[key] in seen:
                raise SpecError(f"{unlock[key]} is used twice")
            seen.add(unlock[key])
        if unlock.get("min_class") not in CLASSES:
            raise SpecError(f"{unlock['id']}: class {unlock.get('min_class')!r} must be one of {', '.join(CLASSES)}")
        if not unlock["recipes"]:
            raise SpecError(f"{unlock['id']} teaches nothing")
        for recipe_id in unlock["recipes"]:
            if recipe_id not in known:
                raise SpecError(f"{unlock['id']}: {recipe_id} is not a product in vanilla or this spec")
    for product_id in spec.get("creative_known", []):
        if product_id not in known:
            raise SpecError(f"creative_known: {product_id} is not a product in vanilla or this spec")


def to_text(root):
    root = copy.deepcopy(root)
    ET.indent(root, space="\t")
    return '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(root, encoding="unicode") + "\n"


def build(spec, vanilla_dir=EXTRACTED):
    """Return {relative path: file text}."""
    if not spec.get("unlocks") and not spec.get("creative_known"):
        return {}
    _check(spec, _known_products(spec, vanilla_dir))
    out = {}
    if spec.get("unlocks"):
        table = ET.parse(Path(vanilla_dir) / TEMPLATE_TABLE).getroot()
        template = table.find(f"Property[@name='Missions']/Property[@_id='{TEMPLATE_MISSION}']")
        if template is None:
            raise SpecError(f"vanilla mission {TEMPLATE_MISSION} not found")
        missions = P({"name": "Missions"}, *[_mission(template, u) for u in spec["unlocks"]])
        out[MISSIONS_OUT] = to_text(P_data("cGcMissionTable", missions))
    if spec.get("creative_known"):
        known = P(
            {"name": "KnownProducts"},
            *[P({"name": "KnownProducts", "value": pid}) for pid in spec["creative_known"]],
        )
        preset = P(
            {"name": "StartWithAllItemsKnownEnabledData", "value": "GcDifficultyStartWithAllItemsKnownOptionData"},
            P({"name": "InitialKnownThings", "value": "GcKnownThingsPreset"}, known),
        )
        out[DIFFICULTY_OUT] = to_text(P_data("cGcDifficultyConfig", preset))
    return out


def write(spec, module_dir, vanilla_dir=EXTRACTED):
    written = []
    for rel, text in build(spec, vanilla_dir).items():
        path = Path(module_dir) / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        written.append(path)
    return written


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("spec")
    parser.add_argument("module_dir")
    args = parser.parse_args(argv)
    for path in write(json.loads(Path(args.spec).read_text(encoding="utf-8")), args.module_dir):
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
