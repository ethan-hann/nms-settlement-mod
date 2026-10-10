"""Generate a module's settlement perk and judgement patches from a JSON spec.

Perks and judgements are long vanilla structures. Copying one from the current build
keeps every field complete; the spec only names what differs. Text keys named here
get their English from the spec's `text` key, which gen_parts.py turns into LocTable.MXML.

Spec keys (all optional):
  perks:      [{id, copy_from, name, description, stat_changes: [[stat, strength]]}]
                  -> new perk copied from the vanilla perk with _id copy_from
  judgements: [{name, copy_from, type, weighting, title, question, dilemma,
                options: [{text, perks: [[perk, chance]], stat_changes: [[stat, strength]]}]}]
                  -> new judgement appended to the pool, copied from the vanilla
                     judgement at _index copy_from
  custom_judgements: [{id, copy_from, header, title, question, dilemma, options,
                       type, cost_text, objective_text}]
                  -> new entry in CustomJudgements, copied from the vanilla custom
                     judgement with _id copy_from; type and the two wrapper texts are optional

Vanilla judgements have no _id, so a new one is appended without a key. Options never
inherit rewards, perks, stat changes or a chain from the source; the source supplies the
NPC fields and flags. Sources whose options pick their own perk are rejected, because
the copy would carry that behavior silently.

Custom judgements get Weighting 0, as vanilla's debrief judgements do: they still fire
when awarded directly, and the random draw can never pick them.

Usage: gen_settlement.py <spec.json> <module folder>
"""

import argparse
import copy
import json
import sys
from pathlib import Path

from gen_parts import EXTRACTED, MAX_ID, MAX_LOC_KEY, SpecError, Table, P, to_text

TABLES = Path("METADATA/REALITY/TABLES")
PERKS = ("metadata/reality/tables/settlementperkstable.MXML", "Table", TABLES / "SETTLEMENTPERKSTABLE.EXML")
GLOBALS = ("gcsettlementglobals.MXML", "Judgements", Path("GLOBALS/GCSETTLEMENTGLOBALS.EXML"))
CUSTOM = "CustomJudgements"
MAX_JUDGEMENT_ID = 15  # 16-byte string; whether it needs a terminator is unknown, so assume it does
MAX_OPTIONS = 4
OPTION_FLAGS = ("UsePolicyPerk", "UsePolicyStat", "UseGiftReward", "UseTechPerk")


def _child(node, name, owner):
    found = node.find(f"Property[@name='{name}']")
    if found is None:
        raise SpecError(f"{owner}: no field {name!r}")
    return found


def _set(node, name, value, owner):
    _child(node, name, owner).set("value", str(value))


def _strip_index(entry):
    for node in entry.iter():
        node.attrib.pop("_index", None)


def _clear(node):
    for child in list(node):
        node.remove(child)
    node.text = None


def _loc_key(key, owner):
    if len(key) > MAX_LOC_KEY:
        raise SpecError(f"{owner}: loc key {key} is longer than {MAX_LOC_KEY} characters")
    return key


class Vocabulary:
    """The stats, strengths and judgement types the current build defines."""

    def __init__(self, globals_root):
        self.stats = {c.get("name") for c in _list(globals_root, "StatsMaxValues")}
        self.types = {c.get("name") for c in _list(globals_root, "JudgementSelectionWeights")}
        self.ranges = {
            stat.get("name"): {s.get("name") for s in _child(stat, "PerkStatStrengthValues", "PerkStatStrengthValues")}
            for stat in _list(globals_root, "PerkStatStrengthValues")
        }

    def check_change(self, stat, strength, owner):
        if stat not in self.stats:
            raise SpecError(f"{owner}: unknown stat {stat!r}; vanilla has {sorted(self.stats)}")
        known = self.ranges.get(stat, set())
        if strength not in known:
            raise SpecError(f"{owner}: stat {stat} has no strength {strength!r}; vanilla has {sorted(known)}")


def _list(root, name):
    found = root.find(f"Property[@name='{name}']")
    if found is None:
        raise SpecError(f"vanilla has no {name} list")
    return found


def _stat_change(stat, strength):
    return P(
        {"name": "StatChanges", "value": "GcSettlementStatChange"},
        P({"name": "Stat", "value": "GcSettlementStatType"}, P({"name": "SettlementStatType", "value": stat})),
        P(
            {"name": "Strength", "value": "GcSettlementStatStrength"},
            P({"name": "SettlementStatStrength", "value": strength}),
        ),
        P({"name": "DirectlyChangePopulation", "value": "false"}),
    )


def _perk_option(perk, chance):
    return P(
        {"name": "Perks", "value": "GcSettlementJudgementPerkOption"},
        P({"name": "Perk", "value": perk}),
        P({"name": "PerkChance", "value": f"{chance:.6f}"}),
    )


def _fill_changes(node, changes, vocab, owner):
    _clear(node)
    for stat, strength in changes:
        vocab.check_change(stat, strength, owner)
        node.append(_stat_change(stat, strength))


def _perk(item, table, vocab):
    id_ = item["id"]
    entry = copy.deepcopy(table.vanilla_entry(item["copy_from"]))
    _strip_index(entry)
    entry.set("_id", id_)
    _set(entry, "ID", id_, id_)
    _set(entry, "Name", _loc_key(item["name"], id_), id_)
    _set(entry, "Description", _loc_key(item["description"], id_), id_)
    _fill_changes(_child(entry, "StatChanges", id_), item["stat_changes"], vocab, id_)
    return entry


def _check_perk_ids(items, vanilla):
    seen = set()
    for item in items:
        id_ = item["id"]
        if len(id_) > MAX_ID:
            raise SpecError(f"{id_} is longer than {MAX_ID} characters")
        if id_ in seen:
            raise SpecError(f"{id_} appears twice in the spec")
        if vanilla.root.find(f"Property[@name='{vanilla.list_name}']/Property[@_id='{id_}']") is not None:
            raise SpecError(f"{id_} already exists in vanilla; pick another id")
        seen.add(id_)


