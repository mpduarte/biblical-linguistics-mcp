"""The tools with and without STEPBible's data, which the tracked database lacks."""

import shutil
import sqlite3

import pytest

from biblical_linguistics_mcp.db import connection as db_conn
from biblical_linguistics_mcp.tools.word_tools import lookup_word, parse_verse
from conftest import TEST_DB_PATH


@pytest.fixture
def copied_db(tmp_path):
    path = tmp_path / "copy.db"
    shutil.copyfile(TEST_DB_PATH, path)
    db_conn.set_db_path(path)
    return path


@pytest.fixture
def without_extended(copied_db):
    conn = sqlite3.connect(copied_db)
    conn.execute("DROP TABLE extended_lexemes")
    conn.commit()
    conn.close()


async def test_parse_verse_works_without_extended_data(without_extended):
    result = await parse_verse("Genesis 1:1")
    assert result["words"]
    assert result["words"][0]["extended_strongs"] == ""


async def test_lookup_of_an_extended_number_without_data_is_an_error(without_extended):
    result = await lookup_word("H7462C")
    assert "error" in result


async def test_lookup_of_an_extended_number(copied_db):
    conn = sqlite3.connect(copied_db)
    conn.execute(
        "INSERT INTO extended_lexemes VALUES "
        "('H7462C', 'רָעָה', 'ra.ah', 'H:V', 'to accompany', 'to associate with')"
    )
    conn.commit()
    conn.close()
    result = await lookup_word("h7462c")
    assert result["gloss"] == "to accompany"
    assert result["source"] == "STEPBible TBESH"
