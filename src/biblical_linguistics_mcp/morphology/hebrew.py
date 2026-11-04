"""Hebrew morphology parser.

Parses OSHB-style morphology codes into human-readable descriptions.
OSHB codes follow the pattern: part_of_speech/stem,aspect,person,gender,number/state
Examples:
  "HVqp3ms" = Hebrew Verb, Qal, Perfect, 3rd person, masculine, singular
  "HNcmsa"  = Hebrew Noun, common, masculine, singular, absolute
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Part of speech codes (OSHB)
POS_CODES = {
    "A": "adjective",
    "C": "conjunction",
    "D": "adverb",
    "N": "noun",
    "P": "pronoun",
    "R": "preposition",
    "S": "suffix",
    "T": "particle",
    "V": "verb",
}

# Noun type
NOUN_TYPE = {
    "c": "common",
    "g": "gentilic",
    "p": "proper",
}

# Pronoun type
PRONOUN_TYPE = {
    "d": "demonstrative",
    "f": "indefinite",
    "i": "interrogative",
    "p": "personal",
    "r": "relative",
}

# Adjective type
ADJ_TYPE = {
    "a": "adjective",
    "c": "cardinal_number",
    "g": "gentilic",
    "o": "ordinal_number",
}

# Verb stems (binyanim)
STEM_CODES = {
    "q": "Qal",
    "N": "Niphal",
    "p": "Piel",
    "P": "Pual",
    "h": "Hiphil",
    "H": "Hophal",
    "t": "Hithpael",
    # Less common
    "o": "Polel",
    "O": "Polal",
    "r": "Hithpolel",
    "m": "Poel",
    "M": "Poal",
    "k": "Palel",
    "K": "Pulal",
    "Q": "Qal_Passive",
    "l": "Pilpel",
    "L": "Polpal",
    "f": "Hithpalpel",
    "D": "Nithpael",
    "j": "Pealal",
    "i": "Pilel",
    "u": "Hothpaal",
    "c": "Tiphil",
    "v": "Hishtaphel",
    "w": "Nithpalel",
    "y": "Nithpoel",
    "z": "Hithpoel",
}

# Aspect / conjugation
ASPECT_CODES = {
    "p": "perfect",
    "q": "sequential_perfect",
    "i": "imperfect",
    "w": "sequential_imperfect",
    "h": "cohortative",
    "j": "jussive",
    "v": "imperative",
    "r": "participle_active",
    "s": "participle_passive",
    "a": "infinitive_absolute",
    "c": "infinitive_construct",
}

# Person
PERSON_CODES = {
    "1": "1st",
    "2": "2nd",
    "3": "3rd",
}

# Gender
GENDER_CODES = {
    "m": "masculine",
    "f": "feminine",
    "b": "both",
    "c": "common",
}

# Number
NUMBER_CODES = {
    "s": "singular",
    "p": "plural",
    "d": "dual",
}

# State
STATE_CODES = {
    "a": "absolute",
    "c": "construct",
    "d": "determined",
}


# Particle types
PARTICLE_TYPE = {
    "a": "affirmation",
    "d": "definite_article",
    "e": "exhortation",
    "i": "interrogative",
    "j": "interjection",
    "m": "demonstrative",
    "n": "negative",
    "o": "direct_object_marker",
    "r": "relative",
}

# Preposition type: only "d", an inseparable preposition pointed for the article
PREPOSITION_TYPE = {
    "d": "definite_article",
}

# Suffix types
SUFFIX_TYPE = {
    "d": "directional_he",
    "h": "paragogic_he",
    "n": "paragogic_nun",
    "p": "pronominal",
}

# Aramaic verb stems: the same letters name different stems in Aramaic
ARAMAIC_STEM_CODES = {
    "q": "Peal",
    "Q": "Peil",
    "u": "Hithpeel",
    "p": "Pael",
    "P": "Ithpaal",
    "M": "Hithpaal",
    "a": "Aphel",
    "h": "Haphel",
    "s": "Saphel",
    "e": "Shaphel",
    "H": "Hophal",
    "i": "Ithpeel",
    "t": "Hishtaphel",
    "v": "Ishtaphel",
    "w": "Hithaphel",
    "o": "Polel",
    "z": "Ithpoel",
    "r": "Hithpolel",
    "f": "Hithpalpel",
    "b": "Hephal",
    "c": "Tiphel",
    "m": "Poel",
    "l": "Palpel",
    "L": "Ithpalpel",
    "O": "Ithpolel",
    "G": "Ittaphal",
}


@dataclass
class HebrewMorphology:
    """Parsed Hebrew morphological data."""

    raw_code: str
    language: str = ""
    part_of_speech: str = ""
    subtype: str = ""
    stem: str = ""
    aspect: str = ""
    person: str = ""
    gender: str = ""
    number: str = ""
    state: str = ""
    prefixes: list[str] = field(default_factory=list)
    suffix_type: str = ""
    suffix_person: str = ""
    suffix_gender: str = ""
    suffix_number: str = ""

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"raw_code": self.raw_code}
        for fld in [
            "language", "part_of_speech", "subtype", "stem", "aspect", "person",
            "gender", "number", "state", "prefixes", "suffix_type",
            "suffix_person", "suffix_gender", "suffix_number",
        ]:
            val = getattr(self, fld)
            if val:
                d[fld] = val
        return d


def _value(table: dict[str, str], char: str) -> str:
    """Look a code up; 'x' is OSHB's placeholder for no value."""
    return "" if char == "x" else table.get(char, char)


