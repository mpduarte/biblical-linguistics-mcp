"""SQLite schema definitions for the biblical linguistics database."""

SCHEMA_SQL = """
-- Bible books metadata
CREATE TABLE IF NOT EXISTS books (
    book_number INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    testament TEXT NOT NULL CHECK (testament IN ('OT', 'NT')),
    chapters INTEGER NOT NULL,
    original_language TEXT NOT NULL CHECK (original_language IN ('Hebrew', 'Greek', 'Aramaic'))
);

-- Verses with original language text and translations
CREATE TABLE IF NOT EXISTS verses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_number INTEGER NOT NULL,
    chapter INTEGER NOT NULL,
    verse INTEGER NOT NULL,
    text_original TEXT,          -- Unicode Hebrew/Greek
    text_kjv TEXT,
    text_asv TEXT,
    text_web TEXT,
    UNIQUE (book_number, chapter, verse),
    FOREIGN KEY (book_number) REFERENCES books(book_number)
);

-- Lexicon entries (one per Strong's number)
CREATE TABLE IF NOT EXISTS lexemes (
    strongs TEXT PRIMARY KEY,       -- e.g. "H7225", "G3056"
    language TEXT NOT NULL CHECK (language IN ('Hebrew', 'Greek')),
    word TEXT NOT NULL,             -- Unicode original form
    transliteration TEXT,
    root_form TEXT,                 -- lexeme / dictionary form
    gloss TEXT,                     -- short definition
    definition TEXT,                -- extended definition
    frequency INTEGER DEFAULT 0,   -- total occurrences
    semantic_domain TEXT            -- Louw-Nida or similar category
);

-- Individual word occurrences with morphology
CREATE TABLE IF NOT EXISTS extended_lexemes (
    strongs TEXT PRIMARY KEY,
    word TEXT,
    transliteration TEXT,
    morphology TEXT,
    gloss TEXT,
    definition TEXT
);

CREATE TABLE IF NOT EXISTS words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    verse_id INTEGER NOT NULL,
    word_position INTEGER NOT NULL,  -- 1-based position in verse
    text_original TEXT NOT NULL,      -- surface form
    strongs TEXT,                     -- Strong's number
    morphology_code TEXT,            -- raw morphology code
    -- Parsed morphology fields
    part_of_speech TEXT,
    -- Greek-specific
    tense TEXT,
    voice TEXT,
    mood TEXT,
    -- Hebrew-specific
    stem TEXT,                       -- binyan (Qal, Niphal, Piel, etc.)
    aspect TEXT,                     -- perfect, imperfect, etc.
    state TEXT,                      -- construct, absolute
    -- Common
    person TEXT,
    number TEXT,                     -- singular, plural, dual
    gender TEXT,                     -- masculine, feminine, neuter, common
    case_form TEXT,                  -- nominative, genitive, etc. (Greek)
    suffix_person TEXT,
    suffix_number TEXT,
    suffix_gender TEXT,
    qere TEXT,                       -- the word as read, where it differs from the written text
    wlc_ref TEXT,                    -- the WLC verse, whose numbering can differ from the KJV's
    strongs_ext TEXT,                -- STEPBible extended Strong's, one per BDB entry
    strongs_tags TEXT,               -- every morpheme's tag, as TAHOT writes them
    sense TEXT,                      -- that entry's short meaning
    translation TEXT,                -- TAHOT's word-for-word English
    FOREIGN KEY (verse_id) REFERENCES verses(id),
    FOREIGN KEY (strongs) REFERENCES lexemes(strongs)
);

-- Cross-references from TSK
CREATE TABLE IF NOT EXISTS cross_references (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_book INTEGER NOT NULL,
    source_chapter INTEGER NOT NULL,
    source_verse INTEGER NOT NULL,
    target_book INTEGER NOT NULL,
    target_chapter INTEGER NOT NULL,
    target_verse INTEGER NOT NULL,
    source TEXT DEFAULT 'TSK',
    FOREIGN KEY (source_book) REFERENCES books(book_number),
    FOREIGN KEY (target_book) REFERENCES books(book_number)
);

-- Topical index (Nave's)
CREATE TABLE IF NOT EXISTS topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT NOT NULL,
    subtopic TEXT
);

CREATE TABLE IF NOT EXISTS topic_verses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_id INTEGER NOT NULL,
    book_number INTEGER NOT NULL,
    chapter INTEGER NOT NULL,
    verse INTEGER NOT NULL,
    FOREIGN KEY (topic_id) REFERENCES topics(id),
    FOREIGN KEY (book_number) REFERENCES books(book_number)
);

-- LXX alignments
CREATE TABLE IF NOT EXISTS lxx_alignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hebrew_book INTEGER NOT NULL,
    hebrew_chapter INTEGER NOT NULL,
    hebrew_verse INTEGER NOT NULL,
    hebrew_word TEXT,
    hebrew_strongs TEXT,
    lxx_word TEXT,
    lxx_strongs TEXT,
    lxx_morphology TEXT,
    FOREIGN KEY (hebrew_book) REFERENCES books(book_number)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_verses_ref ON verses(book_number, chapter, verse);
CREATE INDEX IF NOT EXISTS idx_words_verse ON words(verse_id);
CREATE INDEX IF NOT EXISTS idx_words_strongs ON words(strongs);
CREATE INDEX IF NOT EXISTS idx_lexemes_language ON lexemes(language);
CREATE INDEX IF NOT EXISTS idx_lexemes_gloss ON lexemes(gloss);
CREATE INDEX IF NOT EXISTS idx_crossref_source ON cross_references(source_book, source_chapter, source_verse);
CREATE INDEX IF NOT EXISTS idx_crossref_target ON cross_references(target_book, target_chapter, target_verse);
CREATE INDEX IF NOT EXISTS idx_topic_verses ON topic_verses(book_number, chapter, verse);
CREATE INDEX IF NOT EXISTS idx_topics_name ON topics(topic);
CREATE INDEX IF NOT EXISTS idx_lxx_hebrew ON lxx_alignments(hebrew_book, hebrew_chapter, hebrew_verse);
CREATE INDEX IF NOT EXISTS idx_lxx_hebrew_strongs ON lxx_alignments(hebrew_strongs);
CREATE INDEX IF NOT EXISTS idx_lxx_lxx_strongs ON lxx_alignments(lxx_strongs);
CREATE INDEX IF NOT EXISTS idx_words_pos ON words(part_of_speech);
"""
