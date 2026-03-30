"""Integration tests for MCP tools."""

import json

import pytest

from biblical_linguistics_mcp.tools.word_tools import (
    parse_verse,
    lookup_word,
    reverse_lookup,
    word_frequency,
)
from biblical_linguistics_mcp.tools.crossref_tools import (
    cross_reference_tsk,
    cross_reference_thematic,
    search_by_root_tool,
    lxx_alignment,
)
from biblical_linguistics_mcp.tools.translation_tools import compare_translations
from biblical_linguistics_mcp.server import handle_call_tool, handle_list_tools


class TestParseVerse:
    @pytest.mark.asyncio
    async def test_genesis_1_1(self):
        result = await parse_verse("Genesis 1:1")
        assert result["reference"] == "Genesis 1:1"
        assert result["testament"] == "OT"
        assert result["word_count"] == 7  # 7 Hebrew words
        # Check first word
        first = result["words"][0]
        assert first["strongs"] == "H7225"
        assert "beginning" in first["gloss"].lower()
        assert first["morphology"]["part_of_speech"] == "noun"

    @pytest.mark.asyncio
    async def test_john_1_1(self):
        result = await parse_verse("John 1:1")
        assert result["reference"] == "John 1:1"
        assert result["testament"] == "NT"
        assert result["word_count"] == 17
        # Check logos
        logos_words = [w for w in result["words"] if w["strongs"] == "G3056"]
        assert len(logos_words) == 3  # logos appears 3 times in John 1:1

    @pytest.mark.asyncio
    async def test_invalid_verse(self):
        result = await parse_verse("Genesis 99:99")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_json_serializable(self):
        result = await parse_verse("Genesis 1:1")
        serialized = json.dumps(result, ensure_ascii=False)
        assert isinstance(serialized, str)
        parsed_back = json.loads(serialized)
        assert parsed_back["reference"] == "Genesis 1:1"


class TestLookupWord:
    @pytest.mark.asyncio
    async def test_hebrew_word(self):
        result = await lookup_word("H7225")
        assert result["strongs"] == "H7225"
        assert result["language"] == "Hebrew"
        assert "beginning" in result["gloss"].lower()

    @pytest.mark.asyncio
    async def test_greek_word(self):
        result = await lookup_word("G3056")
        assert result["strongs"] == "G3056"
        assert result["language"] == "Greek"
        assert "word" in result["gloss"].lower()

    @pytest.mark.asyncio
    async def test_with_occurrences(self):
        result = await lookup_word("G3056", include_occurrences=True)
        assert "occurrences" in result
        assert len(result["occurrences"]) > 0

    @pytest.mark.asyncio
    async def test_invalid_strongs(self):
        result = await lookup_word("X999")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_nonexistent(self):
        result = await lookup_word("H99999")
        assert "error" in result


class TestReverseLookup:
    @pytest.mark.asyncio
    async def test_english_to_hebrew(self):
        result = await reverse_lookup("create", testament="OT")
        assert result["total"] > 0
        strongs = [r["strongs"] for r in result["results"]]
        assert "H1254" in strongs

    @pytest.mark.asyncio
    async def test_english_to_greek(self):
        result = await reverse_lookup("love", testament="NT")
        assert result["total"] > 0

    @pytest.mark.asyncio
    async def test_no_filter(self):
        result = await reverse_lookup("God")
        assert result["total"] > 0


class TestWordFrequency:
    @pytest.mark.asyncio
    async def test_frequency(self):
        result = await word_frequency("H430")
        assert result["strongs"] == "H430"
        assert result["total_occurrences"] > 0

    @pytest.mark.asyncio
    async def test_nonexistent(self):
        result = await word_frequency("H99999")
        assert "error" in result


class TestCrossRefTools:
    @pytest.mark.asyncio
    async def test_tsk(self):
        result = await cross_reference_tsk("Genesis 1:1")
        assert result["total"] > 0

    @pytest.mark.asyncio
    async def test_thematic_by_topic(self):
        result = await cross_reference_thematic(topic="Creation")
        assert result["total_topics"] > 0

    @pytest.mark.asyncio
    async def test_thematic_no_args(self):
        result = await cross_reference_thematic()
        assert "error" in result

    @pytest.mark.asyncio
    async def test_search_by_root(self):
        result = await search_by_root_tool("G2316")
        assert result["total_occurrences"] > 0

    @pytest.mark.asyncio
    async def test_lxx(self):
        result = await lxx_alignment("Genesis 1:1", "hebrew_to_lxx")
        assert result["total"] > 0


class TestCompareTranslations:
    @pytest.mark.asyncio
    async def test_all_versions(self):
        result = await compare_translations("Genesis 1:1")
        assert result["reference"] == "Genesis 1:1"
        assert "kjv" in result["translations"]
        assert "asv" in result["translations"]
        assert "web" in result["translations"]
        assert result["translations"]["kjv"] is not None

    @pytest.mark.asyncio
    async def test_specific_versions(self):
        result = await compare_translations("John 1:1", versions=["kjv", "web"])
        assert "kjv" in result["translations"]
        assert "web" in result["translations"]

    @pytest.mark.asyncio
    async def test_invalid_verse(self):
        result = await compare_translations("Genesis 99:99")
        assert "error" in result


class TestMCPServerTools:
    @pytest.mark.asyncio
    async def test_list_tools(self):
        tools = await handle_list_tools()
        names = [t.name for t in tools]
        assert "parse_verse" in names
        assert "lookup_word" in names
        assert "reverse_lookup" in names
        assert "search_by_root" in names
        assert "cross_reference_tsk" in names
        assert "cross_reference_thematic" in names
        assert "lxx_alignment" in names
        assert "word_frequency" in names
        assert "compare_translations" in names

    @pytest.mark.asyncio
    async def test_call_tool_parse_verse(self):
        result = await handle_call_tool("parse_verse", {"reference": "Genesis 1:1"})
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["reference"] == "Genesis 1:1"

    @pytest.mark.asyncio
    async def test_call_unknown_tool(self):
        result = await handle_call_tool("nonexistent_tool", {})
        data = json.loads(result[0].text)
        assert "error" in data

    @pytest.mark.asyncio
    async def test_call_tool_invalid_ref(self):
        result = await handle_call_tool("parse_verse", {"reference": "Narnia 1:1"})
        data = json.loads(result[0].text)
        assert "error" in data
