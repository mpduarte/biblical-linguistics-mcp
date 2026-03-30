"""Greek lexicon access (Thayer's / Dodson / Strong's)."""

from __future__ import annotations

from ..db import queries


async def get_greek_entry(strongs: str) -> dict | None:
    """Get a full Greek lexical entry by Strong's number."""
    if not strongs.startswith("G"):
        strongs = f"G{strongs}"
    entry = await queries.get_lexeme(strongs)
    if not entry:
        return None
    freq_data = await queries.get_lexeme_frequency_by_book(strongs)
    entry["frequency_by_book"] = freq_data
    return entry


async def search_greek_by_english(english_word: str) -> list[dict]:
    """Reverse lookup: English word -> Greek lexemes."""
    return await queries.search_lexemes_by_gloss(english_word, language="Greek")
