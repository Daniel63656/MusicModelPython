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
    """
    Represents an octave shift in a musical score. Octave shifts are a type of `Range` that change the pitch of notes in a `Staff`.

    Attributes:
    staff (Staff): The parent staff of the octave shift.
    onset (Fraction): The onset of the octave shift. Equal to the onset of the first `Event` in the octave shift.
    offset (Fraction): The offset of the octave shift (exclusive). Equal to the offset of the last `Event` in the octave shift.
    octavation (Octavation): The type of octavation.
    """
    def __init__(self, staff: Staff, onset: Fraction, offset: Fraction, octavation: Octavation):
        self._staff = staff
        self._onset = onset
        self._offset = offset
        self._octavation = octavation

    def get_staff(self) -> Staff:
        return self._staff
    
    def get_octavation(self) -> Octavation:
        return self._octavation
    
    def get_events(self) -> Iterator[Event]:
        return self._staff.get_events(start=self._onset, end=self._offset, inclusive=(True, True))
    
    def get_chords_and_rests(self) -> Iterator[ChordRest]:
        return self._staff.get_chords_and_rests(minimum=self._onset, maximum=self._offset, borders=(True, True))
    
    def get_first_chord_or_rest(self) -> ChordRest:
        return next(self.get_chords_and_rests())
    
    def get_last_chord_or_rest(self) -> ChordRest:
        return next(self.get_chords_and_rests(reversed=True))
    
    def get_onset(self) -> Fraction:
        return self._onset
        
    def get_offset(self) -> Fraction:
        return self._offset

    def to_json(self):
        return {
            "onset": str(self._onset),
            "offset": str(self._offset),
            "octavation": self._octavation.name
        }
