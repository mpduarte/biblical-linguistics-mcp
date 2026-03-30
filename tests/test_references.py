"""Tests for Bible reference parser."""

import pytest

from biblical_linguistics_mcp.references.parser import (
    parse_reference,
    normalize_book_name,
    get_all_books,
    get_book_metadata,
    ReferenceError,
    VerseRange,
)


class TestNormalizeBookName:
    def test_full_name(self):
        assert normalize_book_name("Genesis") == "Genesis"
        assert normalize_book_name("Revelation") == "Revelation"

    def test_abbreviation(self):
        assert normalize_book_name("Gen") == "Genesis"
        assert normalize_book_name("Rev") == "Revelation"
        assert normalize_book_name("Rom") == "Romans"

    def test_case_insensitive(self):
        assert normalize_book_name("genesis") == "Genesis"
        assert normalize_book_name("JOHN") == "John"

    def test_numbered_books(self):
        assert normalize_book_name("1 Samuel") == "1 Samuel"
        assert normalize_book_name("1 John") == "1 John"
        assert normalize_book_name("2 Corinthians") == "2 Corinthians"

    def test_unknown_book(self):
        with pytest.raises(ReferenceError):
            normalize_book_name("Narnia")


class TestParseReference:
    def test_simple_verse(self):
        ref = parse_reference("Genesis 1:1")
        assert ref.start.book == "Genesis"
        assert ref.start.chapter == 1
        assert ref.start.verse == 1
        assert ref.is_single

    def test_abbreviated_book(self):
        ref = parse_reference("Gen 1:1")
        assert ref.start.book == "Genesis"

    def test_nt_verse(self):
        ref = parse_reference("John 1:1")
        assert ref.start.book == "John"
        assert ref.start.testament == "NT"
        assert ref.start.book_number == 43

    def test_verse_range(self):
        ref = parse_reference("Romans 8:28-30")
        assert not ref.is_single
        assert ref.start.verse == 28
        assert ref.end is not None
        assert ref.end.verse == 30

    def test_numbered_book(self):
        ref = parse_reference("1 John 3:16")
        assert ref.start.book == "1 John"
        assert ref.start.chapter == 3
        assert ref.start.verse == 16

    def test_whole_chapter(self):
        ref = parse_reference("Psalm 23")
        assert ref.start.book == "Psalms"
        assert ref.start.chapter == 23
        assert ref.start.verse == 1

    def test_osis_format(self):
        ref = parse_reference("John 1:1")
        assert ref.start.osis == "John 1:1"

    def test_str_single(self):
        ref = parse_reference("Gen 1:1")
        assert str(ref) == "Genesis 1:1"

    def test_str_range(self):
        ref = parse_reference("Rom 8:28-30")
        assert str(ref) == "Romans 8:28-30"

    def test_invalid_reference(self):
        with pytest.raises(ReferenceError):
            parse_reference("not a reference at all")

    def test_invalid_book(self):
        with pytest.raises(ReferenceError):
            parse_reference("Narnia 1:1")


class TestBookMetadata:
    def test_get_all_books(self):
        books = get_all_books()
        assert len(books) == 66
        assert books[0]["name"] == "Genesis"
        assert books[-1]["name"] == "Revelation"

    def test_get_book_metadata(self):
        meta = get_book_metadata("Genesis")
        assert meta["testament"] == "OT"
        assert meta["chapters"] == 50
        assert meta["original_language"] == "Hebrew"
        assert meta["book_number"] == 1

    def test_nt_book_metadata(self):
        meta = get_book_metadata("John")
        assert meta["testament"] == "NT"
        assert meta["original_language"] == "Greek"
