"""MCP tool implementations for cross-references."""

from __future__ import annotations

from ..crossref.tsk import get_tsk_references
from ..crossref.thematic import search_by_topic, get_thematic_crossrefs
from ..crossref.root_search import search_by_root, find_shared_roots
from ..crossref.lxx import lxx_alignment as _lxx_alignment


async def cross_reference_tsk(reference: str) -> dict:
    """TSK cross-references for a verse."""
    return await get_tsk_references(reference)


async def cross_reference_thematic(
    reference: str | None = None,
    topic: str | None = None,
) -> dict:
    """Topical/thematic related passages."""
    if topic:
        return await search_by_topic(topic)
    if reference:
        return await get_thematic_crossrefs(reference)
    return {"error": "Either 'reference' or 'topic' must be provided."}


async def search_by_root_tool(
    strongs: str,
    book: str | None = None,
    testament: str | None = None,
) -> dict:
    """Find verses sharing a lexeme/root."""
    return await search_by_root(strongs, book=book, testament=testament)


async def lxx_alignment(reference: str, direction: str) -> dict:
    """Show LXX Greek for a Hebrew verse or vice versa."""
    return await _lxx_alignment(reference, direction)
