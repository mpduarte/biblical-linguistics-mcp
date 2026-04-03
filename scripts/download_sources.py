#!/usr/bin/env python3
"""Download raw data sources for the Biblical Linguistics MCP server.

All sources are free / public domain / openly licensed.
This script handles only the download step — parsing is in bootstrap.py.
"""

from __future__ import annotations

import os
import sys
import json
import zipfile
import io
from pathlib import Path

import httpx

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

# ---------------------------------------------------------------------------
# Data source URLs
# ---------------------------------------------------------------------------

SOURCES = {
    # OSHB — Open Scriptures Hebrew Bible (morphology + text)
    "oshb": {
        "url": "https://raw.githubusercontent.com/openscriptures/morphhb/master/wlc/ruth.xml",
        "description": "OSHB Hebrew Bible sample (Ruth) for morphology data",
        "filename": "oshb_ruth.xml",
    },
    # Strong's Hebrew dictionary (public domain JSON)
    "strongs_hebrew": {
        "url": "https://raw.githubusercontent.com/openscriptures/HebrewLexicon/master/HebrewStrong.xml",
        "description": "Strong's Hebrew Dictionary (Open Scriptures)",
        "filename": "HebrewStrong.xml",
    },
    # Dodson Greek lexicon
    "strongs_greek": {
        "url": "https://raw.githubusercontent.com/openscriptures/GreekLexicon/master/dodson/greek.json",
        "description": "Dodson Greek Lexicon (Open Scriptures)",
        "filename": "dodson_greek.json",
    },
    # Berean Interlinear Bible — Greek NT morphology (public domain)
    "berean_greek": {
        "url": "https://raw.githubusercontent.com/bereaninterlinear/berean-interlinear-bible/main/data/berean_interlinear.json",
        "description": "Berean Interlinear Greek NT data",
        "filename": "berean_interlinear.json",
    },
    # Treasury of Scripture Knowledge — cross-references
    "tsk": {
        "url": "https://raw.githubusercontent.com/scrollmapper/bible_databases/master/json/cross_references.json",
        "description": "Treasury of Scripture Knowledge cross-references (JSON)",
        "filename": "cross_references.json",
    },
    # KJV Bible text
    "kjv": {
        "url": "https://raw.githubusercontent.com/scrollmapper/bible_databases/master/json/t_kjv.json",
        "description": "King James Version (public domain)",
        "filename": "t_kjv.json",
    },
    # ASV Bible text
    "asv": {
        "url": "https://raw.githubusercontent.com/scrollmapper/bible_databases/master/json/t_asv.json",
        "description": "American Standard Version (public domain)",
        "filename": "t_asv.json",
    },
    # WEB Bible text
    "web": {
        "url": "https://raw.githubusercontent.com/scrollmapper/bible_databases/master/json/t_web.json",
        "description": "World English Bible (public domain)",
        "filename": "t_web.json",
    },
    # Bible book/key data
    "books": {
        "url": "https://raw.githubusercontent.com/scrollmapper/bible_databases/master/json/key_english.json",
        "description": "Bible books metadata",
        "filename": "key_english.json",
    },
    # Strong's numbers linked to verses (scrollmapper)
    # Optional — bootstrap.py skips gracefully if missing
    "strongs_verses": {
        "url": "https://raw.githubusercontent.com/scrollmapper/bible_databases/master/json/t_strongs.json",
        "description": "Strong's numbers linked to verses",
        "filename": "t_strongs.json",
        "optional": True,
    },
}


def download_file(name: str, source: dict, force: bool = False) -> bool:
    """Download a single source file. Returns True if downloaded."""
    dest = RAW_DIR / source["filename"]
    if dest.exists() and not force:
        print(f"  [skip] {name}: {dest.name} already exists")
        return False

    print(f"  [downloading] {name}: {source['description']}")
    print(f"    URL: {source['url']}")

    try:
        with httpx.Client(timeout=120.0, follow_redirects=True) as client:
            resp = client.get(source["url"])
            resp.raise_for_status()
            dest.write_bytes(resp.content)
            size_kb = len(resp.content) / 1024
            print(f"    ✓ Downloaded {size_kb:.1f} KB -> {dest.name}")
            return True
    except httpx.HTTPError as e:
        print(f"    ✗ Failed to download {name}: {e}", file=sys.stderr)
        return False


def main() -> None:
    force = "--force" in sys.argv
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Data directory: {RAW_DIR}")
    print(f"Downloading {len(SOURCES)} sources...\n")

    downloaded = 0
    failed = 0
    skipped = 0

    for name, source in SOURCES.items():
        result = download_file(name, source, force=force)
        if result:
            downloaded += 1
        elif (RAW_DIR / source["filename"]).exists():
            skipped += 1
        elif source.get("optional"):
            print(f"  [skip] {name}: optional file unavailable, continuing")
        else:
            failed += 1

    print(f"\nDone: {downloaded} downloaded, {skipped} skipped, {failed} failed")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
