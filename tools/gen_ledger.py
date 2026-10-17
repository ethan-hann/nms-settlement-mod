"""Generate the Fair Ledger modules' patches from a JSON spec.

Spec keys (all optional):
  debt_step:        n -> the Debt PositiveLarge strength becomes a flat cut of n
  terminal_options: [{id, text, debt_steps}] -> per option, appended to the Administration
                    Terminal (SETTLEMENT_ADMIN) as a copy of its first option:
                      a units cost C_OT_FL_<id>, copied from vanilla C_FLT_TRADE_9, at
                      UNITS_PER_DEBT units for each debt it clears;
                      a reward R_OT_FL_DEBT<debt_steps> of that many Debt PositiveLarge steps;
                      text, the option's loc key, which needs an entry in the spec's text
  text_overrides:   [vanilla loc key] -> keys in the spec's text that replace vanilla text;
                    every other text key must be new (OT_FL_)
  match_upkeep_to_production: [building] -> each building's Base Upkeep range becomes
                    its Base Production range, both read from vanilla

gen_parts.py writes the spec's text into LocTable.MXML.

Usage: gen_ledger.py <spec.json> <module folder>
"""

import argparse
import copy
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from gen_parts import EXTRACTED, P, SpecError, to_text

TABLES = Path("METADATA/REALITY/TABLES")
COSTS = ("metadata/reality/tables/costtable.MXML", TABLES / "COSTTABLE.EXML")
REWARDS_OUT = TABLES / "REWARDTABLE.EXML"
DIALOG = ("metadata/reality/tables/nms_dialog_gcalienpuzzletable.MXML", TABLES / "NMS_DIALOG_GCALIENPUZZLETABLE.EXML")
GLOBALS = ("gcsettlementglobals.MXML", Path("GLOBALS/GCSETTLEMENTGLOBALS.EXML"))

# The premium keeps buildings and decisions the main way out of debt; one constant so options cannot drift.
UNITS_PER_DEBT = 2
COST_SOURCE = "C_FLT_TRADE_9"
TERMINAL = "SETTLEMENT_ADMIN"
# Session 6: the terminal lists six options and drops the rest.
MAX_TERMINAL_OPTIONS = 6
MAX_TABLE_ID = 15  # 16-byte string, assumed to need a terminator
PREFIX = "OT_FL_"


def _child(node, path, owner):
    found = node.find(path)
    if found is None:
        raise SpecError(f"{owner}: vanilla has no {path}")
    return found


def _strip_index(entry):
    for node in entry.iter():
        node.attrib.pop("_index", None)


def _clear(node):
    for child in list(node):
        node.remove(child)


def _table_id(id_, owner):
    if len(id_) > MAX_TABLE_ID:
        raise SpecError(f"{owner}: {id_} is longer than {MAX_TABLE_ID} characters")
    return id_


def _vanilla_keys(vanilla_dir):
    keys = set()
    for path in (Path(vanilla_dir) / "language").glob("*english.MXML"):
        keys.update(re.findall(r'TkLocalisationEntry" _id="([^"]+)"', path.read_text(encoding="utf-8")))
    return keys


def _check_text(spec, vanilla_dir):
    text, overrides = spec.get("text", {}), spec.get("text_overrides", [])
    if overrides:
        known = _vanilla_keys(vanilla_dir)
        for key in overrides:
            if key not in known:
                raise SpecError(f"text_overrides: {key} is not a vanilla text key")
            if key not in text:
                raise SpecError(f"text_overrides: {key} has no entry in text")
    for key in text:
        if not key.startswith(PREFIX) and key not in overrides:
            raise SpecError(f"{key}: new text keys start with {PREFIX}; list vanilla keys in text_overrides")


def _cost(source, id_, units):
    entry = copy.deepcopy(source)
    _strip_index(entry)
    entry.set("_id", id_)
    _child(entry, "Property[@name='Id']", id_).set("value", id_)
    money = entry.find("Property[@name='Cost']/Property[@name='GcCostMoney']")
    currency = entry.find(".//Property[@name='CostCurrency']/Property[@name='Currency']")
    if money is None or currency is None or currency.get("value") != "Units":
        raise SpecError(f"{COST_SOURCE} is no longer a units cost; pick another source")
    _child(money, "Property[@name='Cost']", id_).set("value", str(units))
    return entry


