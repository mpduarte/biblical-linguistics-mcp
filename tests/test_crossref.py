"""Tests for cross-reference modules."""

import pytest

from biblical_linguistics_mcp.crossref.tsk import get_tsk_references
from biblical_linguistics_mcp.crossref.thematic import search_by_topic
from biblical_linguistics_mcp.crossref.root_search import search_by_root, find_shared_roots
from biblical_linguistics_mcp.crossref.lxx import get_lxx_for_hebrew_verse, get_hebrew_for_lxx_word, lxx_alignment


class TestTSK:
    @pytest.mark.asyncio
    async def test_get_crossrefs_genesis(self):
        result = await get_tsk_references("Genesis 1:1")
        assert result["source"] == "Genesis 1:1"
        assert result["total"] > 0
        refs = [cr["reference"] for cr in result["cross_references"]]
        assert any("John 1:1" in r for r in refs)

    @pytest.mark.asyncio
    async def test_get_crossrefs_john(self):
        result = await get_tsk_references("John 1:1")
        assert result["total"] > 0

    @pytest.mark.asyncio
    async def test_crossrefs_structure(self):
        result = await get_tsk_references("Genesis 1:1")
        for cr in result["cross_references"]:
            assert "reference" in cr
            assert "book" in cr
            assert "chapter" in cr
            assert "verse" in cr


class TestThematic:
    @pytest.mark.asyncio
    async def test_search_by_topic(self):
        result = await search_by_topic("Creation")
        assert result["total_topics"] > 0
        assert result["topics_found"][0]["topic"] == "Creation"

    @pytest.mark.asyncio
    async def test_search_no_results(self):
        result = await search_by_topic("xyznonexistent")
        assert result["total_topics"] == 0

    @pytest.mark.asyncio
    async def test_search_love(self):
        result = await search_by_topic("Love")
        assert result["total_topics"] > 0


class TestRootSearch:
    @pytest.mark.asyncio
    async def test_search_by_strongs(self):
        result = await search_by_root("G3056")
        assert result["strongs"] == "G3056"
        assert result["total_occurrences"] > 0

    @pytest.mark.asyncio
    async def test_search_by_strongs_hebrew(self):
        result = await search_by_root("H430")
        assert result["total_occurrences"] > 0

    @pytest.mark.asyncio
    async def test_find_shared_roots(self):
        result = await find_shared_roots("Genesis 1:1")
        assert "key_words" in result
        assert len(result["key_words"]) > 0


class TestLXX:
    @pytest.mark.asyncio
    async def test_hebrew_to_lxx(self):
        result = await get_lxx_for_hebrew_verse("Genesis 1:1")
        assert result["direction"] == "hebrew_to_lxx"
        assert result["total"] > 0
        # Check known alignment
        words = {a["hebrew_strongs"]: a["lxx_word"] for a in result["alignments"]}
        assert "H430" in words
        assert "θεός" in words["H430"]

    @pytest.mark.asyncio
    async def test_lxx_to_hebrew(self):
        result = await get_hebrew_for_lxx_word("G2316")
        assert result["direction"] == "lxx_to_hebrew"
        assert result["total_alignments"] > 0

    @pytest.mark.asyncio
    async def test_lxx_nt_verse_rejected(self):
        result = await get_lxx_for_hebrew_verse("John 1:1")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_lxx_alignment_dispatch(self):
        result = await lxx_alignment("Genesis 1:1", "hebrew_to_lxx")
        assert result["direction"] == "hebrew_to_lxx"

        result2 = await lxx_alignment("G2316", "lxx_to_hebrew")
        assert result2["direction"] == "lxx_to_hebrew"

    @pytest.mark.asyncio
    async def test_lxx_invalid_direction(self):
        result = await lxx_alignment("Gen 1:1", "invalid")
        assert "error" in result
