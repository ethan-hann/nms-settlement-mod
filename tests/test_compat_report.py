import os
import re

import pytest

import compat_report as cr

# --- synthetic vanilla and module trees --------------------------------------

VANILLA_OBJECTS = """<?xml version="1.0" encoding="utf-8"?>
<Data template="cGcBaseBuildingTable">
  <Property name="Objects">
    <Property name="Objects" value="GcBaseBuildingEntry" _id="DECALPATH">
      <Property name="ID" value="DECALPATH" />
      <Property name="PlanetBaseLimit" value="50" />
      <Property name="Groups" />
    </Property>
    <Property name="Objects" value="GcBaseBuildingEntry" _id="S_FLOOR_Q">
      <Property name="ID" value="S_FLOOR_Q" />
      <Property name="PlanetBaseLimit" value="0" />
      <Property name="Groups">
        <Property name="Groups" value="GcBaseBuildingEntryGroup" _index="0">
          <Property name="Group" value="BASIC_S" />
        </Property>
      </Property>
    </Property>
  </Property>
</Data>
"""

VANILLA_GLOBALS = """<?xml version="1.0" encoding="utf-8"?>
<Data template="cGcBuildingGlobals">
  <Property name="RadiusMultiplier_DoNotPlaceAnywhereNear" value="2.500000" />
  <Property name="Radius_DoNotPlaceAnywhereNear" value="200" />
</Data>
"""

OBJECTS_REL = "METADATA/REALITY/TABLES/BASEBUILDINGOBJECTSTABLE.EXML"
GLOBALS_REL = "GCBUILDINGGLOBALS.GLOBAL.EXML"

# What the game's paks contain, lower case with .mbin, as in scratch/all_files.txt.
GAME_FILES = {
    "metadata/reality/tables/basebuildingobjectstable.mbin",
    "gcbuildingglobals.global.mbin",
}

GAME_PROCESS = f"OTC{os.getpid()}.exe"


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8") if isinstance(text, str) else text)


def entry(id_, body):
    return f'<Property name="Objects" value="GcBaseBuildingEntry" _id="{id_}">{body}</Property>'


def field(name, value):
    return f'<Property name="{name}" value="{value}" />'


def group_append(group):
    return (
        '<Property name="Groups"><Property name="Groups" value="GcBaseBuildingEntryGroup">'
        f'<Property name="Group" value="{group}" /></Property></Property>'
    )


def objects_patch(*entries, extra=""):
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n<Data template="cGcBaseBuildingTable">'
        f'{extra}<Property name="Objects">{"".join(entries)}</Property></Data>\n'
    )


def globals_patch(multiplier):
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n<Data template="cGcBuildingGlobals">'
        f'{field("RadiusMultiplier_DoNotPlaceAnywhereNear", multiplier)}</Data>\n'
    )


@pytest.fixture
def vanilla(tmp_path):
    root = tmp_path / "vanilla"
    write(root / "metadata/reality/tables/basebuildingobjectstable.MXML", VANILLA_OBJECTS)
    write(root / "gcbuildingglobals.global.MXML", VANILLA_GLOBALS)
    return root


@pytest.fixture
def mod_root(tmp_path):
    """Our modules: a shipped one that edits and adds, and the test-only Probes module."""
    root = tmp_path / "repo/mod"
    shipped = root / "OverseersToolkit"
    write(
        shipped / OBJECTS_REL,
        objects_patch(
            entry("DECALPATH", field("PlanetBaseLimit", "200") + group_append("OT_SETTLEMENT")),
            entry("OT_PATH_TILE", field("ID", "OT_PATH_TILE") + field("PlanetBaseLimit", "300")),
        ),
    )
    write(shipped / GLOBALS_REL, globals_patch("1.000000"))
    write(
        root / "OverseersToolkit-Probes" / OBJECTS_REL,
        objects_patch(entry("S_FLOOR_Q", field("PlanetBaseLimit", "9"))),
    )
    return root


@pytest.fixture
def mods(tmp_path):
    """An empty stand-in for GAMEDATA/MODS with a Vortex file at its root."""
    root = tmp_path / "game/GAMEDATA/MODS"
    write(root / "vortex.deployment.json", "{}")
    return root


def generate(mod_root, vanilla, **kw):
    return cr.generate_compatibility(mod_root, vanilla, **kw)


def scan(mods, mod_root, vanilla, **kw):
    return cr.scan_mods(mods, mod_root, vanilla, game_files=GAME_FILES, **kw)


