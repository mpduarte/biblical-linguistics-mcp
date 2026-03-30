"""Tests for lexicon lookups."""

import pytest

from biblical_linguistics_mcp.lexicon.hebrew import get_hebrew_entry, search_hebrew_by_english
from biblical_linguistics_mcp.lexicon.greek import get_greek_entry, search_greek_by_english


class TestHebrewLexicon:
    @pytest.mark.asyncio
    async def test_get_entry_by_strongs(self):
        entry = await get_hebrew_entry("H7225")
        assert entry is not None
        assert entry["strongs"] == "H7225"
        assert entry["language"] == "Hebrew"
        assert "beginning" in entry["gloss"].lower()

    @pytest.mark.asyncio
    async def test_get_entry_without_prefix(self):
        entry = await get_hebrew_entry("7225")
        assert entry is not None
        assert entry["strongs"] == "H7225"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self):
        entry = await get_hebrew_entry("H99999")
        assert entry is None

    @pytest.mark.asyncio
    async def test_search_by_english(self):
        results = await search_hebrew_by_english("create")
        assert len(results) > 0
        strongs_nums = [r["strongs"] for r in results]
        assert "H1254" in strongs_nums

    @pytest.mark.asyncio
    async def test_frequency_by_book(self):
        entry = await get_hebrew_entry("H430")
        assert entry is not None
        assert "frequency_by_book" in entry


class TestGreekLexicon:
    @pytest.mark.asyncio
    async def test_get_entry_by_strongs(self):
        entry = await get_greek_entry("G3056")
        assert entry is not None
        assert entry["strongs"] == "G3056"
        assert entry["language"] == "Greek"
        assert "word" in entry["gloss"].lower()

    @pytest.mark.asyncio
    async def test_search_by_english(self):
        results = await search_greek_by_english("love")
        assert len(results) > 0
        strongs_nums = [r["strongs"] for r in results]
        assert "G25" in strongs_nums
