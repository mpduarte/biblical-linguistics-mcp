"""Bible reference parser — handles all common reference formats."""

from __future__ import annotations

import re
from dataclasses import dataclass

# Canonical book names with abbreviations and metadata
BOOK_DATA: list[dict] = [
    # OT
    {"name": "Genesis", "abbrevs": ["gen", "ge", "gn"], "testament": "OT", "chapters": 50},
    {"name": "Exodus", "abbrevs": ["exo", "exod", "ex"], "testament": "OT", "chapters": 40},
    {"name": "Leviticus", "abbrevs": ["lev", "le", "lv"], "testament": "OT", "chapters": 27},
    {"name": "Numbers", "abbrevs": ["num", "nu", "nm", "nb"], "testament": "OT", "chapters": 36},
    {"name": "Deuteronomy", "abbrevs": ["deut", "de", "dt"], "testament": "OT", "chapters": 34},
    {"name": "Joshua", "abbrevs": ["josh", "jos", "jsh"], "testament": "OT", "chapters": 24},
    {"name": "Judges", "abbrevs": ["judg", "jdg", "jg", "jdgs"], "testament": "OT", "chapters": 21},
    {"name": "Ruth", "abbrevs": ["rth", "ru"], "testament": "OT", "chapters": 4},
    {"name": "1 Samuel", "abbrevs": ["1sam", "1sa", "1 sam", "1 sa", "i sam", "i sa"], "testament": "OT", "chapters": 31},
    {"name": "2 Samuel", "abbrevs": ["2sam", "2sa", "2 sam", "2 sa", "ii sam", "ii sa"], "testament": "OT", "chapters": 24},
    {"name": "1 Kings", "abbrevs": ["1kgs", "1ki", "1 kgs", "1 ki", "i kgs", "i ki"], "testament": "OT", "chapters": 22},
    {"name": "2 Kings", "abbrevs": ["2kgs", "2ki", "2 kgs", "2 ki", "ii kgs", "ii ki"], "testament": "OT", "chapters": 25},
    {"name": "1 Chronicles", "abbrevs": ["1chr", "1ch", "1 chr", "1 ch", "i chr", "i ch"], "testament": "OT", "chapters": 29},
    {"name": "2 Chronicles", "abbrevs": ["2chr", "2ch", "2 chr", "2 ch", "ii chr", "ii ch"], "testament": "OT", "chapters": 36},
    {"name": "Ezra", "abbrevs": ["ezr", "ez"], "testament": "OT", "chapters": 10},
    {"name": "Nehemiah", "abbrevs": ["neh", "ne"], "testament": "OT", "chapters": 13},
    {"name": "Esther", "abbrevs": ["esth", "est", "es"], "testament": "OT", "chapters": 10},
    {"name": "Job", "abbrevs": ["jb"], "testament": "OT", "chapters": 42},
    {"name": "Psalms", "abbrevs": ["psa", "ps", "psalm", "pslm", "psm"], "testament": "OT", "chapters": 150},
    {"name": "Proverbs", "abbrevs": ["prov", "pro", "prv", "pr"], "testament": "OT", "chapters": 31},
    {"name": "Ecclesiastes", "abbrevs": ["eccl", "ecc", "ec", "eccles"], "testament": "OT", "chapters": 12},
    {"name": "Song of Solomon", "abbrevs": ["song", "sos", "so", "song of songs", "canticles", "cant"], "testament": "OT", "chapters": 8},
    {"name": "Isaiah", "abbrevs": ["isa", "is"], "testament": "OT", "chapters": 66},
    {"name": "Jeremiah", "abbrevs": ["jer", "je", "jr"], "testament": "OT", "chapters": 52},
    {"name": "Lamentations", "abbrevs": ["lam", "la"], "testament": "OT", "chapters": 5},
    {"name": "Ezekiel", "abbrevs": ["ezek", "eze", "ezk"], "testament": "OT", "chapters": 48},
    {"name": "Daniel", "abbrevs": ["dan", "da", "dn"], "testament": "OT", "chapters": 12},
    {"name": "Hosea", "abbrevs": ["hos", "ho"], "testament": "OT", "chapters": 14},
    {"name": "Joel", "abbrevs": ["joe", "jl"], "testament": "OT", "chapters": 3},
    {"name": "Amos", "abbrevs": ["amo", "am"], "testament": "OT", "chapters": 9},
    {"name": "Obadiah", "abbrevs": ["oba", "ob", "obad"], "testament": "OT", "chapters": 1},
    {"name": "Jonah", "abbrevs": ["jon", "jnh"], "testament": "OT", "chapters": 4},
    {"name": "Micah", "abbrevs": ["mic", "mc"], "testament": "OT", "chapters": 7},
    {"name": "Nahum", "abbrevs": ["nah", "na"], "testament": "OT", "chapters": 3},
    {"name": "Habakkuk", "abbrevs": ["hab", "hb"], "testament": "OT", "chapters": 3},
    {"name": "Zephaniah", "abbrevs": ["zeph", "zep", "zp"], "testament": "OT", "chapters": 3},
    {"name": "Haggai", "abbrevs": ["hag", "hg"], "testament": "OT", "chapters": 2},
    {"name": "Zechariah", "abbrevs": ["zech", "zec", "zc"], "testament": "OT", "chapters": 14},
    {"name": "Malachi", "abbrevs": ["mal", "ml"], "testament": "OT", "chapters": 4},
    # NT
    {"name": "Matthew", "abbrevs": ["matt", "mat", "mt"], "testament": "NT", "chapters": 28},
    {"name": "Mark", "abbrevs": ["mrk", "mar", "mk", "mr"], "testament": "NT", "chapters": 16},
    {"name": "Luke", "abbrevs": ["luk", "lk"], "testament": "NT", "chapters": 24},
    {"name": "John", "abbrevs": ["joh", "jhn", "jn"], "testament": "NT", "chapters": 21},
    {"name": "Acts", "abbrevs": ["act", "ac"], "testament": "NT", "chapters": 28},
    {"name": "Romans", "abbrevs": ["rom", "ro", "rm"], "testament": "NT", "chapters": 16},
    {"name": "1 Corinthians", "abbrevs": ["1cor", "1co", "1 cor", "1 co", "i cor", "i co"], "testament": "NT", "chapters": 16},
    {"name": "2 Corinthians", "abbrevs": ["2cor", "2co", "2 cor", "2 co", "ii cor", "ii co"], "testament": "NT", "chapters": 13},
    {"name": "Galatians", "abbrevs": ["gal", "ga"], "testament": "NT", "chapters": 6},
    {"name": "Ephesians", "abbrevs": ["eph", "ep"], "testament": "NT", "chapters": 6},
    {"name": "Philippians", "abbrevs": ["phil", "php", "pp"], "testament": "NT", "chapters": 4},
    {"name": "Colossians", "abbrevs": ["col", "co"], "testament": "NT", "chapters": 4},
    {"name": "1 Thessalonians", "abbrevs": ["1thess", "1th", "1 thess", "1 th", "i thess", "i th"], "testament": "NT", "chapters": 5},
    {"name": "2 Thessalonians", "abbrevs": ["2thess", "2th", "2 thess", "2 th", "ii thess", "ii th"], "testament": "NT", "chapters": 3},
    {"name": "1 Timothy", "abbrevs": ["1tim", "1ti", "1 tim", "1 ti", "i tim", "i ti"], "testament": "NT", "chapters": 6},
    {"name": "2 Timothy", "abbrevs": ["2tim", "2ti", "2 tim", "2 ti", "ii tim", "ii ti"], "testament": "NT", "chapters": 4},
    {"name": "Titus", "abbrevs": ["tit", "ti"], "testament": "NT", "chapters": 3},
    {"name": "Philemon", "abbrevs": ["phm", "phlm", "philem"], "testament": "NT", "chapters": 1},
    {"name": "Hebrews", "abbrevs": ["heb", "he"], "testament": "NT", "chapters": 13},
    {"name": "James", "abbrevs": ["jas", "jm"], "testament": "NT", "chapters": 5},
    {"name": "1 Peter", "abbrevs": ["1pet", "1pe", "1pt", "1 pet", "1 pe", "i pet", "i pe"], "testament": "NT", "chapters": 5},
    {"name": "2 Peter", "abbrevs": ["2pet", "2pe", "2pt", "2 pet", "2 pe", "ii pet", "ii pe"], "testament": "NT", "chapters": 3},
    {"name": "1 John", "abbrevs": ["1joh", "1jn", "1jo", "1 joh", "1 jn", "1 jo", "i joh", "i jn", "i jo"], "testament": "NT", "chapters": 5},
    {"name": "2 John", "abbrevs": ["2joh", "2jn", "2jo", "2 joh", "2 jn", "2 jo", "ii joh", "ii jn", "ii jo"], "testament": "NT", "chapters": 1},
    {"name": "3 John", "abbrevs": ["3joh", "3jn", "3jo", "3 joh", "3 jn", "3 jo", "iii joh", "iii jn", "iii jo"], "testament": "NT", "chapters": 1},
    {"name": "Jude", "abbrevs": ["jud", "jd"], "testament": "NT", "chapters": 1},
    {"name": "Revelation", "abbrevs": ["rev", "re", "rv", "apocalypse"], "testament": "NT", "chapters": 22},
]

