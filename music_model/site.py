from __future__ import annotations
from sortedcontainers import SortedDict
from music_model import ZERO
from .abstract import Range
from .chord import Chord
from .event import Event

import typing as t
if t.TYPE_CHECKING:
    from fractions import Fraction
    from typing import Iterator, Optional
    from .staff import Staff
    from .tuplet import Tuplet
    from .abstract import Element, ChordRest
    from .note import Note
    from .enums import NoteType, Stem


class Site(Range):
    """
    Base class for an ordered collection of elements (Tuplets, Chords and Rests), forming an independent temporal strand.

    Attributes:
    elements (SortedDict): A sorted dictionary of elements in the site, ordered by onset.
    """
    def __init__(self):
        self._elements = SortedDict()
    
    def get_elements(self, start: Fraction = None, end: Fraction = None, inclusive=(True, True), reverse: bool = False) -> Iterator[Element]:
        """ Create an iterator of directly owned elements (Tuplets, Chords and Rests)
            between `start` and `end`, not recursing into child sites

            If `start` and `end` are not specified, all elements within the
            site are returned.
            The argument `inclusive` is a pair of booleans that indicates whether
            the start and end ought to be included in the range,
            respectively. The default is ``(True, True)`` such that the range is
            inclusive of both start and end.
        """ 
        return (self._elements[key] for key in self._elements.irange(start, end, inclusive, reverse))
    
    def get_element(self, time: Fraction) -> Optional[Element]:
        """ Get the element at an exact time or None if no element exists at that time.
        """
        return self._elements[time]
    
    def get_chords_and_rests(self, start: Fraction=None, end: Fraction=None, inclusive=(True, False), reverse: bool=False) -> Iterator[ChordRest]:
        """ Create an iterator of all chords and rests in a flattened view (this site and
            all child sites) between `start` and `end`.

            If `start` and `end` are not specified, all chords and rests
            within the site are returned.
            The argument `inclusive` is a pair of booleans that indicates whether
            the start and end ought to be included in the range,
            respectively. The default is ``(True, True)`` such that the range is
            inclusive of both start and end.
        """
        # correct minimum to include current tuplet sites
        safe_start = start
        if start:
            index = self._elements.bisect_right(safe_start) - 1
            if index >= 0:
                element = self._elements[self._elements.keys()[index]]
                if isinstance(element, Site):
                    safe_start = element.get_onset()
        # loop over sites recursively
        for key in self._elements.irange(safe_start, end, inclusive, reverse):
            element = self._elements[key]
            # recurse into Tuplet
            if isinstance(element, Site):
                yield from element.get_chords_and_rests(start, end, inclusive, reverse)
            else:
                yield element

    def get_first_chord_or_rest(self) -> ChordRest:
        return next(self.get_chords_and_rests())
    
    def get_last_chord_or_rest(self) -> ChordRest:
        element = self._elements.values()[-1]
        while isinstance(element, Site):
            element = element._elements.values()[-1]
        return element

    def append_note(self, note: Note, staff: Staff, note_type: NoteType, dots=0, stem: Stem = None) -> Chord:
        return self.insert_note(self.get_offset(), note, staff, note_type, dots, stem)
        
    def insert_note(self, onset: Fraction, note: Note, staff: Staff, note_type: NoteType, dots=0, stem: Stem = None) -> Chord:
        chord = Chord(note_type, dots, stem)
        chord._notes.add(note)
        note._chord = chord
        self.insert_chord_or_rest(onset, chord, staff)
        return chord

    def append_chord_or_rest(self, chord_rest: ChordRest, staff: Staff):
        self.insert_chord_or_rest(self.get_offset(), chord_rest, staff)

    def insert_chord_or_rest(self, onset: Fraction, chord_rest: ChordRest, staff: Staff):
        event = self.__get_or_create_event(staff, onset)
        event._chord_rests[self] = chord_rest
        chord_rest._event = event
        chord_rest._site = self
        self._elements[onset] = chord_rest

    def append_tuplet(self, tuplet: Tuplet):
        self.insert_tuplet(self.get_offset(), tuplet)

    def insert_tuplet(self, onset: Fraction, tuplet: Tuplet):
        tuplet._site = self
        self._elements[onset] = tuplet
        tuplet._onset = onset

    def __get_or_create_event(self, staff: Staff, onset: Fraction) -> Event:
        """
        Internal function used to get or create an event at a given onset and staff.
        """
        if onset in staff._events:
            return staff._events[onset]
        event = Event(staff, onset)
        staff._events[onset] = event
        return event
    
    def get_onset(self) -> Fraction:
        if len(self._elements) == 0:
            return ZERO
        self._elements[0].get_onset()

    def get_offset(self) -> Fraction:
        if len(self._elements) == 0:
            return ZERO
        # don't recurse into child sites!
        return self._elements.values()[-1].get_offset()