def snapshot(root):
    """Names, bytes and modification times of everything under root."""
    snap = {}
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root).as_posix()
        snap[rel] = None if p.is_dir() else (p.read_bytes(), p.stat().st_mtime_ns)
    return snap


def section(text, heading):
    """Lines under a Markdown heading, up to the next heading of the same or a higher level."""
    level = len(heading) - len(heading.lstrip("#"))
    lines = text.splitlines()
    start = lines.index(heading) + 1
    out = []
    for line in lines[start:]:
        m = re.match(r"(#+) ", line)
        if m and len(m.group(1)) <= level:
            break
        out.append(line)
    return "\n".join(out)


def of_kind(findings, kind):
    return [f for f in findings if f.kind == kind]


# --- COMPATIBILITY.md --------------------------------------------------------


def test_header_says_the_file_is_generated_and_by_which_command(mod_root, vanilla):
    head = "\n".join(generate(mod_root, vanilla).splitlines()[:5])
    assert "Generated" in head
    assert "tools/compat_report.py" in head


def test_changed_field_row_has_vanilla_and_our_value(mod_root, vanilla):
    edits = section(generate(mod_root, vanilla), "### Edits vanilla")
    assert re.search(r"\| Objects\[DECALPATH\]\.PlanetBaseLimit \| 50 \| 200 \|", edits)


def test_changed_global_field_is_listed_under_its_own_file(mod_root, vanilla):
    edits = section(generate(mod_root, vanilla), "### Edits vanilla")
    assert GLOBALS_REL in edits
    assert re.search(r"\| RadiusMultiplier_DoNotPlaceAnywhereNear \| 2.500000 \| 1.000000 \|", edits)


def test_list_appended_on_a_vanilla_entry_is_listed(mod_root, vanilla):
    edits = section(generate(mod_root, vanilla), "### Edits vanilla")
    assert "Objects[DECALPATH].Groups" in edits
    assert "OT_SETTLEMENT" not in edits  # the list is named, not its content


def test_new_entries_are_listed_apart_from_vanilla_edits(mod_root, vanilla):
    text = generate(mod_root, vanilla)
    edits = section(text, "### Edits vanilla")
    adds = section(text, "### Adds new")
    assert "OT_PATH_TILE" in adds
    assert "OT_PATH_TILE" not in edits
    assert "PlanetBaseLimit" not in adds
    assert text.index("### Edits vanilla") < text.index("### Adds new")


def test_module_without_vanilla_edits_says_so(mod_root, vanilla):
    write(mod_root / "OverseersToolkit-Extra" / OBJECTS_REL, objects_patch(entry("OT_EXTRA", field("ID", "OT_EXTRA"))))
    text = generate(mod_root, vanilla)
    extra = section(text, "## OverseersToolkit-Extra")
    assert "does not edit vanilla" in section(extra, "### Edits vanilla").lower()
    assert "OT_EXTRA" in section(extra, "### Adds new")


def test_full_mxml_files_have_no_vanilla_counterpart_and_count_as_new(mod_root, vanilla):
    write(mod_root / "OverseersToolkit-Text/LocTable.MXML", '<Data template="cTkLocalisationTable" />')
    text = generate(mod_root, vanilla)
    assert "LocTable.MXML" in section(section(text, "## OverseersToolkit-Text"), "### Adds new")


def test_test_only_modules_are_left_out_by_an_explicit_constant(mod_root, vanilla):
    assert {"OverseersToolkit-Probes", "OverseersToolkit-TestTuning"} <= set(cr.EXCLUDED_MODULES)
    text = generate(mod_root, vanilla)
    assert "Probes" not in text
    assert "S_FLOOR_Q" not in text


def test_test_modules_can_be_included_on_request(mod_root, vanilla):
    assert "## OverseersToolkit-Probes" in generate(mod_root, vanilla, include_test_modules=True)


def test_with_no_shipped_modules_the_file_says_so(tmp_path, vanilla):
    root = tmp_path / "mod"
    write(root / "OverseersToolkit-Probes" / OBJECTS_REL, objects_patch(entry("S_FLOOR_Q", field("PlanetBaseLimit", "9"))))
    assert "no shipped modules yet" in generate(root, vanilla).lower()


def test_output_is_sorted_stable_and_ascii(tmp_path, vanilla):
    root = tmp_path / "mod"
    for name in ("Zeta", "Alpha"):  # created out of order on purpose
        write(root / name / OBJECTS_REL, objects_patch(entry("DECALPATH", field("PlanetBaseLimit", "7"))))
    first = generate(root, vanilla)
    assert first == generate(root, vanilla)
    assert first.isascii()
    assert first.index("## Alpha") < first.index("## Zeta")


