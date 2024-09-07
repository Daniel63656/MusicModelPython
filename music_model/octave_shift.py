from __future__ import annotations
from .abstract import Range
from .enums import Octavation

import typing as t
if t.TYPE_CHECKING:
    from typing import Iterator
    from fractions import Fraction
    from .staff import Staff
    from .event import Event
    from .abstract import ChordRest
    

class OctaveShift(Range):
    def __init__(self, staff: Staff, onset: Fraction, offset: Fraction, octavation: Octavation):
        self._staff = staff
        self._onset = onset
        self._offset = offset     # onset of last Event to make independent of last Event's duration
        self._octavation = octavation

    def get_staff(self) -> Staff:
        return self._staff
    
    def get_octavation(self) -> Octavation:
        return self._octavation
    
    def get_events(self) -> Iterator[Event]:
        return self._staff.get_events(start=self._onset, end=self._offset, borders=(True, True))
    
    def get_chords_and_rests(self) -> Iterator[ChordRest]:
        return self._staff.get_chords_and_rests(minimum=self._onset, maximum=self._offset, borders=(True, True))
    
    def get_first_chord_or_rest(self) -> ChordRest:
        return next(self.get_chords_and_rests())
    
    def get_onset(self) -> Fraction:
        return self._onset
        
    def get_offset(self) -> Fraction:
        return self._offset
    
    def encloses(self, time: Fraction) -> bool:
        # make end key incluse
        return self.get_onset() <= time <= self.get_offset()