def _debt_step_item():
    return P(
        {"name": "List", "value": "GcRewardTableItem"},
        P({"name": "PercentageChance", "value": "100.000000"}),
        P({"name": "LabelID", "value": ""}),
        P(
            {"name": "Reward", "value": "GcRewardSettlementStat"},
            P(
                {"name": "GcRewardSettlementStat"},
                P(
                    {"name": "StatToAward", "value": "GcSettlementStatChange"},
                    P({"name": "Stat", "value": "GcSettlementStatType"}, P({"name": "SettlementStatType", "value": "Debt"})),
                    P(
                        {"name": "Strength", "value": "GcSettlementStatStrength"},
                        P({"name": "SettlementStatStrength", "value": "PositiveLarge"}),
                    ),
                    P({"name": "DirectlyChangePopulation", "value": "false"}),
                ),
                # The player sees each cut, as with a decision.
                P({"name": "Silent", "value": "false"}),
            ),
        ),
    )


def _reward(id_, steps):
    return P(
        {"name": "SettlementTable", "value": "GcGenericRewardTableEntry", "_id": id_},
        P({"name": "Id", "value": id_}),
        P(
            {"name": "List", "value": "GcRewardTableItemList"},
            P({"name": "RewardChoice", "value": "GiveAll"}),
            P({"name": "OverrideZeroSeed", "value": "false"}),
            P({"name": "UseInventoryChoiceOverride", "value": "false"}),
            P({"name": "IncrementStat", "value": ""}),
            P({"name": "List"}, *[_debt_step_item() for _ in range(steps)]),
        ),
    )


def _option(source, key, cost_id, reward_id):
    entry = copy.deepcopy(source)
    _strip_index(entry)
    for field, value in (("Name", key), ("Cost", cost_id), ("KeepOpen", "true"), ("DisplayCost", "true")):
        _child(entry, f"Property[@name='{field}']", key).set("value", value)
    rewards = _child(entry, "Property[@name='Rewards']", key)
    _clear(rewards)
    rewards.append(P({"name": "Rewards", "value": reward_id}))
    # Session 6: a disabling condition did nothing on this terminal, so none is carried over.
    _clear(_child(entry, "Property[@name='DisablingConditions']", key))
    return entry


def _check_options(items, text):
    seen = set()
    for item in items:
        id_ = item.get("id", "")
        owner = f"terminal option {id_ or '?'}"
        _table_id(f"C_{PREFIX}{id_}", owner)
        if id_ in seen:
            raise SpecError(f"{owner} appears twice in the spec")
        seen.add(id_)
        steps = item.get("debt_steps")
        if not isinstance(steps, int) or steps < 1:
            raise SpecError(f"{owner}: debt_steps must be a positive whole number")
        _table_id(f"R_{PREFIX}DEBT{steps}", owner)
        key = item.get("text", "")
        if not key.startswith(PREFIX):
            raise SpecError(f"{owner}: text key {key!r} must start with {PREFIX}")
        if key not in text:
            raise SpecError(f"{owner}: no text for {key}")


def _terminal(spec, vanilla_dir, out):
    items = spec["terminal_options"]
    step = spec.get("debt_step")
    if not isinstance(step, int) or step < 1:
        raise SpecError("terminal_options need a positive debt_step")
    _check_options(items, spec.get("text", {}))

    dialog = ET.parse(Path(vanilla_dir) / DIALOG[0]).getroot()
    vanilla_options = _child(dialog, f"Property[@name='Table']/Property[@_id='{TERMINAL}']/Property[@name='Options']", TERMINAL)
    if len(vanilla_options) + len(items) > MAX_TERMINAL_OPTIONS:
        raise SpecError(
            f"{TERMINAL} would have {len(vanilla_options) + len(items)} options; the terminal shows six"
        )
    costs = ET.parse(Path(vanilla_dir) / COSTS[0]).getroot()
    cost_source = _child(costs, f"Property[@name='InteractionTable']/Property[@_id='{COST_SOURCE}']", COST_SOURCE)

    cost_list, reward_list = P({"name": "InteractionTable"}), P({"name": "SettlementTable"})
    option_list = P({"name": "Options"})
    rewards = {}
    for item in items:
        steps = item["debt_steps"]
        cost_id, reward_id = f"C_{PREFIX}{item['id']}", f"R_{PREFIX}DEBT{steps}"
        cost_list.append(_cost(cost_source, cost_id, UNITS_PER_DEBT * step * steps))
        if reward_id not in rewards:
            rewards[reward_id] = _reward(reward_id, steps)
            reward_list.append(rewards[reward_id])
        option_list.append(_option(vanilla_options[0], item["text"], cost_id, reward_id))

    out[COSTS[1]] = to_text(_data(costs, cost_list))
    # The reward table is large, so its template is named rather than read.
    out[REWARDS_OUT] = to_text(_data_template("cGcRewardTable", reward_list))
    entry = P({"name": "Table", "value": "GcAlienPuzzleEntry", "_id": TERMINAL}, option_list)
    out[DIALOG[1]] = to_text(_data(dialog, P({"name": "Table"}, entry)))


