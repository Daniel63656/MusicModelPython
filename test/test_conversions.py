import os
from fractions import Fraction
from music_model import *
from music_model.conversion import *
from music_model import ZERO
resources_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")


def test_songs():
    for file in os.listdir(resources_dir):
        filepath = os.path.join(resources_dir, file)
        score = import_xml(filepath)
        show_xml(score)

def test_tuplet_length():
    score = import_xml(os.path.join(resources_dir, "simple_nested_tuplet.musicxml"))
    voice = score.get_parts()[0].get_voice(1)
    outer_tuplet = voice.get_element(Fraction(1, 2))
    assert outer_tuplet.get_duration() == Fraction(1, 4)
    inner_tuplet = outer_tuplet.get_element(Fraction(2, 3))
    assert inner_tuplet.get_duration() == Fraction(1, 12)

def test_standard_contexts():
    score = Score()
    part = Part()
    score.append_part(part)
    staff1 = Staff()
    staff2 = Staff()
    # inserting to part adds standard contexts to staffs
    part.insert_staff(0, staff1)
    part.insert_staff(1, staff2)
    assert staff1.get_clef(ZERO).equals(Clef(ClefType.TREBLE))
    assert staff1.get_key_signature(ZERO).equals(KeySignature(0))
    assert staff1.get_time_signature(ZERO).equals(TimeSignature(4, 4))
    assert staff2.get_clef(ZERO).equals(Clef(ClefType.BASS))
    assert staff2.get_key_signature(ZERO).equals(KeySignature(0))
    assert staff2.get_time_signature(ZERO).equals(TimeSignature(4, 4))
    # check if standard measure has been created in part
    assert part._measures is not None

def test_ending_import():
    score = import_xml(os.path.join(resources_dir, "endings.musicxml"))
    e1 = score._endings.get(Fraction(1, 1))
    assert e1 == score._endings.get_by_offset(Fraction(2, 1))
    assert 1 in e1._numbers
    e2 = score._endings.get(Fraction(2, 1))
    assert e2 == score._endings.get_by_offset(Fraction(3, 1))
    assert 2 in e2._numbers
    e3 = score._endings.get(Fraction(4, 1))
    assert e3 == score._endings.get_by_offset(Fraction(5, 1))
    assert 1 in e3._numbers
    assert 2 in e3._numbers
    e4 = score._endings.get(Fraction(5, 1))
    assert e4 == score._endings.get_by_offset(Fraction(6, 1))
    assert 3 in e4._numbers
    