# Build lookup table: lowercase name/abbrev -> canonical name
_BOOK_LOOKUP: dict[str, str] = {}
_BOOK_META: dict[str, dict] = {}
for _bd in BOOK_DATA:
    canonical = _bd["name"]
    _BOOK_META[canonical] = _bd
    _BOOK_LOOKUP[canonical.lower()] = canonical
    for abbr in _bd["abbrevs"]:
        _BOOK_LOOKUP[abbr.lower()] = canonical

# Book order (1-indexed)
BOOK_ORDER: dict[str, int] = {bd["name"]: i + 1 for i, bd in enumerate(BOOK_DATA)}


@dataclass
class VerseRef:
    """A single verse reference."""

    book: str  # Canonical name e.g. "Genesis"
    chapter: int
    verse: int
    book_number: int  # 1-66

    @property
    def testament(self) -> str:
        return _BOOK_META[self.book]["testament"]

    @property
    def osis(self) -> str:
        return f"{self.book} {self.chapter}:{self.verse}"

    def __str__(self) -> str:
        return self.osis


@dataclass
class VerseRange:
    """A range of verses (possibly a single verse)."""

    start: VerseRef
    end: VerseRef | None = None

    @property
    def is_single(self) -> bool:
        return self.end is None

    def __str__(self) -> str:
        if self.is_single:
            return str(self.start)
        assert self.end is not None
        if self.start.book == self.end.book and self.start.chapter == self.end.chapter:
            return f"{self.start.book} {self.start.chapter}:{self.start.verse}-{self.end.verse}"
        return f"{self.start} - {self.end}"


