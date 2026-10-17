import loc_glossary

ENTRY = """\t\t<Property name="Table" value="TkLocalisationEntry" _id="{key}">
\t\t\t<Property name="Id" value="{key}" />
\t\t\t<Property name="English" value="{english}" />
\t\t\t<Property name="French" value="{french}" />
\t\t</Property>
"""


def language_file(path, entries):
    body = "".join(ENTRY.format(key=k, english=e, french=f) for k, e, f in entries)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f'<Data template="cTkLocalisationTable">\n\t<Property name="Table">\n{body}\t</Property>\n</Data>\n',
        encoding="utf-8",
    )


def test_each_language_comes_from_its_own_file(tmp_path):
    # A vanilla language file fills only its own column; the others are empty.
    language_file(tmp_path / "language/nms_loc1_english.MXML", [("UI_DEBT", "Debt", "")])
    language_file(tmp_path / "language/nms_loc1_french.MXML", [("UI_DEBT", "", "Dette")])
    language_file(tmp_path / "language/nms_loc4_french.MXML", [("UI_TAX", "", "Taxe")])
    text = loc_glossary.vanilla_text(tmp_path)
    assert text == {"UI_DEBT": {"English": "Debt", "French": "Dette"}, "UI_TAX": {"French": "Taxe"}}


def test_us_english_files_are_not_read_as_english(tmp_path):
    path = tmp_path / "language/nms_loc1_usenglish.MXML"
    language_file(path, [("UI_COLOUR", "", "")])
    path.write_text(path.read_text(encoding="utf-8").replace('name="English" value=""', 'name="USEnglish" value="Color"'))
    assert loc_glossary.vanilla_text(tmp_path) == {}


def test_lookup_matches_whole_words_in_the_english(tmp_path):
    text = {
        "A": {"English": "Settlement Debt", "French": "Dette de la colonie"},
        "B": {"English": "Debtor", "French": "Debiteur"},
        "C": {"English": "debt", "French": "dette"},
    }
    assert [key for key, _ in loc_glossary.lookup(text, "debt")] == ["C", "A"]
