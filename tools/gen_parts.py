"""Generate a module's base-part table patches and LocTable.MXML from a JSON spec.

A new part needs three table entries (object, cost, product) that are hundreds of
lines of vanilla fields. Copying them from a vanilla part of the current build keeps
them complete and current; the spec only names what differs.

Spec keys (all optional):
  text:      {loc_key: "English text"}                      -> LocTable.MXML
  subgroups: [{group, id, name}]                            -> new build-menu subgroup in a vanilla group
  parts:     [{id, copy_from, object: {field: value}, groups: [[group, subgroup]],
               product_from, product: {field: value}}]      -> new object, cost and product entries;
               the cost entry is copied only if the source has one, and product_from names
               another part to copy the product from (for sources with no base-part product)
  edits:     [{id, object: {field: value}, add_groups: [[group, subgroup]],
               new_product: {copy_from, fields: {field: value}}}]  -> changes to a vanilla part

Field names may be dotted to reach into a struct, for example "Icon.Filename".

Usage: gen_parts.py <spec.json> <module folder>
"""

import argparse
import copy
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EXTRACTED = REPO / "scratch" / "extracted"
MAX_ID = 16
MAX_LOC_KEY = 31  # longest vanilla key; the ID field is 32 bytes

TABLES = Path("METADATA/REALITY/TABLES")
OBJECTS = ("metadata/reality/tables/basebuildingobjectstable.MXML", "Objects", TABLES / "BASEBUILDINGOBJECTSTABLE.EXML")
COSTS = ("metadata/reality/tables/basebuildingcoststable.MXML", "ObjectCosts", TABLES / "BASEBUILDINGCOSTSTABLE.EXML")
PRODUCTS = ("metadata/reality/tables/nms_basepartproducts.MXML", "Table", TABLES / "NMS_BASEPARTPRODUCTS.EXML")
LOC_FILE = Path("LocTable.MXML")
LOC_LANGUAGES = ("English", "USEnglish")


class SpecError(Exception):
    pass


def P(attrs, *children):
    node = ET.Element("Property", attrs)
    node.extend(children)
    return node


class Table:
    """One vanilla table plus the patch being built for it."""

    def __init__(self, vanilla_dir, source):
        rel, self.list_name, self.out = source
        self.root = ET.parse(Path(vanilla_dir) / rel).getroot()
        self.patch = ET.Element("Data", {"template": self.root.get("template")})
        self.lists = {}

    def has(self, id_):
        return self.root.find(f"Property[@name='{self.list_name}']/Property[@_id='{id_}']") is not None

    def vanilla_entry(self, id_):
        node = self.root.find(f"Property[@name='{self.list_name}']/Property[@_id='{id_}']")
        if node is None:
            raise SpecError(f"{id_} not found in vanilla {self.out.name}")
        return node

    def patch_list(self, name):
        if name not in self.lists:
            self.lists[name] = ET.SubElement(self.patch, "Property", {"name": name})
        return self.lists[name]

    def add(self, entry, list_name=None):
        self.patch_list(list_name or self.list_name).append(entry)

    def used(self):
        return bool(self.lists)


def _field(entry, dotted, owner):
    node = entry
    for part in dotted.split("."):
        nxt = node.find(f"Property[@name='{part}']")
        if nxt is None:
            raise SpecError(f"{owner}: no field {dotted!r}")
        node = nxt
    return node


def _set(entry, overrides, owner):
    for dotted, value in (overrides or {}).items():
        node = _field(entry, dotted, owner)
        if len(node):
            raise SpecError(f"{owner}: {dotted!r} is a struct; name one of its fields")
        node.set("value", str(value))


def _strip_index(entry):
    for node in entry.iter():
        node.attrib.pop("_index", None)


def _group(group, subgroup):
    return P(
        {"name": "Groups", "value": "GcBaseBuildingEntryGroup"},
        P({"name": "Group", "value": group}),
        P({"name": "SubGroupName", "value": subgroup}),
        P({"name": "SubGroup", "value": "0"}),
    )


def _copy_entry(table, source_id, new_id, owner):
    entry = copy.deepcopy(table.vanilla_entry(source_id))
    _strip_index(entry)
    entry.set("_id", new_id)
    _field(entry, "ID", owner).set("value", new_id)
    return entry


