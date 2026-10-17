"""Show how the game itself words a term in every language, from scratch/extracted/language.

Translations of the mod's text reuse these words, so a settlement, debt or Sentinel reads
the same in the mod as everywhere else in that language.

Usage: loc_glossary.py <term> [<term> ...] [--limit N]
"""

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from gen_parts import EXTRACTED, LOC_LANGUAGES

_BY_SUFFIX = {lang.lower(): lang for lang in LOC_LANGUAGES}


def vanilla_text(extracted=EXTRACTED):
    """Return {key: {language: text}}; each vanilla language file fills only its own column."""
    text = {}
    for path in sorted((Path(extracted) / "language").glob("nms_*.MXML")):
        lang = _BY_SUFFIX.get(path.stem.rsplit("_", 1)[-1].lower())
        # USEnglish only respells English, so it says nothing about a term.
        if lang in (None, "USEnglish"):
            continue
        for entry in ET.parse(path).getroot().iter("Property"):
            if entry.get("value") != "TkLocalisationEntry":
                continue
            key = entry.find("Property[@name='Id']").get("value")
            column = entry.find(f"Property[@name='{lang}']")
            if column is not None and column.get("value"):
                text.setdefault(key, {})[lang] = column.get("value")
    return text


def lookup(text, term):
    """Entries whose English holds term as a whole word, shortest first."""
    pattern = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
    found = [(key, langs) for key, langs in text.items() if pattern.search(langs.get("English", ""))]
    return sorted(found, key=lambda item: (len(item[1]["English"]), item[0]))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("terms", nargs="+")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args(argv)
    text = vanilla_text()
    if not text:
        print(f"No language files in {EXTRACTED / 'language'}; run tools/extract.py first.", file=sys.stderr)
        return 2
    sys.stdout.reconfigure(encoding="utf-8")
    for term in args.terms:
        for key, langs in lookup(text, term)[: args.limit]:
            print(f"== {term}: {key}")
            for lang in LOC_LANGUAGES:
                if lang in langs:
                    print(f"  {lang}: {langs[lang]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
