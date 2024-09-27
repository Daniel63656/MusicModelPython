import pytest
from fractions import Fraction
from music_model import *


def test_getting_dotted_note_value_by_duration():
    duration = (Fraction(1, 4) +
                Fraction(1, 8) +
                Fraction(1, 16) +
                Fraction(1, 32))
    note_type, dots = NoteType.from_duration(duration)
    assert note_type == NoteType.QUARTER
    assert dots == 3

def test_invalid_because_not_one_ntpd():
    duration = (Fraction(1, 4) +
                Fraction(1, 8) +
                Fraction(1, 32))
    with pytest.raises(ValueError):
        NoteType.from_duration(duration)

def test_invalid_because_not_divisible():
    duration = (Fraction(1, 4) + Fraction(1, 5))
    with pytest.raises(ValueError):
        NoteType.from_duration(duration)

def test_invalid_because_too_big():
    duration = Fraction(9, 1)
    with pytest.raises(ValueError):
        NoteType.from_duration(duration)

def test_getting_ntpd_list():
    duration = (Fraction(1, 4) + Fraction(1, 8) + Fraction(1, 16) +
                Fraction(1, 64) + Fraction(1, 128))
    type_list = NoteType.types_from_duration(duration)
    assert len(type_list) == 2
    assert type_list[0][0] == NoteType.QUARTER
    assert type_list[0][1] == 2
    assert type_list[1][0] == NoteType.NT64
    assert type_list[1][1] == 1
