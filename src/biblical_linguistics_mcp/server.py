"""MCP server setup — tools, resources, and prompts."""

from __future__ import annotations

import json
import logging
from typing import Any

from mcp.server import Server
from mcp.types import (
    TextContent,
    Tool,
    Resource,
    ResourceTemplate,
    Prompt,
    PromptArgument,
    PromptMessage,
    GetPromptResult,
)

from .references.parser import (
    get_all_books,
    get_book_metadata,
    ReferenceError as RefError,
)
from .morphology.hebrew import MORPHOLOGY_REFERENCE as HEBREW_MORPH_REF
from .morphology.greek import MORPHOLOGY_REFERENCE as GREEK_MORPH_REF
from .tools.word_tools import (
    parse_verse,
    lookup_word,
    reverse_lookup,
    word_frequency,
)
from .tools.crossref_tools import (
    cross_reference_tsk,
    cross_reference_thematic,
    search_by_root_tool,
    lxx_alignment,
)
from .tools.translation_tools import compare_translations
from .lexicon.hebrew import get_hebrew_entry
from .lexicon.greek import get_greek_entry
from .db import queries

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Server instance
# ---------------------------------------------------------------------------

server = Server("biblical-linguistics-mcp")


def _json_response(data: Any) -> list[TextContent]:
    """Wrap a dict/list as a JSON TextContent response."""
    return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]


def _error_response(msg: str) -> list[TextContent]:
    return _json_response({"error": msg})


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS: list[Tool] = [
    Tool(
        name="parse_verse",
        description="Return all words with full morphological parsing for a Bible verse",
        inputSchema={
            "type": "object",
            "properties": {
                "reference": {
                    "type": "string",
                    "description": "Bible verse reference, e.g. 'John 1:1', 'Genesis 1:1'",
                },
            },
            "required": ["reference"],
        },
    ),
    Tool(
        name="lookup_word",
        description="Full lexical entry by Strong's number (e.g. H7225, G3056)",
        inputSchema={
            "type": "object",
            "properties": {
                "strongs": {
                    "type": "string",
                    "description": "Strong's number, e.g. 'G3056' or 'H7225'",
                },
                "include_occurrences": {
                    "type": "boolean",
                    "description": "Include list of verse occurrences (default false)",
                    "default": False,
                },
            },
            "required": ["strongs"],
        },
    ),
    Tool(
        name="reverse_lookup",
        description="English word to possible Hebrew/Greek lexemes reverse lookup",
        inputSchema={
            "type": "object",
            "properties": {
                "english_word": {
                    "type": "string",
                    "description": "English word to look up",
                },
                "testament": {
                    "type": "string",
                    "enum": ["OT", "NT"],
                    "description": "Filter by testament (optional)",
                },
            },
            "required": ["english_word"],
        },
    ),
    Tool(
        name="search_by_root",
        description="Find verses sharing a lexeme/root by Strong's number",
        inputSchema={
            "type": "object",
            "properties": {
                "strongs": {
                    "type": "string",
                    "description": "Strong's number to search for",
                },
                "book": {
                    "type": "string",
                    "description": "Filter by book name (optional)",
                },
                "testament": {
                    "type": "string",
                    "enum": ["OT", "NT"],
                    "description": "Filter by testament (optional)",
                },
            },
            "required": ["strongs"],
        },
    ),
    Tool(
        name="cross_reference_tsk",
        description="Get Treasury of Scripture Knowledge cross-references for a verse",
        inputSchema={
            "type": "object",
            "properties": {
                "reference": {
                    "type": "string",
                    "description": "Bible verse reference",
                },
            },
            "required": ["reference"],
        },
    ),
    Tool(
        name="cross_reference_thematic",
        description="Find topical/thematic related passages by reference or topic keyword",
        inputSchema={
            "type": "object",
            "properties": {
                "reference": {
                    "type": "string",
                    "description": "Bible verse reference (optional if topic provided)",
                },
                "topic": {
                    "type": "string",
                    "description": "Topic keyword to search (optional if reference provided)",
                },
            },
        },
    ),
    Tool(
        name="lxx_alignment",
        description="Show LXX Greek for a Hebrew verse or find Hebrew source for LXX Greek word",
        inputSchema={
            "type": "object",
            "properties": {
                "reference": {
                    "type": "string",
                    "description": "Hebrew verse reference (for hebrew_to_lxx) or Greek Strong's number (for lxx_to_hebrew)",
                },
                "direction": {
                    "type": "string",
                    "enum": ["hebrew_to_lxx", "lxx_to_hebrew"],
                    "description": "Direction of alignment lookup",
                },
            },
            "required": ["reference", "direction"],
        },
    ),
    Tool(
        name="word_frequency",
        description="Get frequency and distribution statistics for a lexeme by Strong's number",
        inputSchema={
            "type": "object",
            "properties": {
                "strongs": {
                    "type": "string",
                    "description": "Strong's number, e.g. 'G3056' or 'H7225'",
                },
            },
            "required": ["strongs"],
        },
    ),
    Tool(
        name="compare_translations",
        description="Show a verse across multiple Bible translations (KJV, ASV, WEB)",
        inputSchema={
            "type": "object",
            "properties": {
                "reference": {
                    "type": "string",
                    "description": "Bible verse reference",
                },
                "versions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of version codes (kjv, asv, web). Defaults to all.",
                },
            },
            "required": ["reference"],
        },
    ),
]


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return TOOL_DEFINITIONS


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any] | None) -> list[TextContent]:
    arguments = arguments or {}
    try:
        if name == "parse_verse":
            result = await parse_verse(arguments["reference"])
        elif name == "lookup_word":
            result = await lookup_word(
                arguments["strongs"],
                include_occurrences=arguments.get("include_occurrences", False),
            )
        elif name == "reverse_lookup":
            result = await reverse_lookup(
                arguments["english_word"],
                testament=arguments.get("testament"),
            )
        elif name == "search_by_root":
            result = await search_by_root_tool(
                arguments["strongs"],
                book=arguments.get("book"),
                testament=arguments.get("testament"),
            )
        elif name == "cross_reference_tsk":
            result = await cross_reference_tsk(arguments["reference"])
        elif name == "cross_reference_thematic":
            result = await cross_reference_thematic(
                reference=arguments.get("reference"),
                topic=arguments.get("topic"),
            )
        elif name == "lxx_alignment":
            result = await lxx_alignment(
                arguments["reference"],
                arguments["direction"],
            )
        elif name == "word_frequency":
            result = await word_frequency(arguments["strongs"])
        elif name == "compare_translations":
            result = await compare_translations(
                arguments["reference"],
                versions=arguments.get("versions"),
            )
        else:
            return _error_response(f"Unknown tool: {name}")

        return _json_response(result)

    except RefError as e:
        return _error_response(f"Invalid reference: {e}")
    except Exception as e:
        logger.exception("Tool %s failed", name)
        return _error_response(f"Internal error in tool '{name}': {e}")


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