class ReferenceError(Exception):
    """Invalid Bible reference."""


def normalize_book_name(raw: str) -> str:
    """Resolve a book name or abbreviation to its canonical form."""
    key = raw.strip().lower().rstrip(".")
    if key in _BOOK_LOOKUP:
        return _BOOK_LOOKUP[key]
    # Try removing trailing 's' for plurals like "Psalms" -> "psalm"
    if key.endswith("s") and key[:-1] in _BOOK_LOOKUP:
        return _BOOK_LOOKUP[key[:-1]]
    raise ReferenceError(f"Unknown book: {raw!r}")


# Regex: optional number prefix, book name, chapter:verse(-verse)?
_REF_PATTERN = re.compile(
    r"^(?P<book>(?:[123iIl]{1,3}\s+)?[A-Za-z ]+?)\s+"
    r"(?P<chapter>\d+)"
    r"(?::(?P<verse_start>\d+)"
    r"(?:-(?P<verse_end>\d+))?)?"
    r"$"
)


def parse_reference(ref_str: str) -> VerseRange:
    """Parse a Bible reference string into a VerseRange.

    Supported formats:
    - "Genesis 1:1"
    - "Gen 1:1"
    - "1 John 3:16"
    - "Rom 8:28-30"
    - "Psalm 23" (whole chapter)
    """
    ref_str = ref_str.strip()
    m = _REF_PATTERN.match(ref_str)
    if not m:
        raise ReferenceError(f"Cannot parse reference: {ref_str!r}")

    book = normalize_book_name(m.group("book"))
    chapter = int(m.group("chapter"))
    verse_start_str = m.group("verse_start")
    verse_end_str = m.group("verse_end")

    book_num = BOOK_ORDER[book]

    if verse_start_str is None:
        # Whole chapter reference — treat as verse 1
        start = VerseRef(book=book, chapter=chapter, verse=1, book_number=book_num)
        return VerseRange(start=start)

    verse_start = int(verse_start_str)
    start = VerseRef(book=book, chapter=chapter, verse=verse_start, book_number=book_num)

    if verse_end_str is not None:
        verse_end = int(verse_end_str)
        end = VerseRef(book=book, chapter=chapter, verse=verse_end, book_number=book_num)
        return VerseRange(start=start, end=end)

    return VerseRange(start=start)


def get_book_metadata(book_name: str) -> dict:
    """Return metadata for a canonical book name."""
    if book_name not in _BOOK_META:
        raise ReferenceError(f"Unknown book: {book_name!r}")
    bd = _BOOK_META[book_name]
    return {
        "name": bd["name"],
        "testament": bd["testament"],
        "chapters": bd["chapters"],
        "book_number": BOOK_ORDER[bd["name"]],
        "original_language": "Hebrew" if bd["testament"] == "OT" else "Greek",
    }


def get_all_books() -> list[dict]:
    """Return metadata for all Bible books."""
    return [get_book_metadata(bd["name"]) for bd in BOOK_DATA]
