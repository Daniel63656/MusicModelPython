import os
from fractions import Fraction
from music_model import *
from music_model.conversion import *
from music_model.repeat import JumpIterator
resources_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")
ZERO = Fraction(0, 1)

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

def test_pitch_retrieval():
    midi_pitches = [68, 68, 66, 67, 61, 73, 68, 65, 60, 72, 67, 65]
    score = import_xml(os.path.join(resources_dir, "acc_and_keys.musicxml"))
    for i, chord in enumerate(score.get_parts()[0].get_staff(0).get_chords_and_rests()):
        assert next(iter(chord.get_notes())).get_pitch() == midi_pitches[i]

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

# for jump tests
def verify_sections(score, expected):
    cursor = JumpIterator(score)
    time = ZERO
    for i, jump in enumerate(cursor):
        print(f"{time} - {jump[0]}")
        assert (time, jump[0]) == expected[i]
        time = jump[1]
    print(f"{time} - {cursor._time}")
    assert (time, cursor.get_time()) == expected[-1]

def test_jumps():
    score = import_xml(os.path.join(resources_dir, "jumps.musicxml"))
    verify_sections(score, [
        (0, 2),     # first D.C.
        (0, 3),     # D.S. al Coda
        (1, 5),     # To Coda (skip 2nd D.C.)
        (6, 7),     # D.S. al Fine
        (1, 8)      # from Segno to Fine
    ])

def test_repeats():
    score = import_xml(os.path.join(resources_dir, "jumps_and_repeats.musicxml"))
    verify_sections(score, [
        (0, 1),     # first repeat end
        (0, 4),     # second repeat end
        (2, 4),     # D.S.
        (1, 6),     # third repeat end
        (5, 7),     # D.C.
        (0, 7)      # begin to end, unubstructed
    ])
    