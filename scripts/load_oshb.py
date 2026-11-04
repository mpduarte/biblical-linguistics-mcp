#!/usr/bin/env python3
"""Load the Open Scriptures Hebrew Bible into the database.

Replaces every Old Testament row of `words` with one row per word of the
Westminster Leningrad Codex, with its morphology, and fills
`verses.text_original`. Verses stay in the KJV's numbering, which the rest of
the database uses: OSHB's VerseMap.xml gives the moves, and each word keeps its
own WLC verse in `wlc_ref`.

Writes data/biblical_linguistics.local.db (or BIBLICAL_LINGUISTICS_DB), starting
from a copy of the tracked database, which stays as upstream ships it. Reads
data/raw/oshb/*.xml, fetched at PINNED_COMMIT if missing. Safe to re-run.
The morphology is CC BY 4.0 (openscriptures/morphhb); the WLC is public domain.
"""

from __future__ import annotations

import os
import re
import shutil
import sqlite3
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from biblical_linguistics_mcp.morphology.hebrew import parse_hebrew_morphology
from biblical_linguistics_mcp.references.parser import BOOK_ORDER

RAW_DIR = ROOT / "data" / "raw" / "oshb"
BASE_DB = ROOT / "data" / "biblical_linguistics.db"
DB_PATH = Path(os.environ.get("BIBLICAL_LINGUISTICS_DB", ROOT / "data" / "biblical_linguistics.local.db"))
PINNED_COMMIT = "3d15126fb1ef74867fc1434be1942e837932691f"
BASE_URL = f"https://raw.githubusercontent.com/openscriptures/morphhb/{PINNED_COMMIT}/wlc"

OSIS = "{http://www.bibletechnologies.net/2003/OSIS/namespace}"
MAP_NS = "{http://www.APTBibleTools.com/namespace}"

# OSIS book id -> this database's book name, in canonical (KJV) order
BOOKS = {
    "Gen": "Genesis", "Exod": "Exodus", "Lev": "Leviticus", "Num": "Numbers",
    "Deut": "Deuteronomy", "Josh": "Joshua", "Judg": "Judges", "Ruth": "Ruth",
    "1Sam": "1 Samuel", "2Sam": "2 Samuel", "1Kgs": "1 Kings", "2Kgs": "2 Kings",
    "1Chr": "1 Chronicles", "2Chr": "2 Chronicles", "Ezra": "Ezra",
    "Neh": "Nehemiah", "Esth": "Esther", "Job": "Job", "Ps": "Psalms",
    "Prov": "Proverbs", "Eccl": "Ecclesiastes", "Song": "Song of Solomon",
    "Isa": "Isaiah", "Jer": "Jeremiah", "Lam": "Lamentations", "Ezek": "Ezekiel",
    "Dan": "Daniel", "Hos": "Hosea", "Joel": "Joel", "Amos": "Amos",
    "Obad": "Obadiah", "Jonah": "Jonah", "Mic": "Micah", "Nah": "Nahum",
    "Hab": "Habakkuk", "Zeph": "Zephaniah", "Hag": "Haggai", "Zech": "Zechariah",
    "Mal": "Malachi",
}

# VerseMap.xml marks five WLC verses as split between KJV verses (and one, 1Kgs
# 22:44, as the end of KJV 22:43) but gives no place. Each is split here at the word (counting written words from 0) where
# the KJV's next verse begins, read against the KJV's text.
SPLITS = {
    "1Kgs.18.34": (10, "1Kgs.18.33", "1Kgs.18.34"),
    "1Kgs.20.3": (6, "1Kgs.20.2", "1Kgs.20.3"),
    "1Kgs.22.21": (8, "1Kgs.22.21", "1Kgs.22.22"),
    "Isa.63.19": (9, "Isa.63.19", "Isa.64.1"),
    "Ps.13.6": (6, "Ps.13.5", "Ps.13.6"),
}


