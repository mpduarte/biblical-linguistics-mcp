#!/usr/bin/env python3
"""Bootstrap the Biblical Linguistics database.

Downloads raw sources (if needed), parses and normalizes them into the
SQLite schema, builds indexes, and validates data integrity.

Idempotent — safe to re-run without duplicating data.
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Add src to path so we can import the package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from biblical_linguistics_mcp.db.schema import SCHEMA_SQL
from biblical_linguistics_mcp.references.parser import BOOK_DATA, BOOK_ORDER

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "biblical_linguistics.db"

# scrollmapper bible_databases use 1-based book IDs matching our BOOK_ORDER
# (Gen=1 ... Rev=66)


def ensure_downloads() -> None:
    """Run download script if key files are missing."""
    required = ["t_kjv.json", "key_english.json"]
    missing = [f for f in required if not (RAW_DIR / f).exists()]
    if missing:
        print("Required data files missing. Running download_sources.py...")
        import subprocess
        subprocess.run(
            [sys.executable, str(Path(__file__).parent / "download_sources.py")],
            check=True,
        )


def create_schema(conn: sqlite3.Connection) -> None:
    """Create tables and indexes."""
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    print("[schema] Tables and indexes created")


def load_books(conn: sqlite3.Connection) -> None:
    """Load Bible books metadata."""
    existing = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    if existing > 0:
        print(f"[books] Already loaded ({existing} books)")
        return

    for bd in BOOK_DATA:
        lang = "Hebrew" if bd["testament"] == "OT" else "Greek"
        # Special case: Daniel/Ezra have Aramaic portions, but primary is Hebrew
        conn.execute(
            "INSERT OR IGNORE INTO books (book_number, name, testament, chapters, original_language) "
            "VALUES (?, ?, ?, ?, ?)",
            (BOOK_ORDER[bd["name"]], bd["name"], bd["testament"], bd["chapters"], lang),
        )
    conn.commit()
    print(f"[books] Loaded {len(BOOK_DATA)} books")


def load_translation(conn: sqlite3.Connection, filename: str, column: str) -> int:
    """Load a Bible translation from scrollmapper JSON format.

    Format: array of objects with keys: b (book), c (chapter), v (verse), t (text)
    """
    filepath = RAW_DIR / filename
    if not filepath.exists():
        print(f"[{column}] File not found: {filename}, skipping")
        return 0

    data = json.loads(filepath.read_text(encoding="utf-8"))

    # Check if already loaded by sampling
    sample = conn.execute(
        f"SELECT {column} FROM verses WHERE book_number = 1 AND chapter = 1 AND verse = 1"
    ).fetchone()
    if sample and sample[0]:
        print(f"[{column}] Already loaded")
        return 0

    count = 0
    for entry in data:
        book = int(entry.get("b", 0))
        chapter = int(entry.get("c", 0))
        verse = int(entry.get("v", 0))
        text = entry.get("t", "").strip()

        if not (1 <= book <= 66) or not text:
            continue

        # Upsert: insert verse row if needed, then update the translation column
        conn.execute(
            "INSERT OR IGNORE INTO verses (book_number, chapter, verse) VALUES (?, ?, ?)",
            (book, chapter, verse),
        )
        conn.execute(
            f"UPDATE verses SET {column} = ? WHERE book_number = ? AND chapter = ? AND verse = ?",
            (text, book, chapter, verse),
        )
        count += 1

    conn.commit()
    print(f"[{column}] Loaded {count} verses from {filename}")
    return count


def load_strongs_data(conn: sqlite3.Connection) -> int:
    """Load Strong's concordance data linking words to verses."""
    filepath = RAW_DIR / "t_strongs.json"
    if not filepath.exists():
        print("[strongs] t_strongs.json not found, skipping")
        return 0

    existing = conn.execute("SELECT COUNT(*) FROM words").fetchone()[0]
    if existing > 0:
        print(f"[strongs] Already loaded ({existing} word entries)")
        return existing

    data = json.loads(filepath.read_text(encoding="utf-8"))

    count = 0
    for entry in data:
        book = int(entry.get("b", 0))
        chapter = int(entry.get("c", 0))
        verse = int(entry.get("v", 0))
        strongs_raw = entry.get("t", "").strip()

        if not (1 <= book <= 66) or not strongs_raw:
            continue

        # Get verse id
        row = conn.execute(
            "SELECT id FROM verses WHERE book_number = ? AND chapter = ? AND verse = ?",
            (book, chapter, verse),
        ).fetchone()
        if not row:
            continue
        verse_id = row[0]

        # Parse Strong's numbers (may be space-separated)
        strongs_numbers = strongs_raw.split()
        for pos, sn in enumerate(strongs_numbers, 1):
            sn = sn.strip()
            if not sn:
                continue
            # Normalize: ensure H/G prefix
            if sn.isdigit():
                # Determine prefix from book number
                prefix = "H" if book <= 39 else "G"
                sn = f"{prefix}{sn}"
            elif sn[0] not in ("H", "G") and sn[1:].isdigit():
                continue

            conn.execute(
                "INSERT INTO words (verse_id, word_position, text_original, strongs) "
                "VALUES (?, ?, ?, ?)",
                (verse_id, pos, "", sn),
            )
            count += 1

    conn.commit()
    print(f"[strongs] Loaded {count} word-to-verse mappings")
    return count


