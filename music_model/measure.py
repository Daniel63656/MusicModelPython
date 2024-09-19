from __future__ import annotations
from fractions import Fraction
from .abstract import NavigableRange

import typing as t
if t.TYPE_CHECKING:
    from . import Self
    from typing import Iterable, Optional
    from .staff import Staff
    from .event import Event
    from .chord import ChordRest
    from .signatures import TimeSignature


class Measure(NavigableRange):
    def __init__(self, repetition_start=False, repetition_end=False):
        self._staff = None
        self._onset = None
        self._repetition_start = repetition_start
        self._repetition_end = repetition_end

    def get_staff(self) -> Staff:
        return self._staff
    
    def get_time_signature(self) -> TimeSignature:
        return self._staff.get_time_signature(self._onset)

    def get_events(self) -> Iterable[Event]:
        return self._staff.get_events(start=self._onset, end=self.get_offset(), inclusive=(True, False))
    
    def get_chords_and_rests(self) -> Iterable[ChordRest]:
        return self._staff.get_chords(start=self._onset, end=self.get_offset(), inclusive=(True, False))

    def get_onset(self) -> Fraction:
        return self._onset

    def get_offset(self) -> Fraction:
        next_measure = self.next()
        if next_measure is not None:
            return next_measure.get_onset()
        # last measure, get length by checking all staffs of part
        max_offset = Fraction(0, 1)
        for staff in self._staff._part._staffs.values():
            if len(staff._events) > 0:
                max_offset = max(max_offset, staff._events.values()[-1].get_offset())
        return max_offset
    
    def next(self) -> Optional[Self]:
        idx = self._staff._measures.bisect_right(self.get_onset())
        if idx >= len(self._staff._measures):
            return None
        return self._staff._measures.values()[idx]
    
    def previous(self) -> Optional[Self]:
        idx = self._staff._measures.bisect_left(self.get_onset())
        if idx < 0:
            return None
        return self._staff._measures.values()[idx]

    def get_index(self) -> int:
        return self._staff._measures.bisect_right(self.get_onset()) - 1
