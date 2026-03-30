"""Shared root word / lexeme cross-reference search."""

from __future__ import annotations

from ..db import queries
from ..references.parser import (
    BOOK_ORDER,
    VerseRef,
    parse_reference,
    _BOOK_META,
)


async def search_by_root(
    strongs: str,
    book: str | None = None,
    testament: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict:
    """Find verses that share a given lexeme/root (by Strong's number).

    Optionally filter by book name or testament (OT/NT).
    """
    total = await queries.count_words_by_strongs(strongs)
    occurrences = await queries.get_words_by_strongs(strongs, limit=500, offset=0)

    # Apply filters
    filtered = occurrences
    if book:
        filtered = [o for o in filtered if o["book_name"].lower() == book.lower()]
    if testament:
        filtered = [
            o for o in filtered
            if _BOOK_META.get(o["book_name"], {}).get("testament") == testament.upper()
        ]

    # Deduplicate to verse level
    seen_verses: set[str] = set()
    verse_results = []
    for occ in filtered:
        ref_key = f"{occ['book_name']} {occ['chapter']}:{occ['verse']}"
        if ref_key not in seen_verses:
            seen_verses.add(ref_key)
            verse_results.append({
                "reference": ref_key,
                "book": occ["book_name"],
                "chapter": occ["chapter"],
                "verse": occ["verse"],
                "word_form": occ["text_original"],
                "morphology_code": occ.get("morphology_code", ""),
            })

    # Apply pagination to deduped results
    paginated = verse_results[offset:offset + limit]

    # Get lexeme info
    lexeme = await queries.get_lexeme(strongs)

    return {
        "strongs": strongs,
        "lexeme": lexeme.get("word", "") if lexeme else "",
        "gloss": lexeme.get("gloss", "") if lexeme else "",
        "total_occurrences": total,
        "unique_verses": len(verse_results),
        "verses": paginated,
        "filters_applied": {
            "book": book,
            "testament": testament,
        },
        "pagination": {
            "limit": limit,
            "offset": offset,
        },
    }


async def find_shared_roots(reference: str) -> dict:
    """Given a verse, find key words and other verses sharing those roots."""
    ref = parse_reference(reference)
    v = ref.start

    verse_row = await queries.get_verse(v.book_number, v.chapter, v.verse)
    if not verse_row:
        return {"error": f"Verse not found: {reference}", "results": []}

    words = await queries.get_words_for_verse(verse_row["id"])

    results = []
    for w in words:
        if not w.get("strongs"):
            continue
        count = await queries.count_words_by_strongs(w["strongs"])
        if count > 1:  # Only include words that appear elsewhere
            results.append({
                "word": w["text_original"],
                "strongs": w["strongs"],
                "gloss": w.get("gloss", ""),
                "total_occurrences": count,
            })

    return {
        "source": str(v),
        "key_words": results,
    }
