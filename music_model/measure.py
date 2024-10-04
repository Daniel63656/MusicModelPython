from __future__ import annotations
from fractions import Fraction
from .abstract import NavigableRange
from music_model import ZERO

import typing as t
if t.TYPE_CHECKING:
    from . import Self
    from typing import Iterable, Optional
    from .part import Part
    from .chord import ChordRest


class Measure(NavigableRange):
    """
    Represents a measure in a musical score. Measures are the basic unit of time in music, and are saved as
    continuous and navigable `Range`s of a `Part`.

    Attributes:
    part (Part): The parent part of the measure.
    onset (Fraction): The onset of the measure.
    """
    def __init__(self):
        self._part = None
        self._onset = None

    def get_part(self) -> Part:
        return self._part

    def get_chords_and_rests(self) -> Iterable[ChordRest]:
        for staff in self._part._staffs.values():
            yield from staff.get_chords_and_rests(start=self._onset, end=self.get_offset(), inclusive=(True, False))

    def get_onset(self) -> Fraction:
        return self._onset

    def get_offset(self) -> Fraction:
        next_measure = self.next()
        if next_measure is not None:
            return next_measure.get_onset()
        # last measure, get length by checking all staffs of part
        max_offset = ZERO
        for staff in self._part._staffs.values():
            if len(staff._events) > 0:
                max_offset = max(max_offset, staff._events.values()[-1].get_offset())
        return max_offset

    def starts_repeat(self) -> bool:
        """
        Returns `True` if left barline has repeat symbol
        """
        return self._onset in self._part._score._repeat_starts

    def ends_repeat(self) -> bool:
        """
        Returns `True` if right barline has repeat symbol
        """
        return self.get_offset() in self._part._score._repeat_ends

    def make_repeat_start(self):
        self._part._score._repeat_starts.add(self.onset)

    def make_repeat_end(self):
        self._part._score._repeat_ends.add(self.get_offset())

    def next(self) -> Optional[Self]:
        entry = self._part._measures.higher_entry(self.get_onset())
        return None if entry is None else entry[1]

    def previous(self) -> Optional[Self]:
        entry = self._part._measures.lower_entry(self.get_onset())
        return None if entry is None else entry[1]

    def get_index(self) -> int:
        return self._part._measures.index_of(self.get_onset())
