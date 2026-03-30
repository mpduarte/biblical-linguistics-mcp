"""MCP tool implementations for translation comparison."""

from __future__ import annotations

from ..db import queries
from ..references.parser import parse_reference


AVAILABLE_VERSIONS = ["kjv", "asv", "web"]


async def compare_translations(
    reference: str,
    versions: list[str] | None = None,
) -> dict:
    """Show a verse across multiple translations."""
    ref = parse_reference(reference)
    v = ref.start

    verse_row = await queries.get_verse_text(v.book_number, v.chapter, v.verse)
    if not verse_row:
        return {"error": f"Verse not found: {reference}"}

    if versions is None:
        versions = AVAILABLE_VERSIONS

    translations = {}
    version_map = {
        "kjv": "text_kjv",
        "asv": "text_asv",
        "web": "text_web",
    }

    for ver in versions:
        ver_lower = ver.lower()
        col = version_map.get(ver_lower)
        if col and verse_row.get(col):
            translations[ver_lower] = verse_row[col]
        else:
            translations[ver_lower] = None

    return {
        "reference": str(v),
        "book": v.book,
        "chapter": v.chapter,
        "verse": v.verse,
        "translations": translations,
        "original_text": verse_row.get("text_original", ""),
    }
