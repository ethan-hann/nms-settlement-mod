"""Shipped modules carry their text in every game language; test-only modules may stay English."""

import json
from pathlib import Path

import pytest

import gen_parts
import package

SPECS = Path(__file__).resolve().parent.parent / "specs"
SHIPPED_SPECS = [m for m in package.SHIPPED if (SPECS / f"{m}.json").is_file()]


def text_of(module):
    return json.loads((SPECS / f"{module}.json").read_text(encoding="utf-8")).get("text", {})


@pytest.mark.parametrize("module", SHIPPED_SPECS)
def test_shipped_text_lists_every_language(module):
    # A plain string would put English in every column with nothing marking it as pending.
    plain = sorted(key for key, text in text_of(module).items() if isinstance(text, str))
    assert not plain, f"{module}: give these keys every language, or null while pending: {plain}"


@pytest.mark.parametrize("module", SHIPPED_SPECS)
def test_shipped_text_is_valid(module):
    for key, text in text_of(module).items():
        gen_parts.loc_columns(key, text)


@pytest.mark.parametrize("module", SHIPPED_SPECS)
def test_part_names_are_their_menu_names_in_capitals(module):
    # Vanilla pairs every _NAME with a _NAME_L that is the same name in normal case, in every language.
    text = text_of(module)
    for key in [k for k in text if k.endswith("_NAME") and f"{k}_L" in text]:
        upper, normal = gen_parts.loc_columns(key, text[key]), gen_parts.loc_columns(f"{key}_L", text[f"{key}_L"])
        for lang, value in upper.items():
            assert value == normal[lang].upper(), f"{key} {lang}: {value!r} vs {normal[lang]!r}"