def test_a_patch_that_does_not_merge_fails_the_report(mod_root, vanilla):
    write(mod_root / "OverseersToolkit" / OBJECTS_REL, objects_patch(entry("DECALPATH", field("PlanetBaseLimitt", "1"))))
    with pytest.raises(cr.CompatError, match="PlanetBaseLimitt"):
        generate(mod_root, vanilla)


# --- scanning an installed MODS folder ---------------------------------------


def test_same_field_changed_is_a_conflict_showing_both_values(mods, mod_root, vanilla):
    write(mods / "Other Mod" / OBJECTS_REL, objects_patch(entry("DECALPATH", field("PlanetBaseLimit", "75"))))
    (conflict,) = of_kind(scan(mods, mod_root, vanilla), "conflict")
    assert conflict.mod == "Other Mod"
    assert "Objects[DECALPATH].PlanetBaseLimit" in conflict.message
    assert "200" in conflict.message and "75" in conflict.message
    assert "50" in conflict.message  # vanilla


def test_a_value_equal_to_vanilla_is_not_a_change(mods, mod_root, vanilla):
    # Full-file mods repeat every vanilla value; only real changes can conflict.
    write(mods / "Full Copy" / OBJECTS_REL, objects_patch(entry("DECALPATH", field("PlanetBaseLimit", "50"))))
    assert of_kind(scan(mods, mod_root, vanilla), "conflict") == []


def test_game_paths_match_regardless_of_case(mods, mod_root, vanilla):
    write(
        mods / "Lower Case" / "metadata/reality/tables/basebuildingobjectstable.exml",
        objects_patch(entry("DECALPATH", field("PlanetBaseLimit", "75"))),
    )
    assert len(of_kind(scan(mods, mod_root, vanilla), "conflict")) == 1


def test_same_id_appended_by_both_is_a_conflict(mods, mod_root, vanilla):
    write(mods / "Clone" / OBJECTS_REL, objects_patch(entry("OT_PATH_TILE", field("ID", "OT_PATH_TILE"))))
    (conflict,) = of_kind(scan(mods, mod_root, vanilla), "conflict")
    assert "OT_PATH_TILE" in conflict.message


def test_appending_to_the_same_vanilla_list_is_a_note_not_a_conflict(mods, mod_root, vanilla):
    write(mods / "Grouper" / OBJECTS_REL, objects_patch(entry("DECALPATH", group_append("THEIRS"))))
    findings = scan(mods, mod_root, vanilla)
    assert of_kind(findings, "conflict") == []
    (note,) = of_kind(findings, "note")
    assert note.mod == "Grouper"
    assert "Objects[DECALPATH].Groups" in note.message


def test_a_mod_in_the_same_file_with_no_shared_field_is_listed_as_sharing_it(mods, mod_root, vanilla):
    write(mods / "Neighbor" / OBJECTS_REL, objects_patch(entry("S_FLOOR_Q", field("PlanetBaseLimit", "5"))))
    findings = scan(mods, mod_root, vanilla)
    assert of_kind(findings, "conflict") == []
    (shared,) = of_kind(findings, "shared-file")
    assert shared.mod == "Neighbor"


def test_an_mbin_at_a_patched_path_replaces_the_whole_file(mods, mod_root, vanilla):
    write(mods / "Binary Mod/METADATA/REALITY/TABLES/BASEBUILDINGOBJECTSTABLE.MBIN", b"\x00\x01")
    (conflict,) = of_kind(scan(mods, mod_root, vanilla), "conflict")
    assert conflict.mod == "Binary Mod"
    assert "whole file" in conflict.message.lower()


def test_an_mbin_at_a_path_we_do_not_patch_is_ignored(mods, mod_root, vanilla):
    write(mods / "Other Binary/METADATA/REALITY/TABLES/SOMETHINGELSE.MBIN", b"\x00\x01")
    assert scan(mods, mod_root, vanilla) == []


def test_a_patch_under_globals_is_flagged_as_possibly_not_loading(mods, mod_root, vanilla):
    write(mods / "gBase-like/GLOBALS/GCBUILDINGGLOBALS.GLOBAL.EXML", globals_patch("0.5"))
    findings = scan(mods, mod_root, vanilla)
    (flag,) = of_kind(findings, "may-not-load")
    assert flag.mod == "gBase-like"
    assert "GLOBALS/GCBUILDINGGLOBALS.GLOBAL.EXML" in flag.file
    assert of_kind(findings, "conflict") == []  # a different path, so not our file


