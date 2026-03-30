"""LXX (Septuagint) alignment — Hebrew to Greek and vice versa."""

from __future__ import annotations

from ..db import queries
from ..references.parser import parse_reference


async def get_lxx_for_hebrew_verse(reference: str) -> dict:
    """Show the LXX Greek rendering for a Hebrew OT verse."""
    ref = parse_reference(reference)
    v = ref.start

    if v.testament != "OT":
        return {
            "error": "LXX alignment is only available for Old Testament verses",
            "reference": str(v),
        }

    alignments = await queries.get_lxx_alignment_for_verse(
        v.book_number, v.chapter, v.verse
    )

    return {
        "reference": str(v),
        "direction": "hebrew_to_lxx",
        "alignments": [
            {
                "hebrew_word": a.get("hebrew_word", ""),
                "hebrew_strongs": a.get("hebrew_strongs", ""),
                "lxx_word": a.get("lxx_word", ""),
                "lxx_strongs": a.get("lxx_strongs", ""),
                "lxx_morphology": a.get("lxx_morphology", ""),
            }
            for a in alignments
        ],
        "total": len(alignments),
    }


async def get_hebrew_for_lxx_word(strongs: str) -> dict:
    """Given a Greek word in the LXX, find the underlying Hebrew source word(s)."""
    if not strongs.startswith("G"):
        strongs = f"G{strongs}"

    alignments = await queries.get_lxx_by_greek_strongs(strongs)

    # Group by Hebrew word
    hebrew_words: dict[str, dict] = {}
    for a in alignments:
        h_strongs = a.get("hebrew_strongs", "")
        if h_strongs not in hebrew_words:
            hebrew_words[h_strongs] = {
                "hebrew_strongs": h_strongs,
                "hebrew_word": a.get("hebrew_word", ""),
                "occurrences": [],
            }
        hebrew_words[h_strongs]["occurrences"].append({
            "reference": f"{a['book_name']} {a['hebrew_chapter']}:{a['hebrew_verse']}",
        })

    return {
        "lxx_strongs": strongs,
        "direction": "lxx_to_hebrew",
        "hebrew_sources": list(hebrew_words.values()),
        "total_alignments": len(alignments),
    }


async def lxx_alignment(reference: str, direction: str) -> dict:
    """Dispatch to the appropriate LXX alignment function."""
    if direction == "hebrew_to_lxx":
        return await get_lxx_for_hebrew_verse(reference)
    elif direction == "lxx_to_hebrew":
        # For lxx_to_hebrew, reference is treated as a Strong's number
        return await get_hebrew_for_lxx_word(reference)
    else:
        return {"error": f"Invalid direction: {direction}. Use 'hebrew_to_lxx' or 'lxx_to_hebrew'"}