def load_dodson_greek_lexicon(conn: sqlite3.Connection) -> int:
    """Load Dodson Greek lexicon."""
    filepath = RAW_DIR / "dodson_greek.json"
    if not filepath.exists():
        print("[greek_lexicon] dodson_greek.json not found, skipping")
        return 0

    existing = conn.execute("SELECT COUNT(*) FROM lexemes WHERE language = 'Greek'").fetchone()[0]
    if existing > 0:
        print(f"[greek_lexicon] Already loaded ({existing} entries)")
        return existing

    data = json.loads(filepath.read_text(encoding="utf-8"))

    count = 0
    for strongs_num, entry in data.items():
        # Normalize Strong's number
        sn = strongs_num.strip()
        if not sn.startswith("G"):
            sn = f"G{sn}"

        word = entry.get("word", "")
        gloss = entry.get("short_definition", "") or entry.get("definition", "")
        definition = entry.get("long_definition", "") or entry.get("definition", "")
        transliteration = entry.get("translit", "") or entry.get("transliteration", "")

        conn.execute(
            "INSERT OR IGNORE INTO lexemes (strongs, language, word, transliteration, root_form, gloss, definition) "
            "VALUES (?, 'Greek', ?, ?, ?, ?, ?)",
            (sn, word, transliteration, word, gloss, definition),
        )
        count += 1

    conn.commit()
    print(f"[greek_lexicon] Loaded {count} Greek lexicon entries")
    return count


def load_hebrew_lexicon(conn: sqlite3.Connection) -> int:
    """Load Hebrew Strong's lexicon from XML."""
    filepath = RAW_DIR / "HebrewStrong.xml"
    if not filepath.exists():
        print("[hebrew_lexicon] HebrewStrong.xml not found, skipping")
        return 0

    existing = conn.execute("SELECT COUNT(*) FROM lexemes WHERE language = 'Hebrew'").fetchone()[0]
    if existing > 0:
        print(f"[hebrew_lexicon] Already loaded ({existing} entries)")
        return existing

    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"[hebrew_lexicon] XML parse error: {e}")
        return 0

    count = 0
    # Try multiple possible XML structures
    for entry in root.iter():
        if entry.tag in ("entry", "w", "item"):
            strongs = entry.get("id", "") or entry.get("strongs", "") or entry.get("n", "")
            if not strongs:
                continue
            if not strongs.startswith("H"):
                strongs = f"H{strongs}"

            word = entry.findtext("w", "") or entry.get("word", "") or ""
            gloss = entry.findtext("meaning", "") or entry.findtext("def", "") or ""
            transliteration = entry.findtext("translit", "") or entry.get("translit", "") or ""

            if word or gloss:
                conn.execute(
                    "INSERT OR IGNORE INTO lexemes (strongs, language, word, transliteration, root_form, gloss, definition) "
                    "VALUES (?, 'Hebrew', ?, ?, ?, ?, ?)",
                    (strongs, word, transliteration, word, gloss, gloss),
                )
                count += 1

    conn.commit()
    print(f"[hebrew_lexicon] Loaded {count} Hebrew lexicon entries")
    return count


def load_cross_references(conn: sqlite3.Connection) -> int:
    """Load TSK cross-references."""
    filepath = RAW_DIR / "cross_references.json"
    if not filepath.exists():
        print("[crossrefs] cross_references.json not found, skipping")
        return 0

    existing = conn.execute("SELECT COUNT(*) FROM cross_references").fetchone()[0]
    if existing > 0:
        print(f"[crossrefs] Already loaded ({existing} entries)")
        return existing

    data = json.loads(filepath.read_text(encoding="utf-8"))

    count = 0
    for entry in data:
        # scrollmapper format: sv (source verse ID), ev (end verse ID)
        # or: fb, fc, fv (from book/chapter/verse), tb, tc, tv (to book/chapter/verse)
        src_book = int(entry.get("fb", entry.get("from_book", 0)))
        src_ch = int(entry.get("fc", entry.get("from_chapter", 0)))
        src_vs = int(entry.get("fv", entry.get("from_verse", 0)))
        tgt_book = int(entry.get("tb", entry.get("to_book", 0)))
        tgt_ch = int(entry.get("tc", entry.get("to_chapter", 0)))
        tgt_vs = int(entry.get("tv", entry.get("to_verse", 0)))

        if not (1 <= src_book <= 66 and 1 <= tgt_book <= 66):
            continue

        conn.execute(
            "INSERT INTO cross_references (source_book, source_chapter, source_verse, "
            "target_book, target_chapter, target_verse, source) VALUES (?, ?, ?, ?, ?, ?, 'TSK')",
            (src_book, src_ch, src_vs, tgt_book, tgt_ch, tgt_vs),
        )
        count += 1

    conn.commit()
    print(f"[crossrefs] Loaded {count} cross-references")
    return count


