from __future__ import annotations
from fractions import Fraction
from .abstract import NavigableRange

import typing as t
if t.TYPE_CHECKING:
    from . import Self
    from typing import Iterable, Optional
    from .part import Part
    from .chord import ChordRest


class Measure(NavigableRange):
    def __init__(self, repetition_start=False, repetition_end=False):
        self._part = None
        self._onset = None
        # TODO implement this in score and remove
        self._repetition_start = repetition_start
        self._repetition_end = repetition_end

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
        return max(
            (staff._events.values()[-1].get_offset() for staff in self._part._staffs.values()),
            default=Fraction(0, 1)
        )
    
    def next(self) -> Optional[Self]:
        idx = self._part._measures.bisect_right(self.get_onset())
        if idx >= len(self._part._measures):
            return None
        return self._part._measures.values()[idx]
    
    def previous(self) -> Optional[Self]:
        idx = self._part._measures.bisect_left(self.get_onset())
        if idx < 0:
            return None
        return self._part._measures.values()[idx]

    def get_index(self) -> int:
        return self._part._measures.bisect_right(self.get_onset()) - 1
