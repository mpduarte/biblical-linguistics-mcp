# Biblical Linguistics MCP

A production-quality **Biblical Linguistic Research Agent** exposed as a standalone **MCP (Model Context Protocol) server** in Python. Provides Hebrew & Greek word study, full morphological parsing, cross-references, LXX alignment, and more — all from free, open-licensed data sources.

Usable by any MCP-compatible client: Claude Desktop, Claude Code, OpenClaw, custom agents, etc.

## Quick Start

```bash
# Clone the repo
git clone https://github.com/your-org/biblical-linguistics-mcp.git
cd biblical-linguistics-mcp

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -e ".[dev]"

# Bootstrap the database (downloads open datasets + builds SQLite DB)
python scripts/bootstrap.py

# Run the MCP server (stdio mode for Claude Desktop / Claude Code)
python -m biblical_linguistics_mcp --transport stdio

# Or run in SSE mode for network access
python -m biblical_linguistics_mcp --transport sse --port 8080
```

## Configuration

| Option | CLI Flag | Env Var | Default |
|--------|----------|---------|---------|
| Transport mode | `--transport stdio\|sse` | — | `stdio` |
| SSE port | `--port 8080` | — | `8080` |
| SSE host | `--host 0.0.0.0` | — | `0.0.0.0` |
| Database path | `--db /path/to/db` | `BIBLICAL_LINGUISTICS_DB` | `data/biblical_linguistics.db` |
| Log level | `--log-level DEBUG` | — | `INFO` |

## MCP Integration Examples

### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "biblical-linguistics": {
      "command": "python",
      "args": ["-m", "biblical_linguistics_mcp", "--transport", "stdio"],
      "cwd": "/path/to/biblical-linguistics-mcp"
    }
  }
}
```

### Claude Code

```bash
# Add as MCP server
claude mcp add biblical-linguistics -- python -m biblical_linguistics_mcp --transport stdio
```

### Custom MCP Client (SSE)

```python
from mcp import ClientSession
from mcp.client.sse import sse_client

async with sse_client("http://localhost:8080/sse") as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        result = await session.call_tool("parse_verse", {"reference": "John 1:1"})
        print(result)
```

## Tool Reference

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `parse_verse` | All words with full morphology for a verse | `reference` (str) |
| `lookup_word` | Full lexical entry by Strong's number | `strongs` (str), `include_occurrences` (bool) |
| `reverse_lookup` | English word → Hebrew/Greek lexemes | `english_word` (str), `testament` (OT/NT) |
| `search_by_root` | Find verses sharing a lexeme/root | `strongs` (str), `book` (str), `testament` (str) |
| `cross_reference_tsk` | TSK cross-references for a verse | `reference` (str) |
| `cross_reference_thematic` | Topical/thematic related passages | `reference` (str) or `topic` (str) |
| `lxx_alignment` | LXX Greek ↔ Hebrew alignment | `reference` (str), `direction` (str) |
| `word_frequency` | Frequency and distribution stats | `strongs` (str) |
| `compare_translations` | Verse across KJV, ASV, WEB | `reference` (str), `versions` (list) |

### Example: `parse_verse`

```json
// Request
{"reference": "John 1:1"}

// Response (abbreviated)
{
  "reference": "John 1:1",
  "testament": "NT",
  "text_kjv": "In the beginning was the Word...",
  "words": [
    {
      "position": 1,
      "text": "Ἐν",
      "morphology": {"part_of_speech": "preposition"}
    },
    {
      "position": 2,
      "text": "ἀρχῇ",
      "strongs": "G746",
      "gloss": "beginning, ruler",
      "morphology": {
        "part_of_speech": "noun",
        "case_form": "dative",
        "number": "singular",
        "gender": "feminine"
      }
    }
  ]
}
```

## Resource Reference

| URI Pattern | Description |
|-------------|-------------|
| `bible://books` | All Bible books with metadata |
| `bible://lexicon/hebrew/{strongs}` | Hebrew lexical entry |
| `bible://lexicon/greek/{strongs}` | Greek lexical entry |
| `bible://verse/{reference}` | Verse text in available translations |
| `bible://morphology-codes` | Hebrew & Greek morphology code reference |

## Prompt Reference

| Prompt | Description | Arguments |
|--------|-------------|-----------|
| `word_study` | Comprehensive word study report | `strongs` (required), `depth` (brief/full) |
| `passage_exegesis` | Exegetical analysis of a passage | `reference` (required) |
| `trace_theme` | Trace theme across both testaments | `topic` (required) |
| `lxx_quotation_analysis` | Analyze NT quotation of OT via LXX | `nt_reference`, `ot_reference` |

## Data Sources & Licensing

All data is free and open-licensed:

| Dataset | License | Use |
|---------|---------|-----|
| [Open Scriptures Hebrew Bible (OSHB)](https://github.com/openscriptures/morphhb) | CC BY 4.0 | Hebrew text + morphology |
| [Dodson Greek Lexicon](https://github.com/openscriptures/GreekLexicon) | CC BY-SA 3.0 | Greek lexical data |
| [Open Scriptures Hebrew Lexicon](https://github.com/openscriptures/HebrewLexicon) | CC BY 4.0 | Hebrew lexical data |
| Strong's Concordance | Public Domain | Numbering system, definitions |
| Treasury of Scripture Knowledge | Public Domain | Cross-references |
| King James Version | Public Domain | English Bible text |
| American Standard Version | Public Domain | English Bible text |
| World English Bible | Public Domain | English Bible text |
| [scrollmapper/bible_databases](https://github.com/scrollmapper/bible_databases) | Public Domain | Structured Bible data |

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=biblical_linguistics_mcp --cov-report=term-missing

# Re-download data sources
python scripts/download_sources.py --force

# Re-bootstrap database
python scripts/bootstrap.py
```

### Project Structure

```
src/biblical_linguistics_mcp/
├── __main__.py          # CLI entry point
├── server.py            # MCP server (tools, resources, prompts)
├── db/                  # SQLite schema, connection, queries
├── morphology/          # Hebrew & Greek morphology parsers
├── lexicon/             # Hebrew & Greek lexicon access
├── crossref/            # TSK, thematic, root search, LXX
├── references/          # Bible reference parser
└── tools/               # MCP tool implementations
```

## Requirements

- Python 3.11+
- No paid APIs or API keys required
- ~100 MB disk space for the full database

## License

MIT
