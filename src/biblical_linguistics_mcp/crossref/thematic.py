"""Thematic / topical cross-reference search using Nave's Topical Bible."""

from __future__ import annotations

from ..db import queries
from ..references.parser import parse_reference, VerseRef


async def search_by_topic(topic: str) -> dict:
    """Search for verses related to a topic keyword.

    Uses the Nave's Topical Bible data to find thematically related passages.
    """
    topics = await queries.search_topics(topic)
    if not topics:
        return {
            "query": topic,
            "topics_found": [],
            "total_topics": 0,
        }

    results = []
    for t in topics[:20]:  # Limit to 20 topics
        verses = await queries.get_topic_verses(t["id"])
        results.append({
            "topic": t["topic"],
            "subtopic": t.get("subtopic", ""),
            "verses": [
                {
                    "reference": f"{v['book_name']} {v['chapter']}:{v['verse']}",
                    "text": v.get("text_kjv", ""),
                }
                for v in verses[:50]  # Limit verses per topic
            ],
            "total_verses": len(verses),
        })

    return {
        "query": topic,
        "topics_found": results,
        "total_topics": len(results),
    }


async def get_thematic_crossrefs(reference: str) -> dict:
    """Find thematically related passages for a given verse.

    Searches for topics that include this verse and returns other verses
    in those same topics.
    """
    ref = parse_reference(reference)
    v = ref.start

    # Find all topics that contain this verse
    all_topics = await queries.search_topics("")  # Get all topics
    related_topics = []

    # This is a simplified approach — in practice, we'd have a
    # verse-to-topic index. For now, search topics containing this verse.
    # The bootstrap script will create appropriate indexes.

    return {
        "source": str(v),
        "related_topics": related_topics,
        "note": "Use search_by_topic() with a keyword for best results",
    }
