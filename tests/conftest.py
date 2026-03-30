"""Test fixtures — includes a small test SQLite database with Genesis 1, John 1, Romans 8 data."""

from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path

import pytest
import aiosqlite

from biblical_linguistics_mcp.db.schema import SCHEMA_SQL
from biblical_linguistics_mcp.db import connection as db_conn

FIXTURES_DIR = Path(__file__).parent / "fixtures"
TEST_DB_PATH = FIXTURES_DIR / "test.db"


def _create_test_db() -> None:
    """Create a small test database with sample data."""
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()

    conn = sqlite3.connect(str(TEST_DB_PATH))
    conn.executescript(SCHEMA_SQL)

    # --- Books ---
    books = [
        (1, "Genesis", "OT", 50, "Hebrew"),
        (19, "Psalms", "OT", 150, "Hebrew"),
        (23, "Isaiah", "OT", 66, "Hebrew"),
        (43, "John", "NT", 21, "Greek"),
        (45, "Romans", "NT", 16, "Greek"),
        (62, "1 John", "NT", 5, "Greek"),
    ]
    conn.executemany(
        "INSERT INTO books (book_number, name, testament, chapters, original_language) VALUES (?,?,?,?,?)",
        books,
    )

    # --- Verses ---
    verses = [
        # Genesis 1:1-3
        (1, 1, 1, "בְּרֵאשִׁ֖ית בָּרָ֣א אֱלֹהִ֑ים אֵ֥ת הַשָּׁמַ֖יִם וְאֵ֥ת הָאָֽרֶץ׃",
         "In the beginning God created the heaven and the earth.",
         "In the beginning God created the heavens and the earth.",
         "In the beginning, God created the heavens and the earth."),
        (1, 1, 2, "וְהָאָ֗רֶץ הָיְתָ֥ה תֹ֙הוּ֙ וָבֹ֔הוּ",
         "And the earth was without form, and void; and darkness was upon the face of the deep.",
         "Now the earth was waste and void; and darkness was upon the face of the deep.",
         "The earth was formless and empty. Darkness was on the surface of the deep."),
        (1, 1, 3, "וַיֹּ֥אמֶר אֱלֹהִ֖ים יְהִ֣י א֑וֹר וַֽיְהִי־אֽוֹר׃",
         "And God said, Let there be light: and there was light.",
         "And God said, Let there be light: and there was light.",
         "God said, \"Let there be light,\" and there was light."),
        # John 1:1-3
        (43, 1, 1, "Ἐν ἀρχῇ ἦν ὁ λόγος, καὶ ὁ λόγος ἦν πρὸς τὸν θεόν, καὶ θεὸς ἦν ὁ λόγος.",
         "In the beginning was the Word, and the Word was with God, and the Word was God.",
         "In the beginning was the Word, and the Word was with God, and the Word was God.",
         "In the beginning was the Word, and the Word was with God, and the Word was God."),
        (43, 1, 2, "οὗτος ἦν ἐν ἀρχῇ πρὸς τὸν θεόν.",
         "The same was in the beginning with God.",
         "The same was in the beginning with God.",
         "The same was in the beginning with God."),
        (43, 1, 3, "πάντα δι᾽ αὐτοῦ ἐγένετο, καὶ χωρὶς αὐτοῦ ἐγένετο οὐδὲ ἕν.",
         "All things were made by him; and without him was not any thing made that was made.",
         "All things were made through him; and without him was not anything made that hath been made.",
         "All things were made through him. Without him, nothing was made that has been made."),
        # Romans 8:28-30
        (45, 8, 28, "Οἴδαμεν δὲ ὅτι τοῖς ἀγαπῶσιν τὸν θεὸν πάντα συνεργεῖ εἰς ἀγαθόν",
         "And we know that all things work together for good to them that love God, to them who are the called according to his purpose.",
         "And we know that to them that love God all things work together for good, even to them that are called according to his purpose.",
         "We know that all things work together for good for those who love God, for those who are called according to his purpose."),
        (45, 8, 29, "ὅτι οὓς προέγνω, καὶ προώρισεν",
         "For whom he did foreknow, he also did predestinate to be conformed to the image of his Son, that he might be the firstborn among many brethren.",
         "For whom he foreknew, he also foreordained to be conformed to the image of his Son, that he might be the firstborn among many brethren.",
         "For whom he foreknew, he also predestined to be conformed to the image of his Son, that he might be the firstborn among many brothers."),
        (45, 8, 30, "οὓς δὲ προώρισεν, τούτους καὶ ἐκάλεσεν",
         "Moreover whom he did predestinate, them he also called: and whom he called, them he also justified: and whom he justified, them he also glorified.",
         "and whom he foreordained, them he also called: and whom he called, them he also justified: and whom he justified, them he also glorified.",
         "Whom he predestined, those he also called. Whom he called, those he also justified. Whom he justified, those he also glorified."),
        # 1 John 3:16
        (62, 3, 16, "ἐν τούτῳ ἐγνώκαμεν τὴν ἀγάπην",
         "Hereby perceive we the love of God, because he laid down his life for us: and we ought to lay down our lives for the brethren.",
         "Hereby know we love, because he laid down his life for us: and we ought to lay down our lives for the brethren.",
         "By this we know love, because he laid down his life for us. And we ought to lay down our lives for the brothers."),
    ]
    conn.executemany(
        "INSERT INTO verses (book_number, chapter, verse, text_original, text_kjv, text_asv, text_web) "
        "VALUES (?,?,?,?,?,?,?)",
        verses,
    )

    # --- Lexemes ---
    lexemes = [
        ("H7225", "Hebrew", "רֵאשִׁית", "reshith", "רֵאשִׁית", "beginning, chief", "the first, beginning, best, chief part", 51),
        ("H1254", "Hebrew", "בָּרָא", "bara", "בָּרָא", "to create", "to create, shape, form", 54),
        ("H430", "Hebrew", "אֱלֹהִים", "elohim", "אֱלֹהִים", "God, gods", "God, gods, rulers, judges", 2602),
        ("H853", "Hebrew", "אֵת", "eth", "אֵת", "(sign of accusative)", "sign of the definite direct object", 7374),
        ("H8064", "Hebrew", "שָׁמַיִם", "shamayim", "שָׁמַיִם", "heaven, sky", "heaven, heavens, sky", 421),
        ("H776", "Hebrew", "אֶרֶץ", "erets", "אֶרֶץ", "earth, land", "earth, land, ground, territory", 2504),
        ("G3056", "Greek", "λόγος", "logos", "λόγος", "word, reason", "a word, speech, divine utterance, analogy", 330),
        ("G2316", "Greek", "θεός", "theos", "θεός", "God", "God, a deity, the supreme Divinity", 1318),
        ("G746", "Greek", "ἀρχή", "arche", "ἀρχή", "beginning, ruler", "beginning, origin, first cause", 55),
        ("G25", "Greek", "ἀγαπάω", "agapao", "ἀγαπάω", "to love", "to love, wish well to, take pleasure in", 143),
        ("G4267", "Greek", "προγινώσκω", "proginosko", "προγινώσκω", "to foreknow", "to know beforehand, foreknow", 5),
        ("G4309", "Greek", "προορίζω", "proorizo", "προορίζω", "to predestine", "to predetermine, decide beforehand, foreordain", 6),
    ]
    conn.executemany(
        "INSERT INTO lexemes (strongs, language, word, transliteration, root_form, gloss, definition, frequency) "
        "VALUES (?,?,?,?,?,?,?,?)",
        lexemes,
    )

    # --- Words (morphological entries for Genesis 1:1 and John 1:1) ---
    # Get verse IDs
    gen11_id = conn.execute("SELECT id FROM verses WHERE book_number=1 AND chapter=1 AND verse=1").fetchone()[0]
    jn11_id = conn.execute("SELECT id FROM verses WHERE book_number=43 AND chapter=1 AND verse=1").fetchone()[0]
    rom828_id = conn.execute("SELECT id FROM verses WHERE book_number=45 AND chapter=8 AND verse=28").fetchone()[0]

    gen_words = [
        (gen11_id, 1, "בְּרֵאשִׁ֖ית", "H7225", "HNcfsa", "noun", None, None, None, "Qal", None, "absolute", None, "feminine", "singular", None),
        (gen11_id, 2, "בָּרָ֣א", "H1254", "HVqp3ms", "verb", None, None, None, "Qal", "perfect", None, "3rd", "masculine", "singular", None),
        (gen11_id, 3, "אֱלֹהִ֑ים", "H430", "HNcmpa", "noun", None, None, None, None, None, "absolute", None, "masculine", "plural", None),
        (gen11_id, 4, "אֵ֥ת", "H853", "HTo", "particle", None, None, None, None, None, None, None, None, None, None),
        (gen11_id, 5, "הַשָּׁמַ֖יִם", "H8064", "HNcmpd", "noun", None, None, None, None, None, "determined", None, "masculine", "plural", None),
        (gen11_id, 6, "וְאֵ֥ת", "H853", "HC", "conjunction", None, None, None, None, None, None, None, None, None, None),
        (gen11_id, 7, "הָאָֽרֶץ", "H776", "HNcbsd", "noun", None, None, None, None, None, "determined", None, "both", "singular", None),
    ]

    jn_words = [
        (jn11_id, 1, "Ἐν", None, "PREP", "preposition", None, None, None, None, None, None, None, None, None, None),
        (jn11_id, 2, "ἀρχῇ", "G746", "N-DSF", "noun", None, None, None, None, None, None, None, "feminine", "singular", "dative"),
        (jn11_id, 3, "ἦν", None, "V-IAI-3S", "verb", "imperfect", "active", "indicative", None, None, None, "3rd", None, "singular", None),
        (jn11_id, 4, "ὁ", None, "T-NSM", "article", None, None, None, None, None, None, None, "masculine", "singular", "nominative"),
        (jn11_id, 5, "λόγος", "G3056", "N-NSM", "noun", None, None, None, None, None, None, None, "masculine", "singular", "nominative"),
        (jn11_id, 6, "καὶ", None, "CONJ", "conjunction", None, None, None, None, None, None, None, None, None, None),
        (jn11_id, 7, "ὁ", None, "T-NSM", "article", None, None, None, None, None, None, None, "masculine", "singular", "nominative"),
        (jn11_id, 8, "λόγος", "G3056", "N-NSM", "noun", None, None, None, None, None, None, None, "masculine", "singular", "nominative"),
        (jn11_id, 9, "ἦν", None, "V-IAI-3S", "verb", "imperfect", "active", "indicative", None, None, None, "3rd", None, "singular", None),
        (jn11_id, 10, "πρὸς", None, "PREP", "preposition", None, None, None, None, None, None, None, None, None, None),
        (jn11_id, 11, "τὸν", None, "T-ASM", "article", None, None, None, None, None, None, None, "masculine", "singular", "accusative"),
        (jn11_id, 12, "θεόν", "G2316", "N-ASM", "noun", None, None, None, None, None, None, None, "masculine", "singular", "accusative"),
        (jn11_id, 13, "καὶ", None, "CONJ", "conjunction", None, None, None, None, None, None, None, None, None, None),
        (jn11_id, 14, "θεὸς", "G2316", "N-NSM", "noun", None, None, None, None, None, None, None, "masculine", "singular", "nominative"),
        (jn11_id, 15, "ἦν", None, "V-IAI-3S", "verb", "imperfect", "active", "indicative", None, None, None, "3rd", None, "singular", None),
        (jn11_id, 16, "ὁ", None, "T-NSM", "article", None, None, None, None, None, None, None, "masculine", "singular", "nominative"),
        (jn11_id, 17, "λόγος", "G3056", "N-NSM", "noun", None, None, None, None, None, None, None, "masculine", "singular", "nominative"),
    ]

    rom_words = [
        (rom828_id, 1, "ἀγαπῶσιν", "G25", "V-PAI-3P", "verb", "present", "active", "indicative", None, None, None, "3rd", None, "plural", None),
        (rom828_id, 2, "τὸν", None, "T-ASM", "article", None, None, None, None, None, None, None, "masculine", "singular", "accusative"),
        (rom828_id, 3, "θεὸν", "G2316", "N-ASM", "noun", None, None, None, None, None, None, None, "masculine", "singular", "accusative"),
    ]

    all_words = gen_words + jn_words + rom_words
    conn.executemany(
        "INSERT INTO words (verse_id, word_position, text_original, strongs, morphology_code, "
        "part_of_speech, tense, voice, mood, stem, aspect, state, person, gender, number, case_form) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        all_words,
    )

    # --- Cross-references ---
    crossrefs = [
        (1, 1, 1, 43, 1, 1),   # Gen 1:1 -> John 1:1
        (1, 1, 1, 45, 8, 28),  # Gen 1:1 -> Rom 8:28
        (1, 1, 1, 23, 40, 21), # Gen 1:1 -> Isa 40:21
        (43, 1, 1, 1, 1, 1),   # John 1:1 -> Gen 1:1
        (43, 1, 1, 62, 3, 16), # John 1:1 -> 1 John 3:16
        (45, 8, 28, 1, 1, 1),  # Rom 8:28 -> Gen 1:1
    ]
    conn.executemany(
        "INSERT INTO cross_references (source_book, source_chapter, source_verse, "
        "target_book, target_chapter, target_verse, source) VALUES (?,?,?,?,?,?, 'TSK')",
        crossrefs,
    )

    # --- Topics ---
    conn.execute("INSERT INTO topics (id, topic, subtopic) VALUES (1, 'Creation', 'God as Creator')")
    conn.execute("INSERT INTO topics (id, topic, subtopic) VALUES (2, 'Love', 'God''s Love')")
    conn.execute("INSERT INTO topics (id, topic, subtopic) VALUES (3, 'Predestination', 'Election')")
    conn.execute("INSERT INTO topics (id, topic, subtopic) VALUES (4, 'Word of God', 'Logos')")

    topic_verses = [
        (1, 1, 1, 1),   # Creation: Gen 1:1
        (1, 43, 1, 3),  # Creation: John 1:3
        (2, 45, 8, 28), # Love: Rom 8:28
        (2, 62, 3, 16), # Love: 1 John 3:16
        (3, 45, 8, 29), # Predestination: Rom 8:29
        (3, 45, 8, 30), # Predestination: Rom 8:30
        (4, 43, 1, 1),  # Word of God: John 1:1
    ]
    conn.executemany(
        "INSERT INTO topic_verses (topic_id, book_number, chapter, verse) VALUES (?,?,?,?)",
        topic_verses,
    )

    # --- LXX Alignments (sample) ---
    lxx_alignments = [
        (1, 1, 1, "בְּרֵאשִׁית", "H7225", "ἀρχή", "G746", "N-DSF"),
        (1, 1, 1, "בָּרָא", "H1254", "ἐποίησεν", "G4160", "V-AAI-3S"),
        (1, 1, 1, "אֱלֹהִים", "H430", "θεός", "G2316", "N-NSM"),
        (1, 1, 1, "שָׁמַיִם", "H8064", "οὐρανόν", "G3772", "N-ASM"),
        (1, 1, 1, "אֶרֶץ", "H776", "γῆν", "G1093", "N-ASF"),
    ]
    conn.executemany(
        "INSERT INTO lxx_alignments (hebrew_book, hebrew_chapter, hebrew_verse, "
        "hebrew_word, hebrew_strongs, lxx_word, lxx_strongs, lxx_morphology) "
        "VALUES (?,?,?,?,?,?,?,?)",
        lxx_alignments,
    )

    conn.commit()
    conn.close()


# Create the test DB once at module import time
_create_test_db()


@pytest.fixture(autouse=True)
def use_test_db(monkeypatch):
    """Point all DB access to the test database."""
    db_conn.set_db_path(TEST_DB_PATH)
    yield
    db_conn._db_path = None
