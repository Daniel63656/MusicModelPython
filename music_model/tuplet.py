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
    from .abstract import ChordRest
    

class Tuplet(Site, Element):
    """
    Tuplet class. Tuplets are both an `Element` and a `Site`, containing other elements themselves.

    Inherits:
    elements (SortedDict): A sorted dictionary of elements contained in the voice.
    note_type (NoteType): The normal note type of the tuplet.
    dots (int): The number of dots of the normal note type.

    Attributes:
    onset (Fraction): The onset of the tuplet.
    normal_count (int): The number of normal notes in the tuplet.
    actual_count (int): The number of actual notes in the tuplet.
    actual_type (NoteType): The actual note type of the tuplet. Defaults to normal type if not specified.
    actual_dots (int): The number of dots of the actual note type. Defaults to normal dots if not specified.
    time_mod (Fraction): The time modification caused by this tuplet. Computable from other attributes.
    """
    def __init__(self, normal_count, normal_type, normal_dots, actual_count, actual_type=None, actual_dots=None) -> None:
        # call super constructors. count, type and dots together make a duration
        Site.__init__(self)
        Element.__init__(self, normal_type, normal_dots)
        self._onset = None  # know onset after adding to site even if no elements inside
        self._normal_count = normal_count
        self._actual_count = actual_count
        self._actual_type = normal_type if actual_type is None else actual_type
        self._actual_dots = normal_dots if actual_dots is None else actual_dots
        self._time_mod = normal_type.get_value(normal_dots)*normal_count / (actual_type.get_value(actual_dots)*actual_count)

    def get_normal_count(self) -> int:
        return self._normal_count
    
    def get_actual_count(self) -> int:
        return self._actual_count
    
    # normal NoteType and dot getters are inherited from Element
    
    def get_actual_type(self) -> NoteType:
        return self._actual_type
    
    def get_actual_dots(self) -> int:
        return self._actual_dots

    def __get_insertion_offset(self):
        """
        Internal method to get the onset of the next element to be added to the tuplet. Used
        to override append methods of `Site`.
        """
        if len(self._elements) == 0:
            return self._onset
        return self._elements.values()[-1].get_offset()

    def append_note(self, note: Note, staff: Staff, note_type: NoteType, dots=0, stem: Stem = None) -> Chord:
        return self.insert_note(self.__get_insertion_offset(), note, staff, note_type, dots, stem)

    def append_chord_or_rest(self, chord: Chord, staff: Staff):
        self.insert_chord_or_rest(self.__get_insertion_offset(), chord, staff)

    def append_tuplet(self, tuplet: Tuplet):
        self.insert_tuplet(self.__get_insertion_offset(), tuplet)

    def insert_chord_or_rest(self, onset: Fraction, chord_rest: ChordRest, staff: Staff):
        event = staff._get_or_create_event(onset)
        event._chord_rests[self.get_voice()] = chord_rest
        chord_rest._event = event
        chord_rest._site = self
        self._elements[onset] = chord_rest

    def get_onset(self) -> Fraction:
        return self._onset
        
    def get_offset(self) -> Fraction:
        return self._onset + self.get_duration()
    
    def get_duration(self) -> Fraction:
        return super().get_duration()*self._normal_count

    def to_json(self):
        return {
            "staff": self.get_staff().get_id(),
            "normal_count": self._normal_count,
            "normal_type": self._note_type.name,
            "normal_dots": self._dots,
            "actual_count": self._actual_count,
            "actual_type": self._actual_type.name,
            "actual_dots": self._actual_dots,
            "elements": {str(onset): element.to_json() for onset, element in self._elements.items()}
        }