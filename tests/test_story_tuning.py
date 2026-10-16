"""StoryTuning is test-only: decisions come quickly and are nearly always a non-Request Settler Stories dilemma."""

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

import merge_preview

REPO = Path(__file__).resolve().parent.parent
MODULE = REPO / "mod" / "OverseersToolkit-StoryTuning"
GLOBALS = MODULE / "GLOBALS" / "GCSETTLEMENTGLOBALS.EXML"
STORIES = REPO / "specs" / "OverseersToolkit-SettlerStories.json"
VANILLA = merge_preview.EXTRACTED / "gcsettlementglobals.MXML"
TUNED_TYPES = {"StrangerVisit", "Policy", "Conflict"}

pytestmark = pytest.mark.skipif(not VANILLA.is_file(), reason="run tools/extract.py first")


def tuning():
    if not GLOBALS.is_file():
        pytest.fail(f"{GLOBALS.relative_to(REPO)} is missing")
    return ET.parse(GLOBALS).getroot()


def value(node, name):
    return node.find(f"Property[@name='{name}']").get("value")


def judgement_type(j):
    return j.find("Property[@name='JudgementType']/Property[@name='SettlementJudgementType']").get("value")


def vanilla_pool():
    return ET.parse(VANILLA).getroot().find("Property[@name='Judgements']")


def test_decisions_arrive_within_a_couple_of_minutes():
    root = tuning()
    low, high = int(value(root, "JudgementWaitTimeMin")), int(value(root, "JudgementWaitTimeMax"))
    assert 0 < low <= high <= 180


def test_only_the_three_tuned_types_can_be_drawn_among_the_heavy_types():
    weights = {c.get("name"): float(c.get("value")) for c in tuning().find("Property[@name='JudgementSelectionWeights']")}
    assert weights["Request"] == 0 and weights["BuildingChoice"] == 0
    assert all(weights[t] >= 50 for t in TUNED_TYPES)


def test_every_vanilla_judgement_of_the_tuned_types_is_zeroed_and_nothing_else():
    tuned = {int(j.get("_index")): j for j in tuning().find("Property[@name='Judgements']")}
    expected = {i for i, j in enumerate(vanilla_pool()) if judgement_type(j) in TUNED_TYPES}
    assert set(tuned) == expected
    for j in tuned.values():
        assert [(c.get("name"), c.get("value")) for c in j] == [("Weighting", "0.000000")]


def test_nearly_every_draw_is_a_settler_stories_dilemma():
    # Type is drawn by JudgementSelectionWeights, then a judgement of that type by Weighting.
    vanilla_weights = {
        c.get("name"): float(c.get("value"))
        for c in ET.parse(VANILLA).getroot().find("Property[@name='JudgementSelectionWeights']")
    }
    vanilla_weights.update(
        {c.get("name"): float(c.get("value")) for c in tuning().find("Property[@name='JudgementSelectionWeights']")}
    )
    stories = json.loads(STORIES.read_text(encoding="utf-8"))["judgements"]
    drawable = {t for t in vanilla_weights if any(judgement_type(j) == t for j in vanilla_pool())}
    total = sum(vanilla_weights[t] for t in drawable)
    chance = sum(vanilla_weights[t] / total for t in TUNED_TYPES if any(s["type"] == t for s in stories))
    assert chance >= 0.9, f"Settler Stories dilemmas are {chance:.0%} of draws"