def _data(vanilla_root, *children):
    return _data_template(vanilla_root.get("template"), *children)


def _data_template(template, *children):
    root = ET.Element("Data", {"template": template})
    root.extend(children)
    return root


def _debt_step(settings, step):
    path = (
        "Property[@name='PerkStatStrengthValues']/Property[@name='Debt']"
        "/Property[@name='PerkStatStrengthValues']/Property[@name='PositiveLarge']"
    )
    vanilla = _child(settings, path, "debt_step")
    for field in ("AmountMin", "AmountMax"):
        _child(vanilla, f"Property[@name='{field}']", "debt_step")
    # Debt strengths are negative cuts; a flat range makes every step clear exactly debt_step.
    return P(
        {"name": "PerkStatStrengthValues"},
        P(
            {"name": "Debt", "value": "GcSettlementStatStrengthData"},
            P(
                {"name": "PerkStatStrengthValues"},
                P(
                    {"name": "PositiveLarge", "value": "GcSettlementStatStrengthRanges"},
                    P({"name": "AmountMin", "value": str(-step)}),
                    P({"name": "AmountMax", "value": str(-step)}),
                ),
            ),
        ),
    )


def _stat_item(base, stat, building):
    for item in base:
        type_ = item.find("Property[@name='Type']/Property[@name='SettlementStatType']")
        if type_ is not None and type_.get("value") == stat:
            return item
    raise SpecError(f"{building}: vanilla Base has no {stat} item")


def _upkeep(settings, buildings):
    contributions = _child(settings, "Property[@name='SettlementBuildingContributions']", "match_upkeep_to_production")
    patch = P({"name": "SettlementBuildingContributions"})
    if len(set(buildings)) != len(buildings):
        raise SpecError("match_upkeep_to_production names a building twice")
    for name in buildings:
        vanilla = contributions.find(f"Property[@name='{name}']")
        if vanilla is None:
            raise SpecError(f"{name}: not a building in vanilla SettlementBuildingContributions")
        base = _child(vanilla, "Property[@name='Base']", name)
        production, upkeep = _stat_item(base, "Production", name), _stat_item(base, "Upkeep", name)
        # The item is matched by the index vanilla gives it, so the patch edits only the Upkeep range.
        patch.append(
            P(
                {"name": name, "value": vanilla.get("value")},
                P(
                    {"name": "Base"},
                    P(
                        {"name": "Base", "value": upkeep.get("value"), "_index": upkeep.get("_index")},
                        P({"name": "MinValue", "value": production.find("Property[@name='MinValue']").get("value")}),
                        P({"name": "MaxValue", "value": production.find("Property[@name='MaxValue']").get("value")}),
                    ),
                ),
            )
        )
    return patch


def build(spec, vanilla_dir=EXTRACTED):
    """Return {relative path: file text} for the module."""
    if not any(k in spec for k in ("debt_step", "terminal_options", "text_overrides", "match_upkeep_to_production")):
        return {}
    _check_text(spec, vanilla_dir)
    out = {}
    if spec.get("terminal_options"):
        _terminal(spec, vanilla_dir, out)
    settings_parts = []
    if "debt_step" in spec or "match_upkeep_to_production" in spec:
        settings = ET.parse(Path(vanilla_dir) / GLOBALS[0]).getroot()
        if "debt_step" in spec:
            settings_parts.append(_debt_step(settings, spec["debt_step"]))
        if spec.get("match_upkeep_to_production"):
            settings_parts.append(_upkeep(settings, spec["match_upkeep_to_production"]))
        out[GLOBALS[1]] = to_text(_data(settings, *settings_parts))
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
    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    for path in write(spec, args.module_dir):
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
