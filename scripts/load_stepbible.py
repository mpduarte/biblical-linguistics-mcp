#!/usr/bin/env python3
"""Load STEPBible's extended Strong's numbers onto the Old Testament's words.

Plain Strong's numbers join words that BDB keeps apart: H7462 is both "to
pasture" (H7462B) and "to accompany" (H7462C). TAHOT tags each word with the
BDB-level number, prefixes and particles included; TBESH defines those numbers.

Run after load_oshb.py. TAHOT's words are matched to the OSHB's in order, by
their letters. Safe to re-run. Data by Tyndale House and STEPBible.org, CC BY
4.0: https://stepbible.github.io/STEPBible-Data
"""

from __future__ import annotations

import os
import re
import sqlite3
from pathlib import Path
from urllib.parse import quote

import httpx

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw" / "stepbible"
DB_PATH = Path(os.environ.get("BIBLICAL_LINGUISTICS_DB", ROOT / "data" / "biblical_linguistics.local.db"))
PINNED_COMMIT = "5de0a47f35f0fc13dfe1430d104e5db8a4285f9c"
BASE_URL = f"https://raw.githubusercontent.com/STEPBible/STEPBible-Data/{PINNED_COMMIT}"

TAHOT_DIR = "Translators Amalgamated OT+NT"
TAHOT_FILES = [
    f"TAHOT {part} - Translators Amalgamated Hebrew OT - STEPBible.org CC BY.txt"
    for part in ("Gen-Deu", "Jos-Est", "Job-Sng", "Isa-Mal")
]
TBESH_FILE = "TBESH - Translators Brief lexicon of Extended Strongs for Hebrew - STEPBible.org CC BY.txt"

# TAHOT's book ids in file order; book_number is the place in this list
BOOKS = (
    "Gen Exo Lev Num Deu Jos Jdg Rut 1Sa 2Sa 1Ki 2Ki 1Ch 2Ch Ezr Neh Est Job Psa "
    "Pro Ecc Sng Isa Jer Lam Ezk Dan Hos Jol Amo Oba Jon Mic Nam Hab Zep Hag Zec Mal"
).split()

ROW = re.compile(r"^([1-3]?[A-Za-z]+)\.\d+\.\d+(?:\([\d.]+\))?#\d+=(\S+)$")
ROOT_TAG = re.compile(r"\{(H\d{4}[A-Z]?)\}")
ROOT_MEANING = re.compile(r"\{(H\d{4}[A-Z]?)=[^=}]*=([^}]*)\}")
LOOKAHEAD = 40


def fetch(url_path: str, dest: Path, client: httpx.Client) -> None:
    if not dest.exists():
        resp = client.get(f"{BASE_URL}/{quote(url_path)}")
        resp.raise_for_status()
        dest.write_bytes(resp.content)


def fetch_sources() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=300.0, follow_redirects=True) as client:
        for name in TAHOT_FILES:
            fetch(f"{TAHOT_DIR}/{name}", RAW_DIR / name, client)
        fetch(f"Lexicons/{TBESH_FILE}", RAW_DIR / TBESH_FILE, client)


def letters(text: str) -> str:
    """A word's consonants, with final forms made plain."""
    plain = re.sub(r"[^א-ת]", "", text)
    return plain.translate(str.maketrans("ךםןףץ", "כמנפצ"))


def meaning_of(expanded: str) -> str:
    found = ROOT_MEANING.search(expanded)
    if not found:
        return ""
    meaning = found.group(2).lstrip(": ")
    return meaning.split("»")[-1].split("@")[0].split(":")[0].strip()


def read_tahot() -> dict[int, list[dict]]:
    """Each book's rows, leaving out words reconstructed from the LXX."""
    books: dict[int, list[dict]] = {}
    for name in TAHOT_FILES:
        for line in (RAW_DIR / name).read_text(encoding="utf-8-sig").splitlines():
            cells = line.split("\t")
            found = ROW.match(cells[0])
            if not found or len(cells) < 12:
                continue
            book, kind = found.groups()
            if kind[0] == "X":  # back-translated from the LXX, not in any Hebrew here
                continue
            tag = ROOT_TAG.search(cells[4])
            books.setdefault(BOOKS.index(book) + 1, []).append({
                "key": letters(cells[1].split("\\")[0]),
                "alt": letters(cells[6]) if cells[6].startswith("K=") else "",
                "tag": tag.group(1) if tag else None,
                "tags": cells[4],
                "translation": cells[3].strip(),
                "sense": meaning_of(cells[-1] if "=" in cells[-1] else " ".join(cells[11:])),
            })
    return books