def test_the_same_globals_patch_at_the_pak_root_does_conflict(mods, mod_root, vanilla):
    write(mods / "Rooted" / GLOBALS_REL, globals_patch("0.5"))
    (conflict,) = of_kind(scan(mods, mod_root, vanilla), "conflict")
    assert "RadiusMultiplier_DoNotPlaceAnywhereNear" in conflict.message
    assert "1.000000" in conflict.message and "0.5" in conflict.message


def test_a_new_mxml_file_is_not_flagged_as_misplaced(mods, mod_root, vanilla):
    write(mods / "Texty/LocTable.MXML", '<Data template="cTkLocalisationTable" />')
    assert scan(mods, mod_root, vanilla) == []


def test_an_unparseable_exml_is_reported_and_the_scan_continues(mods, mod_root, vanilla):
    write(mods / "A Broken" / OBJECTS_REL, "<Data template=")
    write(mods / "B Working" / OBJECTS_REL, objects_patch(entry("DECALPATH", field("PlanetBaseLimit", "75"))))
    findings = scan(mods, mod_root, vanilla)
    (bad,) = of_kind(findings, "unreadable")
    assert bad.mod == "A Broken"
    assert [f.mod for f in of_kind(findings, "conflict")] == ["B Working"]


def test_a_patch_that_does_not_fit_vanilla_is_reported_not_fatal(mods, mod_root, vanilla):
    write(mods / "Old Build" / OBJECTS_REL, objects_patch(entry("DECALPATH", field("RenamedField", "1"))))
    (bad,) = of_kind(scan(mods, mod_root, vanilla), "unreadable")
    assert "RenamedField" in bad.message


def test_amumss_annotations_and_comments_are_tolerated(mods, mod_root, vanilla):
    annotated = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<Data template="cGcBaseBuildingTable">\n'
        "  !# CHANGED\n"
        "  <!-- tuned by the author -->\n"
        '  <Property name="Objects">\n'
        "    !# CHANGED\n"
        f'    {entry("DECALPATH", field("PlanetBaseLimit", "75"))}\n'
        "  </Property>\n</Data>\n"
    )
    write(mods / "Annotated" / OBJECTS_REL, annotated)
    assert len(of_kind(scan(mods, mod_root, vanilla), "conflict")) == 1


def test_our_own_dev_folders_are_not_scanned(mods, mod_root, vanilla):
    write(mods / "_OTDEV_core" / OBJECTS_REL, objects_patch(entry("DECALPATH", field("PlanetBaseLimit", "200"))))
    assert scan(mods, mod_root, vanilla) == []


def test_files_at_the_root_of_mods_are_not_mods(mods, mod_root, vanilla):
    write(mods / "Notes.EXML", "not xml")
    assert scan(mods, mod_root, vanilla) == []


def test_test_modules_only_take_part_when_asked(mods, mod_root, vanilla):
    write(mods / "Floors" / OBJECTS_REL, objects_patch(entry("S_FLOOR_Q", field("PlanetBaseLimit", "5"))))
    assert of_kind(scan(mods, mod_root, vanilla), "conflict") == []
    assert len(of_kind(scan(mods, mod_root, vanilla, include_test_modules=True), "conflict")) == 1


def test_findings_are_sorted_by_mod_then_file(mods, mod_root, vanilla):
    for name in ("Zed", "Amy"):
        write(mods / name / OBJECTS_REL, objects_patch(entry("DECALPATH", field("PlanetBaseLimit", "75"))))
    assert [f.mod for f in scan(mods, mod_root, vanilla)] == ["Amy", "Zed"]


def test_scanning_leaves_the_scanned_tree_byte_for_byte_unchanged(mods, mod_root, vanilla):
    write(mods / "Other Mod" / OBJECTS_REL, objects_patch(entry("DECALPATH", field("PlanetBaseLimit", "75"))))
    write(mods / "Binary Mod/METADATA/REALITY/TABLES/BASEBUILDINGOBJECTSTABLE.MBIN", b"\x00\x01")
    write(mods / "A Broken" / OBJECTS_REL, "<Data template=")
    write(mods / "gBase-like/GLOBALS/GCBUILDINGGLOBALS.GLOBAL.EXML", globals_patch("0.5"))
    before = snapshot(mods)
    findings = scan(mods, mod_root, vanilla)
    assert findings  # the scan did real work
    assert snapshot(mods) == before


