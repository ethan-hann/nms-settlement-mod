import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

import merge_preview
from merge_preview import PatchError

VANILLA = """<?xml version="1.0" encoding="utf-8"?>
<Data template="cGcBaseBuildingTable">
  <Property name="Scale" value="1.000000" />
  <Property name="Objects">
    <Property name="Objects" value="GcBaseBuildingEntry" _id="DECALPATH">
      <Property name="ID" value="DECALPATH" />
      <Property name="PlanetBaseLimit" value="50" />
      <Property name="Style" value="GcBaseBuildingPartStyle">
        <Property name="Style" value="None" />
      </Property>
      <Property name="Groups" />
    </Property>
    <Property name="Objects" value="GcBaseBuildingEntry" _id="S_FLOOR_Q">
      <Property name="ID" value="S_FLOOR_Q" />
      <Property name="PlanetBaseLimit" value="0" />
      <Property name="Style" value="GcBaseBuildingPartStyle">
        <Property name="Style" value="None" />
      </Property>
      <Property name="Groups">
        <Property name="Groups" value="GcBaseBuildingEntryGroup" _index="0">
          <Property name="Group" value="BASIC_S" />
        </Property>
      </Property>
    </Property>
  </Property>
</Data>
"""


def merged(patch_text, vanilla_text=VANILLA):
    vanilla = ET.fromstring(vanilla_text)
    patch = ET.fromstring(patch_text)
    result, edits = merge_preview.merge(vanilla, patch)
    return result, edits


def entry(root, id_):
    return root.find(f"Property[@name='Objects']/Property[@_id='{id_}']")


def value(node, name):
    return node.find(f"Property[@name='{name}']").get("value")


def test_top_level_field_is_set_and_recorded():
    root, edits = merged('<Data template="cGcBaseBuildingTable"><Property name="Scale" value="2.000000" /></Data>')
    assert value(root, "Scale") == "2.000000"
    assert edits == [{"path": "Scale", "kind": "changed", "old": "1.000000", "new": "2.000000"}]


def test_entry_matched_by_id_gets_its_field_changed():
    root, edits = merged(
        '<Data template="cGcBaseBuildingTable"><Property name="Objects">'
        '<Property name="Objects" value="GcBaseBuildingEntry" _id="DECALPATH">'
        '<Property name="PlanetBaseLimit" value="200" />'
        "</Property></Property></Data>"
    )
    assert value(entry(root, "DECALPATH"), "PlanetBaseLimit") == "200"
    assert value(entry(root, "S_FLOOR_Q"), "PlanetBaseLimit") == "0"
    assert edits == [
        {"path": "Objects[DECALPATH].PlanetBaseLimit", "kind": "changed", "old": "50", "new": "200"}
    ]


def test_unknown_id_appends_a_new_entry():
    root, edits = merged(
        '<Data template="cGcBaseBuildingTable"><Property name="Objects">'
        '<Property name="Objects" value="GcBaseBuildingEntry" _id="OT_PATH_TILE">'
        '<Property name="ID" value="OT_PATH_TILE" />'
        '<Property name="PlanetBaseLimit" value="300" />'
        "</Property></Property></Data>"
    )
    objects = root.find("Property[@name='Objects']")
    assert [o.get("_id") for o in objects] == ["DECALPATH", "S_FLOOR_Q", "OT_PATH_TILE"]
    assert edits == [{"path": "Objects[OT_PATH_TILE]", "kind": "added"}]


def test_item_without_id_or_index_is_appended_even_to_an_empty_list():
    root, edits = merged(
        '<Data template="cGcBaseBuildingTable"><Property name="Objects">'
        '<Property name="Objects" value="GcBaseBuildingEntry" _id="DECALPATH">'
        '<Property name="Groups">'
        '<Property name="Groups" value="GcBaseBuildingEntryGroup">'
        '<Property name="Group" value="OT_SETTLEMENT" />'
        "</Property></Property></Property></Property></Data>"
    )
    groups = entry(root, "DECALPATH").find("Property[@name='Groups']")
    assert len(groups) == 1
    assert value(groups[0], "Group") == "OT_SETTLEMENT"
    assert edits == [{"path": "Objects[DECALPATH].Groups[+]", "kind": "added"}]


def test_index_matches_a_list_item():
    root, edits = merged(
        '<Data template="cGcBaseBuildingTable"><Property name="Objects">'
        '<Property name="Objects" value="GcBaseBuildingEntry" _id="S_FLOOR_Q">'
        '<Property name="Groups">'
        '<Property name="Groups" value="GcBaseBuildingEntryGroup" _index="0">'
        '<Property name="Group" value="OT_SETTLEMENT" />'
        "</Property></Property></Property></Property></Data>"
    )
    groups = entry(root, "S_FLOOR_Q").find("Property[@name='Groups']")
    assert len(groups) == 1
    assert value(groups[0], "Group") == "OT_SETTLEMENT"
    assert edits[0]["path"] == "Objects[S_FLOOR_Q].Groups[0].Group"


def test_index_out_of_range_is_an_error():
    with pytest.raises(PatchError, match="_index 3"):
        merged(
            '<Data template="cGcBaseBuildingTable"><Property name="Objects">'
            '<Property name="Objects" value="GcBaseBuildingEntry" _id="S_FLOOR_Q">'
            '<Property name="Groups">'
            '<Property name="Groups" value="GcBaseBuildingEntryGroup" _index="3">'
            '<Property name="Group" value="X" />'
            "</Property></Property></Property></Property></Data>"
        )


