"""All SQL queries as async functions."""

from __future__ import annotations

from typing import Any

import aiosqlite

from .connection import get_connection


async def _fetch_all(sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    conn = await get_connection()
    try:
        cursor = await conn.execute(sql, params)
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await conn.close()


async def _fetch_one(sql: str, params: tuple = ()) -> dict[str, Any] | None:
    conn = await get_connection()
    try:
        cursor = await conn.execute(sql, params)
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await conn.close()


# --- Verse queries ---

async def get_verse(book_number: int, chapter: int, verse: int) -> dict[str, Any] | None:
    return await _fetch_one(
        "SELECT * FROM verses WHERE book_number = ? AND chapter = ? AND verse = ?",
        (book_number, chapter, verse),
    )


async def get_verses_in_range(
    book_number: int, chapter: int, verse_start: int, verse_end: int
) -> list[dict[str, Any]]:
    return await _fetch_all(
        "SELECT * FROM verses WHERE book_number = ? AND chapter = ? AND verse BETWEEN ? AND ?",
        (book_number, chapter, verse_start, verse_end),
    )


async def get_verse_text(book_number: int, chapter: int, verse: int) -> dict[str, Any] | None:
    return await _fetch_one(
        "SELECT text_original, text_kjv, text_asv, text_web FROM verses "
        "WHERE book_number = ? AND chapter = ? AND verse = ?",
        (book_number, chapter, verse),
    )


# --- Word / morphology queries ---

async def get_words_for_verse(verse_id: int) -> list[dict[str, Any]]:
    return await _fetch_all(
        "SELECT w.*, l.transliteration, l.root_form, l.gloss, l.definition, l.frequency "
        "FROM words w LEFT JOIN lexemes l ON w.strongs = l.strongs "
        "WHERE w.verse_id = ? ORDER BY w.word_position",
        (verse_id,),
    )


async def get_words_by_strongs(strongs: str, limit: int = 500, offset: int = 0) -> list[dict[str, Any]]:
    return await _fetch_all(
        "SELECT w.*, v.book_number, v.chapter, v.verse, b.name AS book_name "
        "FROM words w "
        "JOIN verses v ON w.verse_id = v.id "
        "JOIN books b ON v.book_number = b.book_number "
        "WHERE w.strongs = ? "
        "ORDER BY v.book_number, v.chapter, v.verse, w.word_position "
        "LIMIT ? OFFSET ?",
        (strongs, limit, offset),
    )


async def count_words_by_strongs(strongs: str) -> int:
    result = await _fetch_one(
        "SELECT COUNT(*) as cnt FROM words WHERE strongs = ?", (strongs,)
    )
    return result["cnt"] if result else 0


# --- Lexicon queries ---

async def get_lexeme(strongs: str) -> dict[str, Any] | None:
    return await _fetch_one("SELECT * FROM lexemes WHERE strongs = ?", (strongs,))


async def search_lexemes_by_gloss(english_word: str, language: str | None = None) -> list[dict[str, Any]]:
    if language:
        return await _fetch_all(
            "SELECT * FROM lexemes WHERE gloss LIKE ? AND language = ? ORDER BY frequency DESC",
            (f"%{english_word}%", language),
        )
    return await _fetch_all(
        "SELECT * FROM lexemes WHERE gloss LIKE ? ORDER BY frequency DESC",
        (f"%{english_word}%",),
    )


async def get_lexeme_frequency_by_book(strongs: str) -> list[dict[str, Any]]:
    return await _fetch_all(
        "SELECT b.name AS book_name, b.testament, COUNT(*) AS occurrences "
        "FROM words w "
        "JOIN verses v ON w.verse_id = v.id "
        "JOIN books b ON v.book_number = b.book_number "
        "WHERE w.strongs = ? "
        "GROUP BY b.book_number "
        "ORDER BY b.book_number",
        (strongs,),
    )


# --- Cross-reference queries ---

async def get_tsk_crossrefs(book_number: int, chapter: int, verse: int) -> list[dict[str, Any]]:
    return await _fetch_all(
        "SELECT cr.*, "
        "sb.name AS source_book_name, tb.name AS target_book_name, "
        "tv.text_kjv AS target_text "
        "FROM cross_references cr "
        "JOIN books sb ON cr.source_book = sb.book_number "
        "JOIN books tb ON cr.target_book = tb.book_number "
        "LEFT JOIN verses tv ON cr.target_book = tv.book_number "
        "  AND cr.target_chapter = tv.chapter AND cr.target_verse = tv.verse "
        "WHERE cr.source_book = ? AND cr.source_chapter = ? AND cr.source_verse = ?",
        (book_number, chapter, verse),
    )


# --- Topic queries ---

async def search_topics(keyword: str) -> list[dict[str, Any]]:
    return await _fetch_all(
        "SELECT * FROM topics WHERE topic LIKE ? ORDER BY topic",
        (f"%{keyword}%",),
    )


async def get_topic_verses(topic_id: int) -> list[dict[str, Any]]:
    return await _fetch_all(
        "SELECT tv.*, b.name AS book_name, v.text_kjv "
        "FROM topic_verses tv "
        "JOIN books b ON tv.book_number = b.book_number "
        "LEFT JOIN verses v ON tv.book_number = v.book_number "
        "  AND tv.chapter = v.chapter AND tv.verse = v.verse "
        "WHERE tv.topic_id = ? "
        "ORDER BY tv.book_number, tv.chapter, tv.verse",
        (topic_id,),
    )


# --- LXX alignment queries ---

async def get_lxx_alignment_for_verse(
    book_number: int, chapter: int, verse: int
) -> list[dict[str, Any]]:
    return await _fetch_all(
        "SELECT * FROM lxx_alignments "
        "WHERE hebrew_book = ? AND hebrew_chapter = ? AND hebrew_verse = ?",
        (book_number, chapter, verse),
    )


async def get_lxx_by_hebrew_strongs(strongs: str) -> list[dict[str, Any]]:
    return await _fetch_all(
        "SELECT la.*, b.name AS book_name "
        "FROM lxx_alignments la "
        "JOIN books b ON la.hebrew_book = b.book_number "
        "WHERE la.hebrew_strongs = ? "
        "ORDER BY la.hebrew_book, la.hebrew_chapter, la.hebrew_verse",
        (strongs,),
    )


async def get_lxx_by_greek_strongs(strongs: str) -> list[dict[str, Any]]:
    return await _fetch_all(
        "SELECT la.*, b.name AS book_name "
        "FROM lxx_alignments la "
        "JOIN books b ON la.hebrew_book = b.book_number "
        "WHERE la.lxx_strongs = ? "
        "ORDER BY la.hebrew_book, la.hebrew_chapter, la.hebrew_verse",
        (strongs,),
    )


# --- Book queries ---

async def get_all_books() -> list[dict[str, Any]]:
    return await _fetch_all("SELECT * FROM books ORDER BY book_number")


# --- Utility ---

async def get_verse_id(book_number: int, chapter: int, verse: int) -> int | None:
    result = await _fetch_one(
        "SELECT id FROM verses WHERE book_number = ? AND chapter = ? AND verse = ?",
        (book_number, chapter, verse),
    )
    return result["id"] if result else None
