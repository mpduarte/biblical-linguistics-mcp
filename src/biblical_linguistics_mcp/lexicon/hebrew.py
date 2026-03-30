"""Hebrew lexicon access (BDB / Strong's)."""

from __future__ import annotations

from ..db import queries


async def get_hebrew_entry(strongs: str) -> dict | None:
    """Get a full Hebrew lexical entry by Strong's number."""
    if not strongs.startswith("H"):
        strongs = f"H{strongs}"
    entry = await queries.get_lexeme(strongs)
    if not entry:
        return None
    # Add frequency breakdown
    freq_data = await queries.get_lexeme_frequency_by_book(strongs)
    entry["frequency_by_book"] = freq_data
    return entry


async def search_hebrew_by_english(english_word: str) -> list[dict]:
    """Reverse lookup: English word -> Hebrew lexemes."""
    return await queries.search_lexemes_by_gloss(english_word, language="Hebrew")