@server.list_resources()
async def handle_list_resources() -> list[Resource]:
    return [
        Resource(
            uri="bible://books",
            name="Bible Books",
            description="List of all Bible books with metadata (testament, chapter count, original language)",
            mimeType="application/json",
        ),
        Resource(
            uri="bible://morphology-codes",
            name="Morphology Code Reference",
            description="Reference table explaining all Hebrew and Greek morphology code abbreviations",
            mimeType="application/json",
        ),
    ]


@server.list_resource_templates()
async def handle_list_resource_templates() -> list[ResourceTemplate]:
    return [
        ResourceTemplate(
            uriTemplate="bible://lexicon/hebrew/{strongs}",
            name="Hebrew Lexical Entry",
            description="Full Hebrew lexical entry by Strong's number",
            mimeType="application/json",
        ),
        ResourceTemplate(
            uriTemplate="bible://lexicon/greek/{strongs}",
            name="Greek Lexical Entry",
            description="Full Greek lexical entry by Strong's number",
            mimeType="application/json",
        ),
        ResourceTemplate(
            uriTemplate="bible://verse/{reference}",
            name="Verse Text",
            description="Verse text in available translations",
            mimeType="application/json",
        ),
    ]


@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    uri_str = str(uri)
    try:
        if uri_str == "bible://books":
            data = get_all_books()
            return json.dumps(data, ensure_ascii=False, indent=2)

        if uri_str == "bible://morphology-codes":
            data = {
                "hebrew": HEBREW_MORPH_REF,
                "greek": GREEK_MORPH_REF,
            }
            return json.dumps(data, ensure_ascii=False, indent=2)

        if uri_str.startswith("bible://lexicon/hebrew/"):
            strongs = uri_str.split("/")[-1]
            entry = await get_hebrew_entry(strongs)
            if not entry:
                return json.dumps({"error": f"Hebrew lexeme not found: {strongs}"})
            return json.dumps(entry, ensure_ascii=False, indent=2)

        if uri_str.startswith("bible://lexicon/greek/"):
            strongs = uri_str.split("/")[-1]
            entry = await get_greek_entry(strongs)
            if not entry:
                return json.dumps({"error": f"Greek lexeme not found: {strongs}"})
            return json.dumps(entry, ensure_ascii=False, indent=2)

        if uri_str.startswith("bible://verse/"):
            reference = uri_str[len("bible://verse/"):]
            from .references.parser import parse_reference
            ref = parse_reference(reference)
            v = ref.start
            verse_data = await queries.get_verse_text(v.book_number, v.chapter, v.verse)
            if not verse_data:
                return json.dumps({"error": f"Verse not found: {reference}"})
            return json.dumps(dict(verse_data), ensure_ascii=False, indent=2)

        return json.dumps({"error": f"Unknown resource URI: {uri_str}"})

    except Exception as e:
        logger.exception("Resource read failed for %s", uri_str)
        return json.dumps({"error": str(e)})


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

