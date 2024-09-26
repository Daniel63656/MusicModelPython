from __future__ import annotations
from fractions import Fraction
from .abstract import Element
from .site import Site

import typing as t
if t.TYPE_CHECKING:
    from fractions import Fraction
    from .enums import NoteType, Stem
    from .staff import Staff
    from .chord import Chord
    from .note import Note
    

class Tuplet(Site, Element):
    """
    Tuplet class. Tuplets are both an `Element` and a `Site`, containing other elements themselves.
    """
    def __init__(self, normal_count, normal_type, normal_dots, actual_count, actual_type=None, actual_dots=None) -> None:
        # call super constructors. count, type and dots together make a duration
        Site.__init__(self)
        Element.__init__(self, normal_type, normal_dots)
        # actual type + duration default to normal if not specified
        self._onset = None  # know onset after adding to site even if no elements inside
        self._normal_count = normal_count
        self._actual_count = actual_count
        if actual_type is None:
            actual_type = normal_type
        if actual_dots is None:
            actual_dots = normal_dots
        self._actual_type = actual_type
        self._actual_dots = actual_dots
        # local time modification (caused by this tuplet only)
        self._time_mod = normal_type.get_value(normal_dots)*normal_count / (actual_type.get_value(actual_dots)*actual_count)

    def __get_insertion_offset(self):
        if len(self._elements) == 0:
            return self._onset
        return self._elements.values()[-1].get_offset()

    def append_note(self, note: Note, staff: Staff, note_type: NoteType, dots=0, stem: Stem = None) -> Chord:
        return self.insert_note(self.__get_insertion_offset(), note, staff, note_type, dots, stem)

    def append_chord_or_rest(self, chord: Chord, staff: Staff):
        self.insert_chord_or_rest(self.__get_insertion_offset(), chord, staff)

    def append_tuplet(self, tuplet: Tuplet):
        self.insert_tuplet(self.__get_insertion_offset(), tuplet)

    def get_onset(self) -> Fraction:
        return self._onset
        
    def get_offset(self) -> Fraction:
        return self._onset + self.get_duration()
    
    def get_duration(self) -> Fraction:
        duration = self._note_type.get_value(self._dots)*self._normal_count
        site = self._site
        while hasattr(site, "_site"):
            duration *= site._time_mod
            site = site._site
        return duration