def same(word: dict, row: dict) -> bool:
    keys = {word["text"], word["qere"]} - {""}
    return row["key"] in keys or any(k and k in row["alt"] for k in keys)


def align(words: list[dict], rows: list[dict]) -> list[tuple[dict, dict]]:
    """Pair two sequences of the same text, skipping past small differences."""
    pairs = []
    i = j = 0
    while i < len(words) and j < len(rows):
        if same(words[i], rows[j]):
            pairs.append((words[i], rows[j]))
            i += 1
            j += 1
            continue
        for skip in range(1, LOOKAHEAD + 1):
            moved = [
                (a, b)
                for a, b in ((skip, 0), (0, skip), (skip, skip))
                if i + a < len(words) and j + b < len(rows) and same(words[i + a], rows[j + b])
            ]
            if moved:
                i += moved[0][0]
                j += moved[0][1]
                break
        else:
            i += 1
            j += 1
    return pairs


def main() -> None:
    if not DB_PATH.exists():
        raise SystemExit(f"{DB_PATH} is missing: run load_oshb.py first")
    fetch_sources()
    conn = sqlite3.connect(DB_PATH)
    columns = {r[1] for r in conn.execute("PRAGMA table_info(words)")}
    for column in ("strongs_ext", "strongs_tags", "sense", "translation"):
        if column not in columns:
            conn.execute(f"ALTER TABLE words ADD COLUMN {column} TEXT")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS extended_lexemes (strongs TEXT PRIMARY KEY, "
        "word TEXT, transliteration TEXT, morphology TEXT, gloss TEXT, definition TEXT)"
    )
    conn.execute("DELETE FROM extended_lexemes")
    for line in (RAW_DIR / TBESH_FILE).read_text(encoding="utf-8-sig").splitlines():
        cells = line.split("\t")
        if len(cells) >= 8:
            found = re.match(r"H\d{4}[A-Z]?\b", cells[1])
            if found:
                conn.execute(
                    "INSERT OR IGNORE INTO extended_lexemes VALUES (?,?,?,?,?,?)",
                    (found.group(), cells[3], cells[4], cells[5], cells[6], cells[7]),
                )

    conn.execute(
        "UPDATE words SET strongs_ext = NULL, strongs_tags = NULL, sense = NULL, translation = NULL"
    )
    tahot = read_tahot()
    matched = total = disagree = 0
    for book_number, rows in sorted(tahot.items()):
        words = [
            {"id": i, "text": letters(t), "qere": letters(q or ""), "strongs": s}
            for i, t, q, s in conn.execute(
                "SELECT w.id, w.text_original, w.qere, w.strongs FROM words w "
                "JOIN verses v ON v.id = w.verse_id WHERE v.book_number = ? "
                "ORDER BY v.chapter, v.verse, w.word_position",
                (book_number,),
            )
        ]
        pairs = align(words, rows)
        total += len(words)
        matched += len(pairs)
        for word, row in pairs:
            plain = f"H{int(row['tag'][1:5])}" if row["tag"] else None
            if word["strongs"] and plain and word["strongs"] != plain:
                disagree += 1
        conn.executemany(
            "UPDATE words SET strongs_ext = ?, strongs_tags = ?, sense = ?, translation = ? "
            "WHERE id = ?",
            [
                (r["tag"], r["tags"], r["sense"] or None, r["translation"] or None, w["id"])
                for w, r in pairs
            ],
        )
        print(f"  {BOOKS[book_number - 1]}: {len(pairs)}/{len(words)} words, {len(rows)} TAHOT rows")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_words_strongs_ext ON words(strongs_ext)")
    conn.commit()
    print(f"Matched {matched}/{total} words; plain Strong's differs on {disagree}")
    print("Lexicon entries:", conn.execute("SELECT COUNT(*) FROM extended_lexemes").fetchone()[0])
    conn.close()


if __name__ == "__main__":
    main()