@server.list_prompts()
async def handle_list_prompts() -> list[Prompt]:
    return [
        Prompt(
            name="word_study",
            description="Guided word study: gathers lexical data, morphology, occurrences, and cross-references for a comprehensive word study report",
            arguments=[
                PromptArgument(name="strongs", description="Strong's number (e.g. G3056, H7225)", required=True),
                PromptArgument(name="depth", description="'brief' or 'full' (default: full)", required=False),
            ],
        ),
        Prompt(
            name="passage_exegesis",
            description="Exegetical analysis: parses all words in a passage, identifies key terms, pulls cross-references, and frames an exegetical outline",
            arguments=[
                PromptArgument(name="reference", description="Bible reference, can be a range like 'Romans 8:28-30'", required=True),
            ],
        ),
        Prompt(
            name="trace_theme",
            description="Trace a theological theme across both testaments using topical index and lexeme search",
            arguments=[
                PromptArgument(name="topic", description="Theological theme or topic keyword", required=True),
            ],
        ),
        Prompt(
            name="lxx_quotation_analysis",
            description="For NT passages quoting the OT: align NT Greek with LXX Greek and underlying Hebrew to analyze the quotation method",
            arguments=[
                PromptArgument(name="nt_reference", description="New Testament verse reference", required=True),
                PromptArgument(name="ot_reference", description="Old Testament verse reference being quoted", required=True),
            ],
        ),
    ]


@server.get_prompt()
async def handle_get_prompt(name: str, arguments: dict[str, str] | None) -> GetPromptResult:
    arguments = arguments or {}

    if name == "word_study":
        return await _prompt_word_study(arguments)
    elif name == "passage_exegesis":
        return await _prompt_passage_exegesis(arguments)
    elif name == "trace_theme":
        return await _prompt_trace_theme(arguments)
    elif name == "lxx_quotation_analysis":
        return await _prompt_lxx_quotation_analysis(arguments)
    else:
        return GetPromptResult(
            description=f"Unknown prompt: {name}",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(type="text", text=f"Error: Unknown prompt '{name}'"),
                )
            ],
        )


async def _prompt_word_study(args: dict[str, str]) -> GetPromptResult:
    strongs = args.get("strongs", "")
    depth = args.get("depth", "full")

    # Gather data using tools
    lexical_data = await lookup_word(strongs, include_occurrences=(depth == "full"))
    freq_data = await word_frequency(strongs)

    # Build cross-reference sample if we have occurrences
    crossref_sample = {}
    if "occurrences" in lexical_data and lexical_data["occurrences"]:
        first_ref = lexical_data["occurrences"][0]["reference"]
        crossref_sample = await cross_reference_tsk(first_ref)

    prompt_text = f"""# Word Study: {strongs}

## Lexical Data
{json.dumps(lexical_data, ensure_ascii=False, indent=2)}

## Frequency Analysis
{json.dumps(freq_data, ensure_ascii=False, indent=2)}

## Cross-Reference Sample
{json.dumps(crossref_sample, ensure_ascii=False, indent=2)}

---

Please provide a comprehensive word study analysis covering:
1. **Etymology & Root Meaning**: Analyze the root form and its semantic range
2. **Usage Distribution**: Comment on where and how frequently this word appears
3. **Key Occurrences**: Highlight the most theologically significant uses
4. **Semantic Field**: Related words and synonyms in the original language
5. **Translation Considerations**: How different translations render this word
{"6. **Theological Significance**: Major theological themes this word contributes to" if depth == "full" else ""}
"""

    return GetPromptResult(
        description=f"Word study for {strongs}",
        messages=[
            PromptMessage(
                role="user",
                content=TextContent(type="text", text=prompt_text),
            )
        ],
    )


