"""Hebrew morphology parser.

Parses OSHB-style morphology codes into human-readable descriptions.
OSHB codes follow the pattern: part_of_speech/stem,aspect,person,gender,number/state
Examples:
  "HVqp3ms" = Hebrew Verb, Qal, Perfect, 3rd person, masculine, singular
  "HNcmsa"  = Hebrew Noun, common, masculine, singular, absolute
"""

from __future__ import annotations

from dataclasses import dataclass, field

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


@dataclass
class HebrewMorphology:
    """Parsed Hebrew morphological data."""

    raw_code: str
    part_of_speech: str = ""
    subtype: str = ""
    stem: str = ""
    aspect: str = ""
    person: str = ""
    gender: str = ""
    number: str = ""
    state: str = ""
    suffix_person: str = ""
    suffix_gender: str = ""
    suffix_number: str = ""

    def to_dict(self) -> dict[str, str]:
        d: dict[str, str] = {"raw_code": self.raw_code}
        for fld in [
            "part_of_speech", "subtype", "stem", "aspect", "person",
            "gender", "number", "state", "suffix_person", "suffix_gender",
            "suffix_number",
        ]:
            val = getattr(self, fld)
            if val:
                d[fld] = val
        return d


def parse_hebrew_morphology(code: str) -> HebrewMorphology:
    """Parse an OSHB-style Hebrew morphology code.

    The code format varies by part of speech. General pattern:
    H[POS][type/stem][aspect][person][gender][number][state]
    Prefix 'H' indicates Hebrew.
    """
    result = HebrewMorphology(raw_code=code)

    if not code:
        return result

    # Strip language prefix
    pos_start = 0
    if code[0] in ("H", "A"):  # H=Hebrew, A=Aramaic
        pos_start = 1

    if pos_start >= len(code):
        return result

    pos_char = code[pos_start]
    result.part_of_speech = POS_CODES.get(pos_char, pos_char)

    remaining = code[pos_start + 1:]

    if pos_char == "V":
        _parse_hebrew_verb(remaining, result)
    elif pos_char == "N":
        _parse_hebrew_noun(remaining, result)
    elif pos_char == "A":
        _parse_hebrew_adjective(remaining, result)
    elif pos_char == "P":
        _parse_hebrew_pronoun(remaining, result)
    elif pos_char in ("R", "C", "D", "T", "S"):
        _parse_hebrew_particle(remaining, result)

    return result


def _parse_hebrew_verb(code: str, result: HebrewMorphology) -> None:
    """Parse verb morphology: stem, aspect, person, gender, number."""
    idx = 0
    if idx < len(code):
        result.stem = STEM_CODES.get(code[idx], code[idx])
        idx += 1
    if idx < len(code):
        result.aspect = ASPECT_CODES.get(code[idx], code[idx])
        idx += 1
    # Participles and infinitives don't have person
    if idx < len(code) and code[idx] in PERSON_CODES:
        result.person = PERSON_CODES.get(code[idx], code[idx])
        idx += 1
    if idx < len(code):
        result.gender = GENDER_CODES.get(code[idx], code[idx])
        idx += 1
    if idx < len(code):
        result.number = NUMBER_CODES.get(code[idx], code[idx])
        idx += 1
    # Optional state for participles
    if idx < len(code) and code[idx] in STATE_CODES:
        result.state = STATE_CODES.get(code[idx], code[idx])
        idx += 1
    # Pronominal suffix
    if idx < len(code):
        _parse_suffix(code[idx:], result)


def _parse_hebrew_noun(code: str, result: HebrewMorphology) -> None:
    """Parse noun morphology: type, gender, number, state."""
    idx = 0
    if idx < len(code):
        result.subtype = NOUN_TYPE.get(code[idx], code[idx])
        idx += 1
    if idx < len(code):
        result.gender = GENDER_CODES.get(code[idx], code[idx])
        idx += 1
    if idx < len(code):
        result.number = NUMBER_CODES.get(code[idx], code[idx])
        idx += 1
    if idx < len(code) and code[idx] in STATE_CODES:
        result.state = STATE_CODES.get(code[idx], code[idx])
        idx += 1
    if idx < len(code):
        _parse_suffix(code[idx:], result)


def _parse_hebrew_adjective(code: str, result: HebrewMorphology) -> None:
    """Parse adjective morphology: type, gender, number, state."""
    idx = 0
    if idx < len(code):
        result.subtype = ADJ_TYPE.get(code[idx], code[idx])
        idx += 1
    if idx < len(code):
        result.gender = GENDER_CODES.get(code[idx], code[idx])
        idx += 1
    if idx < len(code):
        result.number = NUMBER_CODES.get(code[idx], code[idx])
        idx += 1
    if idx < len(code) and code[idx] in STATE_CODES:
        result.state = STATE_CODES.get(code[idx], code[idx])
        idx += 1


def _parse_hebrew_pronoun(code: str, result: HebrewMorphology) -> None:
    """Parse pronoun morphology: type, person, gender, number."""
    idx = 0
    if idx < len(code):
        result.subtype = PRONOUN_TYPE.get(code[idx], code[idx])
        idx += 1
    if idx < len(code) and code[idx] in PERSON_CODES:
        result.person = PERSON_CODES.get(code[idx], code[idx])
        idx += 1
    if idx < len(code):
        result.gender = GENDER_CODES.get(code[idx], code[idx])
        idx += 1
    if idx < len(code):
        result.number = NUMBER_CODES.get(code[idx], code[idx])
        idx += 1


def _parse_hebrew_particle(code: str, result: HebrewMorphology) -> None:
    """Parse particle/preposition/conjunction morphology."""
    # These are usually just the POS, sometimes with a suffix
    if code:
        _parse_suffix(code, result)


def _parse_suffix(code: str, result: HebrewMorphology) -> None:
    """Parse pronominal suffix: person, gender, number."""
    idx = 0
    if idx < len(code) and code[idx] in PERSON_CODES:
        result.suffix_person = PERSON_CODES.get(code[idx], code[idx])
        idx += 1
    if idx < len(code):
        result.suffix_gender = GENDER_CODES.get(code[idx], code[idx])
        idx += 1
    if idx < len(code):
        result.suffix_number = NUMBER_CODES.get(code[idx], code[idx])
        idx += 1


# Morphology code reference table
MORPHOLOGY_REFERENCE = {
    "parts_of_speech": POS_CODES,
    "stems": STEM_CODES,
    "aspects": ASPECT_CODES,
    "persons": PERSON_CODES,
    "genders": GENDER_CODES,
    "numbers": NUMBER_CODES,
    "states": STATE_CODES,
    "noun_types": NOUN_TYPE,
    "pronoun_types": PRONOUN_TYPE,
    "adjective_types": ADJ_TYPE,
}
