"""Greek morphology parser.

Parses Robinson-style morphology codes used in many Greek NT datasets.
Format: POS-TENSE_VOICE_MOOD-PERSON_NUMBER  or  POS-CASE_NUMBER_GENDER
Examples:
  "V-PAI-1S"  = Verb, Present Active Indicative, 1st person Singular
  "N-NSM"     = Noun, Nominative Singular Masculine
  "A-GSF"     = Adjective, Genitive Singular Feminine
"""

from __future__ import annotations

from dataclasses import dataclass

POS_CODES = {
    "N": "noun",
    "V": "verb",
    "A": "adjective",
    "ADV": "adverb",
    "CONJ": "conjunction",
    "PREP": "preposition",
    "PRT": "particle",
    "D": "demonstrative",
    "P": "pronoun",
    "RP": "relative_pronoun",
    "PP": "personal_pronoun",
    "DP": "demonstrative_pronoun",
    "IP": "interrogative_pronoun",
    "RR": "relative_pronoun",
    "C": "conjunction",
    "I": "interjection",
    "X": "indeclinable",
    "T": "article",
    "R": "pronoun",
    "F": "reflexive_pronoun",
    "S": "possessive_pronoun",
    "Q": "interrogative_pronoun",
    "K": "correlative_pronoun",
}

TENSE_CODES = {
    "P": "present",
    "I": "imperfect",
    "F": "future",
    "A": "aorist",
    "X": "perfect",
    "Y": "pluperfect",
    "2A": "second_aorist",
    "2F": "second_future",
    "2P": "second_perfect",
    "2Y": "second_pluperfect",
}

VOICE_CODES = {
    "A": "active",
    "M": "middle",
    "P": "passive",
    "E": "middle_or_passive",
    "D": "middle_deponent",
    "O": "passive_deponent",
    "N": "middle_or_passive_deponent",
    "Q": "impersonal_active",
    "X": "no_voice",
}

MOOD_CODES = {
    "I": "indicative",
    "S": "subjunctive",
    "O": "optative",
    "M": "imperative",
    "N": "infinitive",
    "P": "participle",
}

PERSON_CODES = {
    "1": "1st",
    "2": "2nd",
    "3": "3rd",
}

NUMBER_CODES = {
    "S": "singular",
    "P": "plural",
}

GENDER_CODES = {
    "M": "masculine",
    "F": "feminine",
    "N": "neuter",
}

CASE_CODES = {
    "N": "nominative",
    "G": "genitive",
    "D": "dative",
    "A": "accusative",
    "V": "vocative",
}


@dataclass
class GreekMorphology:
    """Parsed Greek morphological data."""

    raw_code: str
    part_of_speech: str = ""
    tense: str = ""
    voice: str = ""
    mood: str = ""
    person: str = ""
    number: str = ""
    gender: str = ""
    case_form: str = ""

    def to_dict(self) -> dict[str, str]:
        d: dict[str, str] = {"raw_code": self.raw_code}
        for fld in [
            "part_of_speech", "tense", "voice", "mood", "person",
            "number", "gender", "case_form",
        ]:
            val = getattr(self, fld)
            if val:
                d[fld] = val
        return d


def parse_greek_morphology(code: str) -> GreekMorphology:
    """Parse a Robinson-style Greek morphology code.

    Formats:
    - Verb: V-TAI-1S  (tense, voice, mood - person, number)
    - Noun: N-NSM     (case, number, gender)
    - Adj:  A-GSF     (case, number, gender)
    - etc.
    """
    result = GreekMorphology(raw_code=code)

    if not code:
        return result

    parts = code.split("-")
    pos_raw = parts[0].strip()
    result.part_of_speech = POS_CODES.get(pos_raw, pos_raw)

    if len(parts) < 2:
        return result

    if pos_raw == "V":
        _parse_greek_verb(parts[1:], result)
    else:
        _parse_greek_nominal(parts[1:], result)

    return result


def _parse_greek_verb(parts: list[str], result: GreekMorphology) -> None:
    """Parse verb parts: tense/voice/mood and person/number."""
    if not parts:
        return

    tvm = parts[0]

    # Parse tense (may be 2 chars for second aorist etc.)
    idx = 0
    if idx < len(tvm):
        # Check for two-char tense
        if idx + 1 < len(tvm) and tvm[idx] == "2":
            tense_key = tvm[idx:idx + 2]
            idx += 2
        else:
            tense_key = tvm[idx]
            idx += 1
        result.tense = TENSE_CODES.get(tense_key, tense_key)

    if idx < len(tvm):
        result.voice = VOICE_CODES.get(tvm[idx], tvm[idx])
        idx += 1

    if idx < len(tvm):
        result.mood = MOOD_CODES.get(tvm[idx], tvm[idx])
        idx += 1

    # Person and number from second part
    if len(parts) > 1:
        pn = parts[1]
        if len(pn) >= 1:
            result.person = PERSON_CODES.get(pn[0], pn[0])
        if len(pn) >= 2:
            result.number = NUMBER_CODES.get(pn[1], pn[1])

    # Participles may have case/number/gender instead of person/number
    if result.mood == "participle" and len(parts) > 1:
        cng = parts[1]
        if len(cng) >= 1 and cng[0] in CASE_CODES:
            result.person = ""
            result.case_form = CASE_CODES.get(cng[0], cng[0])
        if len(cng) >= 2:
            result.number = NUMBER_CODES.get(cng[1], cng[1])
        if len(cng) >= 3:
            result.gender = GENDER_CODES.get(cng[2], cng[2])


def _parse_greek_nominal(parts: list[str], result: GreekMorphology) -> None:
    """Parse nominal (noun/adj/pronoun/article) parts: case, number, gender."""
    if not parts:
        return

    cng = parts[0]
    idx = 0
    if idx < len(cng):
        result.case_form = CASE_CODES.get(cng[idx], cng[idx])
        idx += 1
    if idx < len(cng):
        result.number = NUMBER_CODES.get(cng[idx], cng[idx])
        idx += 1
    if idx < len(cng):
        result.gender = GENDER_CODES.get(cng[idx], cng[idx])
        idx += 1


# Morphology code reference table
MORPHOLOGY_REFERENCE = {
    "parts_of_speech": POS_CODES,
    "tenses": TENSE_CODES,
    "voices": VOICE_CODES,
    "moods": MOOD_CODES,
    "persons": PERSON_CODES,
    "numbers": NUMBER_CODES,
    "genders": GENDER_CODES,
    "cases": CASE_CODES,
}