def _product_source(products, part):
    src = part.get("product_from", part["copy_from"])
    if not products.has(src):
        hint = "" if "product_from" in part else "; set product_from to copy another part's product"
        raise SpecError(f"{src} has no product in vanilla {products.out.name}{hint}")
    return src


def _check_ids(spec):
    seen = set()
    for item in spec.get("parts", []) + spec.get("edits", []):
        id_ = item["id"]
        if len(id_) > MAX_ID:
            raise SpecError(f"{id_} is longer than {MAX_ID} characters")
        if id_ in seen:
            raise SpecError(f"{id_} appears twice in the spec")
        seen.add(id_)


def _loc_table(text):
    table = P({"name": "Table"})
    for key, english in text.items():
        if len(key) > MAX_LOC_KEY:
            raise SpecError(f"loc key {key} is longer than {MAX_LOC_KEY} characters")
        entry = P({"name": "Table", "value": "TkLocalisationEntry", "_id": key}, P({"name": "Id", "value": key}))
        for lang in LOC_LANGUAGES:
            entry.append(P({"name": lang, "value": english}))
        table.append(entry)
    root = ET.Element("Data", {"template": "cTkLocalisationTable"})
    root.append(table)
    return root


def to_text(root):
    root = copy.deepcopy(root)
    ET.indent(root, space="\t")
    return '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(root, encoding="unicode") + "\n"


def build(spec, vanilla_dir=EXTRACTED):
    """Return {relative path: file text} for the module."""
    _check_ids(spec)
    objects = Table(vanilla_dir, OBJECTS)
    costs = Table(vanilla_dir, COSTS)
    products = Table(vanilla_dir, PRODUCTS)

    for sub in spec.get("subgroups", []):
        group = P({"name": "Groups", "value": "GcBaseBuildingGroup", "_id": sub["group"]})
        if objects.root.find(f"Property[@name='Groups']/Property[@_id='{sub['group']}']") is None:
            raise SpecError(f"build group {sub['group']} not found in vanilla")
        group.append(
            P(
                {"name": "SubGroups"},
                P(
                    {"name": "SubGroups", "value": "GcBaseBuildingSubGroup", "_id": sub["id"]},
                    P({"name": "Id", "value": sub["id"]}),
                    P({"name": "Name", "value": sub["name"]}),
                ),
            )
        )
        objects.add(group, "Groups")

    for part in spec.get("parts", []):
        id_, src = part["id"], part["copy_from"]
        entry = _copy_entry(objects, src, id_, id_)
        flag = entry.find("Property[@name='IsFromModFolder']")
        if flag is not None:
            # Mods that add parts set this; it marks the entry as not from the vanilla tables.
            flag.set("value", "true")
        _set(entry, part.get("object"), id_)
        if "groups" in part:
            groups = _field(entry, "Groups", id_)
            for child in list(groups):
                groups.remove(child)
            for g, s in part["groups"]:
                groups.append(_group(g, s))
        objects.add(entry)
        # Most vanilla parts have no cost entry, so a missing one is not an error.
        if costs.has(src):
            costs.add(_copy_entry(costs, src, id_, id_))
        product = _copy_entry(products, _product_source(products, part), id_, id_)
        _set(product, part.get("product"), id_)
        products.add(product)

    for edit in spec.get("edits", []):
        id_ = edit["id"]
        vanilla = objects.vanilla_entry(id_)
        entry = P({"name": "Objects", "value": vanilla.get("value"), "_id": id_})
        for dotted, value in (edit.get("object") or {}).items():
            _field(vanilla, dotted, id_)
            if "." in dotted:
                raise SpecError(f"{id_}: edits take top-level fields only, not {dotted!r}")
            entry.append(P({"name": dotted, "value": str(value)}))
        if edit.get("add_groups"):
            _field(vanilla, "Groups", id_)
            entry.append(P({"name": "Groups"}, *[_group(g, s) for g, s in edit["add_groups"]]))
        objects.add(entry)
        if "new_product" in edit:
            np = edit["new_product"]
            if products.root.find(f"Property[@name='Table']/Property[@_id='{id_}']") is not None:
                raise SpecError(f"{id_} already has a vanilla product; edit it instead")
            product = _copy_entry(products, np["copy_from"], id_, id_)
            _set(product, np.get("fields"), id_)
            products.add(product)

    out = {}
    for table in (objects, costs, products):
        if table.used():
            out[table.out] = to_text(table.patch)
    if spec.get("text"):
        out[LOC_FILE] = to_text(_loc_table(spec["text"]))
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
