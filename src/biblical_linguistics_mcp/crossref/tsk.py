"""Treasury of Scripture Knowledge cross-reference lookups."""

from __future__ import annotations

from ..db import queries
from ..references.parser import VerseRef, parse_reference


async def get_tsk_references(reference: str) -> dict:
    """Get TSK cross-references for a verse reference.

    Returns a dict with the source verse info and list of cross-references,
    each including the target reference and verse text.
    """
    ref = parse_reference(reference)
    v = ref.start

    crossrefs = await queries.get_tsk_crossrefs(v.book_number, v.chapter, v.verse)

    results = []
    for cr in crossrefs:
        results.append({
            "reference": f"{cr['target_book_name']} {cr['target_chapter']}:{cr['target_verse']}",
            "book": cr["target_book_name"],
            "chapter": cr["target_chapter"],
            "verse": cr["target_verse"],
            "text": cr.get("target_text", ""),
        })

    return {
        "source": str(v),
        "source_book": v.book,
        "source_chapter": v.chapter,
        "source_verse": v.verse,
        "cross_references": results,
        "total": len(results),
    }