async def _prompt_passage_exegesis(args: dict[str, str]) -> GetPromptResult:
    reference = args.get("reference", "")

    # Parse all words
    verse_data = await parse_verse(reference)

    # Get cross-references
    crossrefs = await cross_reference_tsk(reference)

    prompt_text = f"""# Passage Exegesis: {reference}

## Parsed Text with Morphology
{json.dumps(verse_data, ensure_ascii=False, indent=2)}

## Treasury of Scripture Knowledge Cross-References
{json.dumps(crossrefs, ensure_ascii=False, indent=2)}

---

Please provide an exegetical analysis covering:
1. **Text & Translation**: Original language text with literal translation notes
2. **Grammatical Analysis**: Key morphological observations that affect interpretation
3. **Key Terms**: Identify the most important words and their semantic significance
4. **Cross-References**: How the TSK cross-references illuminate this passage
5. **Exegetical Outline**: Structure the passage's argument or narrative flow
6. **Interpretive Notes**: Important exegetical observations and potential interpretive issues
"""

    return GetPromptResult(
        description=f"Passage exegesis for {reference}",
        messages=[
            PromptMessage(
                role="user",
                content=TextContent(type="text", text=prompt_text),
            )
        ],
    )


async def _prompt_trace_theme(args: dict[str, str]) -> GetPromptResult:
    topic = args.get("topic", "")

    # Search topical index
    thematic_data = await cross_reference_thematic(topic=topic)

    # Also do reverse lookup for key terms
    reverse_data = await reverse_lookup(topic)

    prompt_text = f"""# Tracing Theme: {topic}

## Topical Index Results
{json.dumps(thematic_data, ensure_ascii=False, indent=2)}

## Related Hebrew/Greek Terms
{json.dumps(reverse_data, ensure_ascii=False, indent=2)}

---

Please trace this theological theme across both testaments:
1. **Key Terms**: Hebrew and Greek vocabulary used to express this theme
2. **Old Testament Development**: How this theme unfolds in the OT
3. **Intertestamental Development**: Any shifts in understanding
4. **New Testament Fulfillment/Development**: How NT authors use and develop this theme
5. **Key Passages**: The most important passages for understanding this theme
6. **Theological Synthesis**: Summarize the biblical theology of this theme
"""

    return GetPromptResult(
        description=f"Theme trace: {topic}",
        messages=[
            PromptMessage(
                role="user",
                content=TextContent(type="text", text=prompt_text),
            )
        ],
    )


async def _prompt_lxx_quotation_analysis(args: dict[str, str]) -> GetPromptResult:
    nt_ref = args.get("nt_reference", "")
    ot_ref = args.get("ot_reference", "")

    # Parse both passages
    nt_data = await parse_verse(nt_ref)
    ot_data = await parse_verse(ot_ref)

    # Get LXX alignment for the OT verse
    lxx_data = await lxx_alignment(ot_ref, "hebrew_to_lxx")

    prompt_text = f"""# LXX Quotation Analysis

## NT Passage: {nt_ref}
{json.dumps(nt_data, ensure_ascii=False, indent=2)}

## OT Source: {ot_ref}
{json.dumps(ot_data, ensure_ascii=False, indent=2)}

## LXX Alignment for OT Verse
{json.dumps(lxx_data, ensure_ascii=False, indent=2)}

---

Please analyze this NT quotation of the OT:
1. **Hebrew Text**: Original Hebrew with key vocabulary
2. **LXX Rendering**: How the Septuagint translators rendered the Hebrew
3. **NT Quotation**: How the NT author quotes this passage
4. **Comparison**: Word-by-word comparison of Hebrew → LXX → NT Greek
5. **Quotation Method**: Does the NT follow the LXX, the Hebrew, or a modified version?
6. **Theological Implications**: How do any differences affect the theological argument?
"""

    return GetPromptResult(
        description=f"LXX quotation analysis: {nt_ref} quoting {ot_ref}",
        messages=[
            PromptMessage(
                role="user",
                content=TextContent(type="text", text=prompt_text),
            )
        ],
    )