def _prefix_name(segment: str) -> str:
    """Name a morpheme written before the word's main morpheme."""
    pos = POS_CODES.get(segment[0], segment[0])
    if segment[0] == "T" and len(segment) > 1:
        return _value(PARTICLE_TYPE, segment[1])
    if segment[0] == "R" and len(segment) > 1:
        return f"{pos}+{_value(PREPOSITION_TYPE, segment[1])}"
    return pos


def parse_hebrew_morphology(code: str) -> HebrewMorphology:
    """Parse an OSHB morphology code.

    A code is a language letter (H or A) and morphemes joined by "/": any
    prefixes, the main morpheme, then any suffix, as in "HC/Vqw3ms" or
    "HNcmsc/Sp3ms". The fields describe the main morpheme.
    """
    result = HebrewMorphology(raw_code=code)

    if not code:
        return result

    body = code
    if code[0] in ("H", "A"):  # H=Hebrew, A=Aramaic
        result.language = "Hebrew" if code[0] == "H" else "Aramaic"
        body = code[1:]

    segments = [s for s in body.split("/") if s]
    if not segments:
        return result

    if len(segments) > 1 and segments[-1][0] == "S":
        _parse_suffix_morpheme(segments.pop()[1:], result)

    result.prefixes = [_prefix_name(s) for s in segments[:-1]]
    main = segments[-1]

    pos_char = main[0]
    result.part_of_speech = POS_CODES.get(pos_char, pos_char)
    remaining = main[1:]

    if pos_char == "V":
        _parse_hebrew_verb(remaining, result)
    elif pos_char == "N":
        _parse_hebrew_noun(remaining, result)
    elif pos_char == "A":
        _parse_hebrew_adjective(remaining, result)
    elif pos_char == "P":
        _parse_hebrew_pronoun(remaining, result)
    elif pos_char == "T" and remaining:
        result.subtype = _value(PARTICLE_TYPE, remaining[0])
    elif pos_char == "R" and remaining:
        result.subtype = _value(PREPOSITION_TYPE, remaining[0])
    elif pos_char == "S":
        _parse_suffix_morpheme(remaining, result)

    return result


def _parse_hebrew_verb(code: str, result: HebrewMorphology) -> None:
    """Parse verb morphology: stem, aspect, person, gender, number, state."""
    stems = ARAMAIC_STEM_CODES if result.language == "Aramaic" else STEM_CODES
    idx = 0
    if idx < len(code):
        result.stem = _value(stems, code[idx])
        idx += 1
    if idx < len(code):
        result.aspect = _value(ASPECT_CODES, code[idx])
        idx += 1
    # Participles and infinitives don't have person
    if idx < len(code) and (code[idx] in PERSON_CODES or code[idx] == "x"):
        result.person = _value(PERSON_CODES, code[idx])
        idx += 1
    if idx < len(code):
        result.gender = _value(GENDER_CODES, code[idx])
        idx += 1
    if idx < len(code):
        result.number = _value(NUMBER_CODES, code[idx])
        idx += 1
    # Optional state for participles
    if idx < len(code):
        result.state = _value(STATE_CODES, code[idx])


def _parse_hebrew_noun(code: str, result: HebrewMorphology) -> None:
    """Parse noun morphology: type, gender, number, state."""
    if len(code) > 0:
        result.subtype = _value(NOUN_TYPE, code[0])
    if len(code) > 1:
        result.gender = _value(GENDER_CODES, code[1])
    if len(code) > 2:
        result.number = _value(NUMBER_CODES, code[2])
    if len(code) > 3:
        result.state = _value(STATE_CODES, code[3])


def _parse_hebrew_adjective(code: str, result: HebrewMorphology) -> None:
    """Parse adjective morphology: type, gender, number, state."""
    if len(code) > 0:
        result.subtype = _value(ADJ_TYPE, code[0])
    if len(code) > 1:
        result.gender = _value(GENDER_CODES, code[1])
    if len(code) > 2:
        result.number = _value(NUMBER_CODES, code[2])
    if len(code) > 3:
        result.state = _value(STATE_CODES, code[3])


def _parse_hebrew_pronoun(code: str, result: HebrewMorphology) -> None:
    """Parse pronoun morphology: type, person, gender, number."""
    if len(code) > 0:
        result.subtype = _value(PRONOUN_TYPE, code[0])
    if len(code) > 1:
        result.person = _value(PERSON_CODES, code[1])
    if len(code) > 2:
        result.gender = _value(GENDER_CODES, code[2])
    if len(code) > 3:
        result.number = _value(NUMBER_CODES, code[3])


def _parse_suffix_morpheme(code: str, result: HebrewMorphology) -> None:
    """Parse a suffix morpheme: type, then person, gender, number."""
    if len(code) > 0:
        result.suffix_type = _value(SUFFIX_TYPE, code[0])
    if len(code) > 1:
        result.suffix_person = _value(PERSON_CODES, code[1])
    if len(code) > 2:
        result.suffix_gender = _value(GENDER_CODES, code[2])
    if len(code) > 3:
        result.suffix_number = _value(NUMBER_CODES, code[3])


# Morphology code reference table
MORPHOLOGY_REFERENCE = {
    "parts_of_speech": POS_CODES,
    "stems": STEM_CODES,
    "aramaic_stems": ARAMAIC_STEM_CODES,
    "aspects": ASPECT_CODES,
    "persons": PERSON_CODES,
    "genders": GENDER_CODES,
    "numbers": NUMBER_CODES,
    "states": STATE_CODES,
    "noun_types": NOUN_TYPE,
    "pronoun_types": PRONOUN_TYPE,
    "adjective_types": ADJ_TYPE,
    "particle_types": PARTICLE_TYPE,
    "preposition_types": PREPOSITION_TYPE,
    "suffix_types": SUFFIX_TYPE,
}