def _source_judgement(table, index):
    node = table.root.find(f"Property[@name='Judgements']/Property[@_index='{index}']")
    if node is None:
        raise SpecError(f"no vanilla judgement at _index {index}")
    return node


def _plain_option(option, owner):
    for flag in OPTION_FLAGS:
        if _child(option, flag, owner).get("value") == "true":
            raise SpecError(f"{owner}: the source option sets {flag}; copy a judgement that does not")


def _option(list_node, spec, vocab, perk_ids, owner):
    if len(list_node) != 1:
        raise SpecError(f"{owner}: the source option list has {len(list_node)} alternates; only one is supported")
    option = list_node[0]
    _plain_option(option, owner)
    _set(option, "OptionText", _loc_key(spec["text"], owner), owner)
    perks = _child(option, "Perks", owner)
    _clear(perks)
    for perk, chance in spec.get("perks", []):
        if perk not in perk_ids:
            raise SpecError(f"{owner}: option grants {perk}, which is neither vanilla nor in this spec")
        perks.append(_perk_option(perk, chance))
    _fill_changes(_child(option, "StatChanges", owner), spec.get("stat_changes", []), vocab, owner)
    _clear(_child(option, "AdditionalRewards", owner))
    _set(option, "ChainedJudgementID", "", owner)


def _set_type(data, type_, vocab, owner):
    if type_ not in vocab.types:
        raise SpecError(f"{owner}: unknown judgement type {type_!r}; vanilla has {sorted(vocab.types)}")
    _set(_child(data, "JudgementType", owner), "SettlementJudgementType", type_, owner)


def _fill_data(data, item, vocab, perk_ids, owner):
    """Text and options shared by pool and custom judgements."""
    for field, key in (("Title", "title"), ("QuestionText", "question"), ("DilemmaText", "dilemma")):
        _set(data, field, _loc_key(item[key], owner), owner)
    lists = [_child(data, f"Option{n}List", owner) for n in range(1, MAX_OPTIONS + 1)]
    source_count = sum(1 for node in lists if len(node))
    if source_count != len(item["options"]):
        raise SpecError(f"{owner}: spec has {len(item['options'])} options but the source has {source_count}")
    for node, spec in zip(lists, item["options"]):
        _option(node, spec, vocab, perk_ids, owner)


def _judgement(item, table, vocab, perk_ids, number):
    owner = item.get("name") or f"judgement {number}"
    entry = copy.deepcopy(_source_judgement(table, item["copy_from"]))
    _strip_index(entry)
    _set_type(entry, item["type"], vocab, owner)
    if item["weighting"] <= 0:
        raise SpecError(f"{owner}: weighting must be positive")
    _set(entry, "Weighting", f"{item['weighting']:.6f}", owner)
    _fill_data(entry, item, vocab, perk_ids, owner)
    return entry


def _custom_source(table, id_):
    return table.root.find(f"Property[@name='{CUSTOM}']/Property[@_id='{id_}']")


def _check_custom_ids(items, table):
    seen = set()
    for item in items:
        id_ = item["id"]
        if len(id_) > MAX_JUDGEMENT_ID:
            raise SpecError(f"{id_} is longer than {MAX_JUDGEMENT_ID} characters")
        if id_ in seen:
            raise SpecError(f"{id_} appears twice in the spec")
        if _custom_source(table, id_) is not None:
            raise SpecError(f"{id_} already exists in vanilla; pick another id")
        seen.add(id_)


def _custom_judgement(item, table, vocab, perk_ids):
    id_ = item["id"]
    source = _custom_source(table, item["copy_from"])
    if source is None:
        raise SpecError(f"{id_}: no vanilla custom judgement {item['copy_from']}")
    entry = copy.deepcopy(source)
    _strip_index(entry)
    entry.set("_id", id_)
    _set(entry, "ID", id_, id_)
    # The source's cost and objective text belong to its own story, so they never carry over.
    _set(entry, "CustomCostText", _loc_key(item.get("cost_text", ""), id_), id_)
    _set(entry, "CustomMissionObjectiveText", _loc_key(item.get("objective_text", ""), id_), id_)
    data = _child(entry, "Data", id_)
    if "type" in item:
        _set_type(data, item["type"], vocab, id_)
    _set(data, "Weighting", f"{0:.6f}", id_)
    _set(data, "HeaderOverride", _loc_key(item["header"], id_), id_)
    _fill_data(data, item, vocab, perk_ids, id_)
    return entry


def build(spec, vanilla_dir=EXTRACTED):
    """Return {relative path: file text} for the module."""
    perk_items, judgement_items = spec.get("perks", []), spec.get("judgements", [])
    custom_items = spec.get("custom_judgements", [])
    if not perk_items and not judgement_items and not custom_items:
        return {}
    perks, settings = Table(vanilla_dir, PERKS), Table(vanilla_dir, GLOBALS)
    vocab = Vocabulary(settings.root)
    _check_perk_ids(perk_items, perks)
    _check_custom_ids(custom_items, settings)
    perk_ids = {c.get("_id") for c in _list(perks.root, "Table")} | {i["id"] for i in perk_items}

    for item in perk_items:
        perks.add(_perk(item, perks, vocab))
    for number, item in enumerate(judgement_items, 1):
        settings.add(_judgement(item, settings, vocab, perk_ids, number))
    for item in custom_items:
        settings.add(_custom_judgement(item, settings, vocab, perk_ids), CUSTOM)

    return {table.out: to_text(table.patch) for table in (perks, settings) if table.used()}


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