def fetch_sources() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=120.0, follow_redirects=True) as client:
        for name in [*BOOKS, "VerseMap"]:
            dest = RAW_DIR / f"{name}.xml"
            if not dest.exists():
                resp = client.get(f"{BASE_URL}/{name}.xml")
                resp.raise_for_status()
                dest.write_bytes(resp.content)


def read_verse_map() -> dict[str, str]:
    """WLC verse -> KJV verse, for the verses mapped whole."""
    moves = {}
    for verse in ET.parse(RAW_DIR / "VerseMap.xml").getroot().iter(f"{MAP_NS}verse"):
        wlc, kjv = verse.get("wlc"), verse.get("kjv")
        if "!" not in wlc:
            moves[wlc] = kjv.split("!")[0]
    return moves


def strongs_of(lemma: str) -> str | None:
    """The Strong's number of a word's main morpheme, if it has one."""
    found = re.search(r"\d+", lemma)
    return f"H{int(found.group())}" if found else None


def word_row(element: ET.Element, wlc_ref: str, qere: str | None) -> dict:
    code = element.get("morph", "")
    m = parse_hebrew_morphology(code)
    return {
        "text": text_of(element),
        "strongs": strongs_of(element.get("lemma", "")),
        "code": code,
        "m": m,
        "qere": qere,
        "wlc_ref": wlc_ref,
    }


def text_of(word: ET.Element) -> str:
    """A word's letters, with those a <seg> marks as large or small."""
    return "".join(word.itertext()).replace("/", "")


def read_verse(verse: ET.Element) -> tuple[list[dict], list[str]]:
    """A verse's word rows, and its written words with their marks."""
    wlc_ref = verse.get("osisID")
    children = list(verse)
    rows: list[dict] = []
    written: list[str] = []
    for i, child in enumerate(children):
        if child.tag == f"{OSIS}w":
            qere = None
            if child.get("type") == "x-ketiv":
                for after in children[i + 1:]:
                    if after.tag != f"{OSIS}note":
                        break
                    if after.get("type") == "variant":
                        qere = " ".join(text_of(w) for w in after.iter(f"{OSIS}w"))
                        break
            rows.append(word_row(child, wlc_ref, qere))
            written.append(text_of(child))
        elif child.tag == f"{OSIS}seg":
            if child.get("type") in ("x-maqqef", "x-sof-pasuq", "x-paseq") and written:
                written[-1] += child.text or ""
        elif child.tag == f"{OSIS}note" and child.get("type") == "variant":
            before = [c for c in children[:i] if c.tag != f"{OSIS}note"]
            if not before or before[-1].get("type") != "x-ketiv":
                # Read but not written: a row of its own, not in the verse's text
                for w in child.iter(f"{OSIS}w"):
                    rows.append(word_row(w, wlc_ref, text_of(w)))
    return rows, written


def join_words(written: list[str]) -> str:
    """Words are spaced, except after a maqqef."""
    text = ""
    for word in written:
        text += word if not text or text.endswith("־") else f" {word}"
    return text


def kjv_targets(book: str, refs: list[str], moves: dict[str, str]) -> dict[str, str]:
    """Where each WLC verse of a book goes in the KJV's numbering.

    A verse with no move keeps its number, unless a moved verse has taken that
    number: then it is a Psalm's title, which the KJV prints above verse 1, and
    it goes with the first moved verse after it, if there is one.
    """
    taken = set(moves.values())
    targets: dict[str, str] = {}
    for i, ref in enumerate(refs):
        if ref in moves:
            targets[ref] = moves[ref]
        elif ref in taken and ref not in SPLITS:
            chapter = ref.rsplit(".", 1)[0]
            following = [r for r in refs[i + 1:] if r in moves and r.startswith(f"{chapter}.")]
            # With none after it, two WLC verses make one KJV verse (Num 26:1)
            targets[ref] = moves[following[0]] if following else ref
            if book != "Ps":
                print(f"  note: {ref} joined to {targets[ref]}")
        else:
            targets[ref] = ref
    return targets


