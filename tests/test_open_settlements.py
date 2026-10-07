"""OpenSettlements: let a base computer be claimed inside a settlement."""

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

import merge_preview

MODULE = Path(__file__).resolve().parent.parent / "mod" / "OverseersToolkit-OpenSettlements"
PATCH = MODULE / "GLOBALS" / "GCBUILDINGGLOBALS.GLOBAL.EXML"
VANILLA = merge_preview.EXTRACTED / "gcbuildingglobals.global.MXML"

# Session 1: "Within Existing Base" cleared about 312u from a settlement marker, matching
# the vanilla MinRadiusForBases of 300; settlement hubs are well under 100u across.
OBSERVED_EXCLUSION = 312.0


@pytest.fixture(scope="module")
def edits():
    if not VANILLA.is_file():
        pytest.skip("run tools/extract.py first")
    _, records = merge_preview.merge(ET.parse(VANILLA).getroot(), ET.parse(PATCH).getroot())
    return {r["path"]: r for r in records}


def test_the_module_changes_only_the_minimum_base_radius(edits):
    assert set(edits) == {"MinRadiusForBases"}


def test_the_minimum_base_radius_fits_inside_a_settlement(edits):
    new = float(edits["MinRadiusForBases"]["new"])
    old = float(edits["MinRadiusForBases"]["old"])
    assert old == 300.0
    assert 0 < new <= 30, "small enough to claim between settlement buildings"
    assert new < OBSERVED_EXCLUSION