def update_lexeme_frequencies(conn: sqlite3.Connection) -> None:
    """Update frequency counts on lexemes from word occurrence data."""
    conn.execute("""
        UPDATE lexemes SET frequency = (
            SELECT COUNT(*) FROM words WHERE words.strongs = lexemes.strongs
        )
    """)
    conn.commit()
    updated = conn.execute("SELECT COUNT(*) FROM lexemes WHERE frequency > 0").fetchone()[0]
    print(f"[frequencies] Updated frequency for {updated} lexemes")


def validate_data(conn: sqlite3.Connection) -> None:
    """Run validation checks and report statistics."""
    print("\n=== Data Validation ===")

    stats = {
        "books": conn.execute("SELECT COUNT(*) FROM books").fetchone()[0],
        "verses": conn.execute("SELECT COUNT(*) FROM verses").fetchone()[0],
        "words": conn.execute("SELECT COUNT(*) FROM words").fetchone()[0],
        "lexemes_total": conn.execute("SELECT COUNT(*) FROM lexemes").fetchone()[0],
        "lexemes_hebrew": conn.execute("SELECT COUNT(*) FROM lexemes WHERE language='Hebrew'").fetchone()[0],
        "lexemes_greek": conn.execute("SELECT COUNT(*) FROM lexemes WHERE language='Greek'").fetchone()[0],
        "cross_references": conn.execute("SELECT COUNT(*) FROM cross_references").fetchone()[0],
        "topics": conn.execute("SELECT COUNT(*) FROM topics").fetchone()[0],
        "lxx_alignments": conn.execute("SELECT COUNT(*) FROM lxx_alignments").fetchone()[0],
    }

    for key, val in stats.items():
        print(f"  {key}: {val:,}")

    # Spot checks
    gen11 = conn.execute(
        "SELECT text_kjv FROM verses WHERE book_number = 1 AND chapter = 1 AND verse = 1"
    ).fetchone()
    if gen11 and gen11[0]:
        print(f"\n  Genesis 1:1 (KJV): {gen11[0][:80]}...")
    else:
        print("\n  WARNING: Genesis 1:1 KJV text not found!")

    jn11 = conn.execute(
        "SELECT text_kjv FROM verses WHERE book_number = 43 AND chapter = 1 AND verse = 1"
    ).fetchone()
    if jn11 and jn11[0]:
        print(f"  John 1:1 (KJV): {jn11[0][:80]}...")

    # Check for orphaned Strong's references
    orphaned = conn.execute(
        "SELECT COUNT(DISTINCT strongs) FROM words WHERE strongs IS NOT NULL "
        "AND strongs NOT IN (SELECT strongs FROM lexemes)"
    ).fetchone()[0]
    if orphaned:
        print(f"\n  INFO: {orphaned} Strong's numbers in words table without lexicon entries")

    print("\n=== Bootstrap Complete ===")


def main() -> None:
    print("Biblical Linguistics MCP — Data Bootstrap")
    print(f"Database: {DB_PATH}\n")

    # Step 0: Ensure downloads
    ensure_downloads()

    # Step 1: Create/connect database
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    try:
        # Step 2: Create schema
        create_schema(conn)

        # Step 3: Load books
        load_books(conn)

        # Step 4: Load translations
        load_translation(conn, "t_kjv.json", "text_kjv")
        load_translation(conn, "t_asv.json", "text_asv")
        load_translation(conn, "t_web.json", "text_web")

        # Step 5: Load Strong's word data
        load_strongs_data(conn)

        # Step 6: Load lexicons
        load_dodson_greek_lexicon(conn)
        load_hebrew_lexicon(conn)

        # Step 7: Load cross-references
        load_cross_references(conn)

        # Step 8: Update frequencies
        update_lexeme_frequencies(conn)

        # Step 9: Validate
        validate_data(conn)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