def test_rendered_scan_is_ascii_even_for_odd_mod_names(mods, mod_root, vanilla):
    write(mods / "Caf\u00e9 Mod" / OBJECTS_REL, objects_patch(entry("DECALPATH", field("PlanetBaseLimit", "75"))))
    text = cr.render_scan(scan(mods, mod_root, vanilla))
    assert text.isascii()
    assert "Caf" in text


def test_rendered_scan_with_no_findings_says_so(mods, mod_root, vanilla):
    assert "no overlap" in cr.render_scan(scan(mods, mod_root, vanilla)).lower()


def test_table_cells_escape_pipes(mod_root, vanilla):
    write(mod_root / "OverseersToolkit" / OBJECTS_REL, objects_patch(entry("DECALPATH", field("PlanetBaseLimit", "a|b"))))
    assert "a\\|b" in generate(mod_root, vanilla)


# --- command line ------------------------------------------------------------


def args(tmp_path, mods, mod_root, vanilla, *more):
    game_files = tmp_path / "all_files.txt"
    write(game_files, "Listing X:\\game\\fake.pak\n" + "\n".join(sorted(GAME_FILES)) + "\n")
    return [
        "--mods", str(mods),
        "--mod-root", str(mod_root),
        "--vanilla", str(vanilla),
        "--game-files", str(game_files),
        "--compat-file", str(tmp_path / "COMPATIBILITY.md"),
        *more,
    ]  # fmt: skip


def test_the_game_file_list_loader_skips_listing_headers(tmp_path):
    path = tmp_path / "all_files.txt"
    write(path, "Listing X:\\a.pak\nGCBuildingGlobals.global.mbin\n\nmodels/x.scene.mbin\n")
    assert cr.load_game_files(path) == {"gcbuildingglobals.global.mbin", "models/x.scene.mbin"}


def test_no_arguments_regenerates_the_compatibility_file(tmp_path, mod_root, vanilla):
    compat = tmp_path / "COMPATIBILITY.md"
    rc = cr.main(["--mod-root", str(mod_root), "--vanilla", str(vanilla), "--compat-file", str(compat)])
    assert rc == 0
    assert compat.read_text(encoding="utf-8") == generate(mod_root, vanilla)


def test_scan_output_goes_to_out_and_never_into_the_compatibility_file(tmp_path, mods, mod_root, vanilla):
    write(mods / "Other Mod" / OBJECTS_REL, objects_patch(entry("DECALPATH", field("PlanetBaseLimit", "75"))))
    out = tmp_path / "scan.txt"
    rc = cr.main(args(tmp_path, mods, mod_root, vanilla, "--out", str(out)), process_name=GAME_PROCESS)
    assert rc == 0
    assert "Other Mod" in out.read_text(encoding="utf-8")
    assert not (tmp_path / "COMPATIBILITY.md").exists()


def test_scan_prints_to_stdout_without_out(tmp_path, mods, mod_root, vanilla, capsys):
    write(mods / "Other Mod" / OBJECTS_REL, objects_patch(entry("DECALPATH", field("PlanetBaseLimit", "75"))))
    assert cr.main(args(tmp_path, mods, mod_root, vanilla), process_name=GAME_PROCESS) == 0
    assert "Other Mod" in capsys.readouterr().out


def test_scan_refuses_while_the_game_runs(tmp_path, mods, mod_root, vanilla, fake_process, capsys):
    fake_process(GAME_PROCESS)
    write(mods / "Other Mod" / OBJECTS_REL, objects_patch(entry("DECALPATH", field("PlanetBaseLimit", "75"))))
    before = snapshot(mods)
    out = tmp_path / "scan.txt"
    rc = cr.main(args(tmp_path, mods, mod_root, vanilla, "--out", str(out)), process_name=GAME_PROCESS)
    assert rc != 0
    assert GAME_PROCESS in capsys.readouterr().err
    assert not out.exists()
    assert snapshot(mods) == before


def test_regenerating_needs_no_running_check(tmp_path, mod_root, vanilla, fake_process):
    # Only a scan touches the game folder, so generating the file works with the game up.
    fake_process(GAME_PROCESS)
    compat = tmp_path / "COMPATIBILITY.md"
    rc = cr.main(
        ["--mod-root", str(mod_root), "--vanilla", str(vanilla), "--compat-file", str(compat)],
        process_name=GAME_PROCESS,
    )
    assert rc == 0
    assert compat.is_file()
