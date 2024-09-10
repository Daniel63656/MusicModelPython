import os
from fractions import Fraction
from music_model import *
from music_model.conversion import *
from music_model.repeat import JumpIterator
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

# for jump tests
def verify_sections(score, expected):
    cursor = JumpIterator(score)
    time = Fraction(0, 1)
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
    