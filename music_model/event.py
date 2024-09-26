from __future__ import annotations
from .abstract import NavigableRange

import typing as t
if t.TYPE_CHECKING:
    from fractions import Fraction
    from typing import Optional, Iterable
    from .abstract import ChordRest
    from .measure import Measure
    from .staff import Staff
    from . import Self


class Event(NavigableRange):
    """
    Storage container for `ChordRest` objects within a `Staff` that share a common onset. Since this class
    has no direct musical counterpart, it is only meant for internal use and can't be instantiated
    as standalone object without a parent staff. Offset is determined implicitly by the elements within it.

    Attributes:
    staff (Staff): The parent staff of the event.
    onset (Fraction): The onset of the event.
    chord_rests (dict): A dictionary for storing `ChordRest` objects with their respective `Voice` as key.
    """
    def __init__(self, staff: Staff, onset: Fraction):
        self._staff = staff
        self._onset = onset
        self._chord_rests = {}  # mapped with Voice as key

    def get_staff(self) -> Staff:
        return self._staff
    
    def get_measure(self) -> Measure:
        return self._staff._part.get_measure(self._onset)
    
    def get_chords_and_rests(self) -> Iterable[ChordRest]:
        return self._chord_rests.values()
    
    def get_onset(self) -> Fraction:
        return self._onset
        
    def get_offset(self) -> Fraction:
        return max(cr.get_offset() for cr in self._chord_rests.values())
    
    def next(self) -> Optional[Self]:
        idx = self._staff._events.bisect_right(self.get_onset())
        if idx >= len(self._staff._events):
            return None
        return self._staff._events.values()[idx]
    
    def previous(self) -> Optional[Self]:
        idx = self._staff._events.bisect_left(self.get_onset())
        if idx < 0:
            return None
        return self._staff._events.values()[idx]

    def get_index(self) -> int:
        return self._staff._events.bisect_right(self.get_onset()) - 1
