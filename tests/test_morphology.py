"""Tests for Hebrew and Greek morphology parsers."""

import pytest

from biblical_linguistics_mcp.morphology.hebrew import parse_hebrew_morphology, HebrewMorphology
from biblical_linguistics_mcp.morphology.greek import parse_greek_morphology, GreekMorphology


class TestHebrewMorphology:
    def test_verb_qal_perfect(self):
        # HVqp3ms = Hebrew Verb, Qal, Perfect, 3rd, masculine, singular
        m = parse_hebrew_morphology("HVqp3ms")
        assert m.part_of_speech == "verb"
        assert m.stem == "Qal"
        assert m.aspect == "perfect"
        assert m.person == "3rd"
        assert m.gender == "masculine"
        assert m.number == "singular"

    def test_noun_common(self):
        # HNcfsa = Hebrew Noun, common, feminine, singular, absolute
        m = parse_hebrew_morphology("HNcfsa")
        assert m.part_of_speech == "noun"
        assert m.subtype == "common"
        assert m.gender == "feminine"
        assert m.number == "singular"
        assert m.state == "absolute"

    def test_noun_masculine_plural(self):
        # HNcmpa = Hebrew Noun, common, masculine, plural, absolute
        m = parse_hebrew_morphology("HNcmpa")
        assert m.part_of_speech == "noun"
        assert m.gender == "masculine"
        assert m.number == "plural"
        assert m.state == "absolute"

    def test_verb_hiphil(self):
        m = parse_hebrew_morphology("HVhi3ms")
        assert m.stem == "Hiphil"
        assert m.aspect == "imperfect"

    def test_participle(self):
        # HVqrmsa = Qal participle active masculine singular absolute
        m = parse_hebrew_morphology("HVqrms")
        assert m.stem == "Qal"
        assert m.aspect == "participle_active"
        assert m.gender == "masculine"
        assert m.number == "singular"

    def test_conjunction(self):
        m = parse_hebrew_morphology("HC")
        assert m.part_of_speech == "conjunction"

    def test_empty_code(self):
        m = parse_hebrew_morphology("")
        assert m.raw_code == ""
        assert m.part_of_speech == ""

    def test_to_dict(self):
        m = parse_hebrew_morphology("HVqp3ms")
        d = m.to_dict()
        assert d["part_of_speech"] == "verb"
        assert d["stem"] == "Qal"
        assert "raw_code" in d


class TestGreekMorphology:
    def test_verb_present_active_indicative(self):
        m = parse_greek_morphology("V-PAI-3S")
        assert m.part_of_speech == "verb"
        assert m.tense == "present"
        assert m.voice == "active"
        assert m.mood == "indicative"
        assert m.person == "3rd"
        assert m.number == "singular"

    def test_verb_imperfect(self):
        m = parse_greek_morphology("V-IAI-3S")
        assert m.tense == "imperfect"
        assert m.voice == "active"
        assert m.mood == "indicative"

    def test_noun_nominative(self):
        m = parse_greek_morphology("N-NSM")
        assert m.part_of_speech == "noun"
        assert m.case_form == "nominative"
        assert m.number == "singular"
        assert m.gender == "masculine"

    def test_noun_genitive_feminine(self):
        m = parse_greek_morphology("N-GSF")
        assert m.case_form == "genitive"
        assert m.number == "singular"
        assert m.gender == "feminine"

    def test_adjective(self):
        m = parse_greek_morphology("A-ASN")
        assert m.part_of_speech == "adjective"
        assert m.case_form == "accusative"
        assert m.number == "singular"
        assert m.gender == "neuter"

    def test_article(self):
        m = parse_greek_morphology("T-NSM")
        assert m.part_of_speech == "article"

    def test_aorist(self):
        m = parse_greek_morphology("V-AAI-3S")
        assert m.tense == "aorist"
        assert m.voice == "active"
        assert m.mood == "indicative"

    def test_participle(self):
        m = parse_greek_morphology("V-PAP-NSM")
        assert m.tense == "present"
        assert m.voice == "active"
        assert m.mood == "participle"
        assert m.case_form == "nominative"
        assert m.number == "singular"
        assert m.gender == "masculine"

    def test_empty_code(self):
        m = parse_greek_morphology("")
        assert m.raw_code == ""

    def test_to_dict(self):
        m = parse_greek_morphology("V-PAI-3S")
        d = m.to_dict()
        assert d["tense"] == "present"
        assert "raw_code" in d


class TestOshbCodes:
    def test_prefixes_and_main_morpheme(self):
        m = parse_hebrew_morphology("HC/Vqw3ms")
        assert m.prefixes == ["conjunction"]
        assert m.part_of_speech == "verb"
        assert m.stem == "Qal"
        assert m.aspect == "sequential_imperfect"

    def test_preposition_with_article_prefix(self):
        m = parse_hebrew_morphology("HRd/Ncbsa")
        assert m.prefixes == ["preposition+definite_article"]
        assert m.part_of_speech == "noun"
        assert m.state == "absolute"

    def test_pronominal_suffix(self):
        m = parse_hebrew_morphology("HNcmsc/Sp3ms")
        assert m.state == "construct"
        assert m.suffix_type == "pronominal"
        assert m.suffix_person == "3rd"
        assert m.suffix_gender == "masculine"
        assert m.suffix_number == "singular"

    def test_preposition_with_suffix_only(self):
        m = parse_hebrew_morphology("HR/Sp2fs")
        assert m.part_of_speech == "preposition"
        assert m.prefixes == []
        assert m.suffix_person == "2nd"

    def test_particle_type(self):
        assert parse_hebrew_morphology("HTo").subtype == "direct_object_marker"

    def test_x_is_no_value(self):
        m = parse_hebrew_morphology("HPdxms")
        assert m.subtype == "demonstrative"
        assert m.person == ""
        assert m.gender == "masculine"

    def test_aramaic_stems_differ(self):
        m = parse_hebrew_morphology("AVhp3ms")
        assert m.language == "Aramaic"
        assert m.stem == "Haphel"
