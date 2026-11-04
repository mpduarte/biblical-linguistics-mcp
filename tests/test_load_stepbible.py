"""Tests for matching TAHOT's rows to the OSHB's words."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from load_stepbible import align, letters, meaning_of


def word(text, qere=""):
    return {"text": letters(text), "qere": letters(qere)}


def row(text):
    return {"key": letters(text), "alt": ""}


def test_letters_drop_pointing_and_final_forms():
    assert letters("בְּ/רֵאשִׁ֖ית") == "בראשית"
    assert letters("אֶרֶץ") == letters("ארצ")


def test_align_matches_a_qere_and_skips_an_extra_row():
    words = [word("א"), word("כתיב", "קרי"), word("ג")]
    rows = [row("א"), row("קרי"), row("נוסף"), row("ג")]
    pairs = align(words, rows)
    assert [r["key"] for _, r in pairs] == [letters("א"), letters("קרי"), letters("ג")]


def test_meaning_keeps_the_common_name():
    assert meaning_of("{H7462B=רָעָה=to pasture}") == "to pasture"
    assert meaning_of("{H3068G=יהוה=LORD»LORD@Gen.1.1-Heb}") == "LORD"
