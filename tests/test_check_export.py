import pytest

import check_export

VANILLA = """<Data template="cGcBaseBuildingTable">
  <Property name="Objects">
    <Property name="Objects" value="GcBaseBuildingEntry" _id="DECALPATH">
      <Property name="ID" value="DECALPATH" />
      <Property name="PlanetBaseLimit" value="50" />
      <Property name="Groups" />
    </Property>
  </Property>
</Data>
"""

PATCH = """<Data template="cGcBaseBuildingTable">
  <Property name="Objects">
    <Property name="Objects" value="GcBaseBuildingEntry" _id="DECALPATH">
      <Property name="PlanetBaseLimit" value="250" />
      <Property name="Groups">
        <Property name="Groups" value="GcBaseBuildingEntryGroup">
          <Property name="Group" value="DECORATION" />
        </Property>
      </Property>
    </Property>
    <Property name="Objects" value="GcBaseBuildingEntry" _id="OT_PATH_TILE">
      <Property name="ID" value="OT_PATH_TILE" />
      <Property name="PlanetBaseLimit" value="300" />
    </Property>
  </Property>
</Data>
"""

REL = "METADATA/REALITY/TABLES/BASEBUILDINGOBJECTSTABLE.EXML"


def exported_text(limit="250", with_tile=True, groups=1):
    tile = (
        '<Property name="Objects" value="GcBaseBuildingEntry" _index="1">'
        '<Property name="ID" value="OT_PATH_TILE" /><Property name="PlanetBaseLimit" value="300" /></Property>'
        if with_tile
        else ""
    )
    group = '<Property name="Groups" value="GcBaseBuildingEntryGroup" _index="0"><Property name="Group" value="DECORATION" /></Property>'
    return (
        '<Data template="cGcBaseBuildingTable"><Property name="Objects">'
        '<Property name="Objects" value="GcBaseBuildingEntry" _index="0">'
        f'<Property name="ID" value="DECALPATH" /><Property name="PlanetBaseLimit" value="{limit}" />'
        f'<Property name="Groups">{group * groups}</Property></Property>'
        f"{tile}</Property></Data>"
    )


@pytest.fixture
def tree(tmp_path):
    vanilla = tmp_path / "vanilla/metadata/reality/tables"
    vanilla.mkdir(parents=True)
    (vanilla / "basebuildingobjectstable.MXML").write_text(VANILLA)
    module = tmp_path / "mod/OverseersToolkit" / REL
    module.parent.mkdir(parents=True)
    module.write_text(PATCH)
    return tmp_path


def export(tree, text):
    path = tree / "exported/METADATA/REALITY/TABLES/BASEBUILDINGOBJECTSTABLE.MXML"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return tree / "exported"


def run(tree, exported):
    return check_export.check_module(tree / "mod/OverseersToolkit", exported, tree / "vanilla")


def test_every_edit_found_in_the_export_passes(tree):
    report = run(tree, export(tree, exported_text()))
    assert report.missing == []
    assert report.checked >= 3


def test_a_changed_field_with_the_vanilla_value_is_reported(tree):
    report = run(tree, export(tree, exported_text(limit="50")))
    assert any("DECALPATH" in m and "PlanetBaseLimit" in m for m in report.missing)


def test_an_added_entry_missing_from_the_export_is_reported(tree):
    report = run(tree, export(tree, exported_text(with_tile=False)))
    assert any("OT_PATH_TILE" in m for m in report.missing)


def test_a_list_append_that_did_not_land_is_reported(tree):
    report = run(tree, export(tree, exported_text(groups=0)))
    assert any("Groups" in m for m in report.missing)


def test_entries_are_matched_by_their_id_field_when_the_export_uses_indexes(tree):
    # The export writes _index everywhere; entries must be found by their ID field instead.
    report = run(tree, export(tree, exported_text()))
    assert report.missing == []


def test_a_patched_file_absent_from_the_export_is_reported(tree):
    (tree / "exported").mkdir()
    report = run(tree, tree / "exported")
    assert any("BASEBUILDINGOBJECTSTABLE" in m.upper() for m in report.missing)


def test_a_patch_whose_template_does_not_match_vanilla_is_reported_and_the_rest_still_checked(tree):
    # The game merges a patch with a wrong template anyway, so the check reports it and moves on.
    other = tree / "mod/OverseersToolkit/GCDEBUGOPTIONS.EXML"
    other.write_text('<Data template="cGcSettlementGlobalsOld"><Property name="X" value="1" /></Data>')
    (tree / "vanilla/gcdebugoptions.MXML").write_text('<Data template="cGcSettlementGlobals"><Property name="X" value="0" /></Data>')
    report = run(tree, export(tree, exported_text(limit="50")))
    assert any("GCDEBUGOPTIONS" in m and "cGcSettlementGlobalsOld" in m for m in report.missing)
    assert any("DECALPATH" in m and "PlanetBaseLimit" in m for m in report.missing)


def test_main_keeps_checking_modules_after_one_with_a_bad_patch(tree, monkeypatch, capsys):
    bad = tree / "mod/ABadModule/GCDEBUGOPTIONS.EXML"
    bad.parent.mkdir(parents=True)
    bad.write_text('<Data template="cGcSettlementGlobalsOld" />')
    (tree / "vanilla/gcdebugoptions.MXML").write_text('<Data template="cGcSettlementGlobals" />')
    monkeypatch.setattr(check_export, "REPO", tree)
    check = check_export.check_module
    monkeypatch.setattr(check_export, "check_module", lambda m, e: check(m, e, tree / "vanilla"))
    exported = export(tree, exported_text())
    code = check_export.main([str(exported), "ABadModule", "OverseersToolkit"])
    out = capsys.readouterr().out
    assert code == 1
    assert "MISS ABadModule" in out
    assert "ok   OverseersToolkit" in out
