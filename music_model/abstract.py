from __future__ import annotations
from abc import ABC, abstractmethod

import typing as t
if t.TYPE_CHECKING:
    from . import Self
    from typing import Optional
    from fractions import Fraction
    from .staff import Staff
    from .voice import Voice
    from .site import Site
    from .measure import Measure
    from .beam_group import BeamGroup
    from .enums import NoteType


class Range(ABC):
    """
    Interface for a continuous interval that has defined start and an end points (onset and offset).
    Can be used in sorted collections.
    """
    @abstractmethod
    def get_onset(self) -> Fraction:
        pass

    @abstractmethod
    def get_offset(self) -> Fraction:
        pass

    def get_duration(self) -> Fraction:
        return self.get_offset() - self.get_onset()

    def encloses(self, time: Fraction) -> bool:
        """
        Determine if the specified value is within the range.

        By default, the start of the range is inclusive and the end is exclusive.
        This method can be overridden to adjust the openness or closeness of the
        interval. It is used within the `DiscontinuousMap` to determine whether
        a value hits within the range.

        Parameters:
        time (Fraction): The value to check against the range.

        Returns:
        bool: `True` if the specified value is within the range, otherwise `False`.
        """
        return self.get_onset() <= time < self.get_offset()

    # comparison methods for sorting
    def __gt__(self, other):
        return self.get_onset() > other.get_onset()
    def __lt__(self, other):
        return self.get_onset() < other.get_onset()
    

class NavigableRange(Range):
    """
    Interface for a `Range` that supports indexing and navigation within a sorted collection.
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
    """
    Abstract base class for elements that have a specified duration and are owned in a sequential manner in a `Site`.

    Attributes:
    site (Site): The owning `Site` of the element.
    note_type (NoteType): The duration type of the element. Together with `dots`, this specifies nominal duration.
    dots (int): The number of dots.
    """
    def __init__(self, note_type, dots):
        self._site = None
        self._note_type = note_type
        self._dots = dots
    
    def get_site(self) -> Site:
        """
        Get the `Site` that directly contains this element.
        """
        return self._site
    
    def get_note_type(self) -> NoteType:
        return self._note_type
    
    def get_dots(self) -> int:
        return self._dots
    
    def get_voice(self) -> Voice:
        """
        Get the top-level `Site` that contains this element. 
        """
        site = self._site
        # can't use isinstance here becuase this would cause circular dependency!
        while hasattr(site, "_site"):
            site = site._site
        return site
    
    def get_duration(self) -> Fraction:
        """
        Returns the real duration of the element, taking tuplets into account.
        """
        duration = self._note_type.get_value(self._dots)
        site = self._site
        # can't use isinstance here becuase this would cause circular dependency!
        while hasattr(site, "_site"):
            duration *= site._time_mod
            site = site._site
        return duration
    
    def next(self) -> Optional[Self]:
        entry = self._site._elements.higher_entry(self.get_onset())
        return None if entry is None else entry[1]
    
    def previous(self) -> Optional[Self]:
        entry = self._site._elements.lower_entry(self.get_onset())
        return None if entry is None else entry[1]

    def get_index(self) -> int:
        return self._site._elements.index_of(self.get_onset())


class ChordRest(Element, ABC):
    """
    Abstract base class for chords and rests.

    Attributes:
    event (Event): The owning `Event` of the chord or rest.
    beam_group (BeamGroup): The `BeamGroup` that contains this chord or rest (optional).
    visible (bool): Whether the chord or rest is visible. Defaults to `True`.
    fermata (bool): Whether the chord or rest has a fermata.
    """
    def __init__(self, note_type, dots, visible=True):
        super().__init__(note_type, dots)
        self._event = None
        self._beam_group = None
        self._visible = visible
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
    
    def set_visibility(self, visible: bool):
        self._visible = visible