def main() -> None:
    fetch_sources()
    moves = read_verse_map()
    if not DB_PATH.exists():
        shutil.copyfile(BASE_DB, DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    columns = {r[1] for r in conn.execute("PRAGMA table_info(words)")}
    for column in ("qere", "wlc_ref"):
        if column not in columns:
            conn.execute(f"ALTER TABLE words ADD COLUMN {column} TEXT")

    conn.execute(
        "DELETE FROM words WHERE verse_id IN (SELECT v.id FROM verses v "
        "JOIN books b USING (book_number) WHERE b.testament = 'OT')"
    )
    conn.execute(
        "UPDATE verses SET text_original = NULL WHERE book_number IN "
        "(SELECT book_number FROM books WHERE testament = 'OT')"
    )

    verse_ids = {
        (n, c, v): i
        for i, n, c, v in conn.execute("SELECT id, book_number, chapter, verse FROM verses")
    }
    total = 0
    for osis, name in BOOKS.items():
        book_number = BOOK_ORDER[name]
        verses = list(ET.parse(RAW_DIR / f"{osis}.xml").getroot().iter(f"{OSIS}verse"))
        refs = [v.get("osisID") for v in verses]
        targets = kjv_targets(osis, refs, moves)

        # KJV verse -> its rows and written words, in the order the WLC has them
        gathered: dict[str, tuple[list[dict], list[str]]] = {}

        def add(ref: str, rows: list[dict], written: list[str]) -> None:
            kept = gathered.setdefault(ref, ([], []))
            kept[0].extend(rows)
            kept[1].extend(written)

        for verse in verses:
            ref = verse.get("osisID")
            rows, written = read_verse(verse)
            if ref in SPLITS:
                at, first, second = SPLITS[ref]
                if len(rows) != len(written):
                    raise SystemExit(f"{ref}: a split verse has an unwritten word")
                add(first, rows[:at], written[:at])
                add(second, rows[at:], written[at:])
            else:
                add(targets[ref], rows, written)

        for ref, (rows, written) in gathered.items():
            _, chapter, number = ref.split(".")
            verse_id = verse_ids.get((book_number, int(chapter), int(number)))
            if verse_id is None:
                raise SystemExit(f"{ref}: no such verse in the database")
            conn.execute(
                "UPDATE verses SET text_original = ? WHERE id = ?",
                (join_words(written), verse_id),
            )
            conn.executemany(
                "INSERT INTO words (verse_id, word_position, text_original, strongs, "
                "morphology_code, part_of_speech, stem, aspect, state, person, number, "
                "gender, suffix_person, suffix_number, suffix_gender, qere, wlc_ref) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                [
                    (
                        verse_id, position, r["text"], r["strongs"], r["code"],
                        r["m"].part_of_speech or None, r["m"].stem or None,
                        r["m"].aspect or None, r["m"].state or None,
                        r["m"].person or None, r["m"].number or None,
                        r["m"].gender or None, r["m"].suffix_person or None,
                        r["m"].suffix_number or None, r["m"].suffix_gender or None,
                        r["qere"], r["wlc_ref"],
                    )
                    for position, r in enumerate(rows, start=1)
                ],
            )
            total += len(rows)

    conn.execute(
        "UPDATE lexemes SET frequency = "
        "(SELECT COUNT(*) FROM words WHERE words.strongs = lexemes.strongs)"
    )
    conn.commit()
    print(f"Loaded {total} words")
    empty = conn.execute(
        "SELECT b.name, v.chapter, v.verse FROM verses v JOIN books b USING (book_number) "
        "WHERE b.testament = 'OT' AND v.text_original IS NULL"
    ).fetchall()
    print(f"OT verses with no Hebrew: {len(empty)} {empty[:20]}")
    orphans = conn.execute(
        "SELECT COUNT(DISTINCT strongs) FROM words WHERE strongs IS NOT NULL "
        "AND strongs NOT IN (SELECT strongs FROM lexemes)"
    ).fetchone()[0]
    print(f"Strong's numbers with no lexicon entry: {orphans}")
    conn.close()


if __name__ == "__main__":
    main()
