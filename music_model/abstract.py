from __future__ import annotations
from abc import ABC, abstractmethod

import typing as t
if t.TYPE_CHECKING:
    from . import Self
    from typing import Optional, Union
    from fractions import Fraction
    from .staff import Staff
    from .voice import Voice
    from .tuplet import Tuplet
    from .measure import Measure
    from .beam_group import BeamGroup
    from .enums import NoteType


class Range(ABC):
    @abstractmethod
    def get_onset(self) -> Fraction:
        pass

    @abstractmethod
    def get_offset(self) -> Fraction:
        pass

    def get_duration(self) -> Fraction:
        return self.get_offset() - self.get_onset()

    def encloses(self, time: Fraction) -> bool:
        """ Determines if the specified value is within the range. By default, the start is inclusive
            and the end is exclusive. This method can be overridden to adjust the openness/closeness 
            of the interval. This function is used inside the ```DiscontinuousRangeMap``` to determine a hit.
            
            param key: The value to be checked.
            return: True if the specified value is in range, otherwise False.
        """
        return self.get_onset() <= time < self.get_offset()

    # comparison methods for sorting
    def __gt__(self, other):
        return self.get_onset() > other.get_onset()
    def __lt__(self, other):
        return self.get_onset() < other.get_onset()
    

class NavigableRange(Range):
    """ A range that is kept in a sorted manner in an owner
    """
    @abstractmethod
    def next(self) -> Optional[Self]:
        pass
    
    @abstractmethod
    def previous(self) -> Optional[Self]:
        pass

    @abstractmethod
    def get_index(self) -> int:
        pass


class Element(NavigableRange, ABC):
    def __init__(self, note_type, dots):
        self._site = None
        self._note_type = note_type
        self._dots = dots
    
    def get_voice(self) -> Voice:
        site = self._site
        # can't use isinstance here becuase this would cause circular dependencies!
        while hasattr(site, "_site"):
            site = site._site
        return site
    
    def get_site(self) -> Union[Voice, Tuplet]:
        return self._site
    
    def get_note_type(self) -> NoteType:
        return self._note_type
    
    def get_dots(self) -> int:
        return self._dots
    
    def next(self) -> Optional[Self]:
        idx = self._site._elements.bisect_right(self.get_onset())
        if idx >= len(self._site._elements):
            return None
        return self._site._elements.values()[idx]
    
    def previous(self) -> Optional[Self]:
        idx = self._site._elements.bisect_left(self.get_onset())
        if idx < 0:
            return None
        return self._site._elements.values()[idx]

    def get_index(self) -> int:
        return self._site._elements.bisect_right(self.get_onset()) - 1


class ChordRest(Element, ABC):
    def __init__(self, note_type, dots):
        super().__init__(note_type, dots)
        self._event = None
        self._beam_group = None
        self._fermata = False

    def get_staff(self) -> Staff:
        return self._event._staff

    def get_measure(self) -> Measure:
        return self._event._staff.get_measure(self._event._onset)
    
    def get_beam_group(self) -> BeamGroup:
        return self._beam_group
    
    def has_fermata(self) -> bool:
        return self._fermata
    
    def add_fermata(self):
        self._fermata = True
    
    def get_onset(self) -> Fraction:
        return self._event._onset
        
    def get_offset(self) -> Fraction:
        return self._event._onset + self.get_duration()