def test_struct_field_named_like_its_parent_is_a_field_not_a_list_item():
    root, edits = merged(
        '<Data template="cGcBaseBuildingTable"><Property name="Objects">'
        '<Property name="Objects" value="GcBaseBuildingEntry" _id="DECALPATH">'
        '<Property name="Style" value="GcBaseBuildingPartStyle">'
        '<Property name="Style" value="Stone" />'
        "</Property></Property></Property></Data>"
    )
    style = entry(root, "DECALPATH").find("Property[@name='Style']")
    assert len(style) == 1
    assert value(style, "Style") == "Stone"


def test_field_missing_from_vanilla_is_an_error_naming_it():
    with pytest.raises(PatchError, match="PlanetBaseLimitt"):
        merged(
            '<Data template="cGcBaseBuildingTable"><Property name="Objects">'
            '<Property name="Objects" value="GcBaseBuildingEntry" _id="DECALPATH">'
            '<Property name="PlanetBaseLimitt" value="1" />'
            "</Property></Property></Data>"
        )


def test_template_mismatch_is_an_error():
    with pytest.raises(PatchError, match="template"):
        merged('<Data template="cGcSettlementGlobals"><Property name="Scale" value="2" /></Data>')


def test_overwrite_replaces_the_whole_list():
    root, edits = merged(
        '<Data template="cGcBaseBuildingTable"><Property name="Objects">'
        '<Property name="Objects" value="GcBaseBuildingEntry" _id="S_FLOOR_Q">'
        '<Property name="Groups" _overwrite="true">'
        '<Property name="Groups" value="GcBaseBuildingEntryGroup">'
        '<Property name="Group" value="A" /></Property>'
        '<Property name="Groups" value="GcBaseBuildingEntryGroup">'
        '<Property name="Group" value="B" /></Property>'
        "</Property></Property></Property></Data>"
    )
    groups = entry(root, "S_FLOOR_Q").find("Property[@name='Groups']")
    assert [value(g, "Group") for g in groups] == ["A", "B"]
    assert {"path": "Objects[S_FLOOR_Q].Groups", "kind": "overwritten"} in edits


def test_merge_leaves_the_vanilla_tree_untouched():
    vanilla = ET.fromstring(VANILLA)
    before = ET.tostring(vanilla)
    merge_preview.merge(
        vanilla,
        ET.fromstring('<Data template="cGcBaseBuildingTable"><Property name="Scale" value="9" /></Data>'),
    )
    assert ET.tostring(vanilla) == before


def test_vanilla_path_maps_mod_paths_to_extracted_names():
    assert merge_preview.vanilla_relpath(
        Path("METADATA/REALITY/TABLES/BASEBUILDINGOBJECTSTABLE.EXML")
    ) == Path("metadata/reality/tables/basebuildingobjectstable.MXML")
    assert merge_preview.vanilla_relpath(Path("GCBUILDINGGLOBALS.GLOBAL.EXML")) == Path(
        "gcbuildingglobals.global.MXML"
    )


# --- against the real game data and the pinned compiler ----------------------

EXTRACTED = merge_preview.EXTRACTED
needs_game_data = pytest.mark.skipif(
    not (EXTRACTED / "metadata/reality/tables/basebuildingobjectstable.MXML").is_file()
    or not merge_preview.MBIN.is_file(),
    reason="run tools/bootstrap.ps1 and tools/extract.py first",
)


@needs_game_data
def test_a_real_patch_merges_and_compiles(tmp_path):
    module = tmp_path / "Mod"
    patch = module / "GCBUILDINGGLOBALS.GLOBAL.EXML"
    patch.parent.mkdir(parents=True)
    patch.write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n<Data template="cGcBuildingGlobals">\n'
        '  <Property name="RadiusMultiplier_DoNotPlaceAnywhereNear" value="1.000000" />\n</Data>\n'
    )
    results = merge_preview.preview_module(module, tmp_path / "out")
    assert [r.ok for r in results] == [True], [r.message for r in results]
    assert (tmp_path / "out/gcbuildingglobals.global.MBIN").is_file()


@needs_game_data
def test_a_patch_with_a_bad_value_fails_to_compile(tmp_path):
    module = tmp_path / "Mod"
    patch = module / "GCBUILDINGGLOBALS.GLOBAL.EXML"
    patch.parent.mkdir(parents=True)
    patch.write_text(
        '<Data template="cGcBuildingGlobals">'
        '<Property name="RadiusMultiplier_DoNotPlaceAnywhereNear" value="wide" /></Data>'
    )
    results = merge_preview.preview_module(module, tmp_path / "out")
    assert [r.ok for r in results] == [False]
    assert "wide" in results[0].message


def test_globals_folder_maps_to_the_root_level_vanilla_file():
    # Installed globals mods ship under GLOBALS/ while the extracted files sit at the root.
    assert merge_preview.vanilla_relpath(Path("GLOBALS/GCBUILDINGGLOBALS.GLOBAL.EXML")) == Path(
        "gcbuildingglobals.global.MXML"
    )
    assert merge_preview.vanilla_relpath(Path("globals/gcsettlementglobals.EXML")) == Path("gcsettlementglobals.MXML")
