import os
from fractions import Fraction
from music_model import *
from music_model.conversion import *
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
    