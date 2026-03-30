"""MCP tool implementations for word lookup, morphology, and lexicon."""

from __future__ import annotations

from ..db import queries
from ..lexicon import hebrew as hebrew_lex, greek as greek_lex
from ..morphology.hebrew import parse_hebrew_morphology
from ..morphology.greek import parse_greek_morphology
from ..references.parser import parse_reference, BOOK_ORDER


async def parse_verse(reference: str) -> dict:
    """Return all words with full morphology for a verse."""
    ref = parse_reference(reference)
    v = ref.start

    verse_row = await queries.get_verse(v.book_number, v.chapter, v.verse)
    if not verse_row:
        return {"error": f"Verse not found: {reference}", "words": []}

    words = await queries.get_words_for_verse(verse_row["id"])

    parsed_words = []
    for w in words:
        morph_code = w.get("morphology_code", "") or ""
        # Determine language from Strong's number
        strongs = w.get("strongs", "") or ""
        if strongs.startswith("H"):
            morph = parse_hebrew_morphology(morph_code).to_dict()
        elif strongs.startswith("G"):
            morph = parse_greek_morphology(morph_code).to_dict()
        else:
            morph = {"raw_code": morph_code}

        parsed_words.append({
            "position": w["word_position"],
            "text": w["text_original"],
            "strongs": strongs,
            "transliteration": w.get("transliteration", ""),
            "root_form": w.get("root_form", ""),
            "gloss": w.get("gloss", ""),
            "definition": w.get("definition", ""),
            "frequency": w.get("frequency", 0),
            "morphology": morph,
        })

    return {
        "reference": str(v),
        "book": v.book,
        "chapter": v.chapter,
        "verse": v.verse,
        "testament": v.testament,
        "text_original": verse_row.get("text_original", ""),
        "text_kjv": verse_row.get("text_kjv", ""),
        "words": parsed_words,
        "word_count": len(parsed_words),
    }


async def lookup_word(strongs: str, include_occurrences: bool = False) -> dict:
    """Full lexical entry by Strong's number."""
    strongs = strongs.upper().strip()

    if strongs.startswith("H"):
        entry = await hebrew_lex.get_hebrew_entry(strongs)
    elif strongs.startswith("G"):
        entry = await greek_lex.get_greek_entry(strongs)
    else:
        return {"error": f"Invalid Strong's number format: {strongs}. Must start with H or G."}

    if not entry:
        return {"error": f"Lexeme not found: {strongs}"}

    result = {
        "strongs": entry["strongs"],
        "language": entry["language"],
        "word": entry["word"],
        "transliteration": entry.get("transliteration", ""),
        "root_form": entry.get("root_form", ""),
        "gloss": entry.get("gloss", ""),
        "definition": entry.get("definition", ""),
        "frequency": entry.get("frequency", 0),
        "semantic_domain": entry.get("semantic_domain", ""),
        "frequency_by_book": entry.get("frequency_by_book", []),
    }

    if include_occurrences:
        occurrences = await queries.get_words_by_strongs(strongs, limit=200)
        result["occurrences"] = [
            {
                "reference": f"{o['book_name']} {o['chapter']}:{o['verse']}",
                "word_form": o["text_original"],
                "morphology_code": o.get("morphology_code", ""),
            }
            for o in occurrences
        ]
        result["total_occurrences"] = await queries.count_words_by_strongs(strongs)

    return result


async def reverse_lookup(english_word: str, testament: str | None = None) -> dict:
    """English word -> possible Hebrew/Greek lexemes."""
    language = None
    if testament:
        testament = testament.upper()
        if testament == "OT":
            language = "Hebrew"
        elif testament == "NT":
            language = "Greek"

    if language:
        results = await queries.search_lexemes_by_gloss(english_word, language=language)
    else:
        results = await queries.search_lexemes_by_gloss(english_word)

    return {
        "query": english_word,
        "testament_filter": testament,
        "results": [
            {
                "strongs": r["strongs"],
                "language": r["language"],
                "word": r["word"],
                "transliteration": r.get("transliteration", ""),
                "gloss": r.get("gloss", ""),
                "frequency": r.get("frequency", 0),
            }
            for r in results
        ],
        "total": len(results),
    }


async def word_frequency(strongs: str) -> dict:
    """Frequency and distribution stats for a lexeme."""
    strongs = strongs.upper().strip()
    lexeme = await queries.get_lexeme(strongs)
    if not lexeme:
        return {"error": f"Lexeme not found: {strongs}"}

    freq_by_book = await queries.get_lexeme_frequency_by_book(strongs)
    total = sum(f["occurrences"] for f in freq_by_book)

    ot_count = sum(f["occurrences"] for f in freq_by_book if f["testament"] == "OT")
    nt_count = sum(f["occurrences"] for f in freq_by_book if f["testament"] == "NT")

    return {
        "strongs": strongs,
        "word": lexeme["word"],
        "gloss": lexeme.get("gloss", ""),
        "total_occurrences": total,
        "ot_occurrences": ot_count,
        "nt_occurrences": nt_count,
        "by_book": freq_by_book,
    }
