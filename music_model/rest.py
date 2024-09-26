from __future__ import annotations
from .abstract import ChordRest
from .tuplet import Tuplet
from .enums import NoteType

import typing as t
if t.TYPE_CHECKING:
    from fractions import Fraction


class Rest(ChordRest):
    """
    Represents a rest or period of silence in a musical score.

    Inherits:
    site (Site): The owning `Site` of the rest.
    event (Event): The owning `Event` of the rest.
    beam_group (BeamGroup): The `BeamGroup` that contains this rest (optional).
    note_type (NoteType): The visual duration type of the element.
    dots (int): The visual number of dots.
    fermata (bool): Whether the rest has a fermata.

    Attributes:
    nominal_duration (Fraction): The nominal duration of the rest, without tuplet modifications.
    In case of a measure rest, this duration is different from the one defined by the `NoteType` and dots.
    is_measure_rest (bool): Whether the rest represents a full measure. In this case, duration type is 'whole' and dots are 0. 
    """
    def __init__(self, note_type: NoteType, dots: int, measure_duration: Fraction = None, invisible=False): # TODO how to handle invisibility
        if measure_duration is None:
            self._nominal_duration = note_type.get_value(dots)
            self._is_measure_rest = False
        else:
            self._nominal_duration = measure_duration
            self._is_measure_rest = True
            note_type = NoteType.WHOLE
            dots = 0
        self._invisible = invisible
        super().__init__(note_type, dots)

    def get_duration(self) -> Fraction:
        duration = self._nominal_duration
        site = self._site
        while hasattr(site, "_site"):
            duration *= site._time_mod
            site = site._site
        return duration
    
    def is_measure_rest(self) -> bool:
        return self._is_measure_rest
    
    def __str__(self):
        dots_str = '.' * self._dots
        return f"Rest({self._note_type}{dots_str})"
