from __future__ import annotations
from sortedcontainers import SortedDict
from .collection import ContinuousRangeMap, DiscontinuousRangeMap
from .abstract import Range

import typing as t
if t.TYPE_CHECKING:
    from typing import Iterator, Iterable, Optional
    from fractions import Fraction
    from .part import Part
    from .event import Event
    from .abstract import ChordRest
    from .enums import Clef, Ottavation
    from .signatures import KeySignature, TimeSignature
    from .octave_shift import OctaveShift
    from .measure import Measure


class Staff(Range):
    def __init__(self):
        self._part = None
        self._id = None
        self._events = SortedDict()
        self._measures = ContinuousRangeMap()
        self._clefs = ContinuousRangeMap()
        self._key_signatures = ContinuousRangeMap()
        self._time_signatures = ContinuousRangeMap()
        self._octave_shifts = DiscontinuousRangeMap()

    def get_part(self) -> Part:
        return self._part

    def get_id(self) -> int:
        return self._id
    
    def get_events(self, start: Fraction = None, end: Fraction = None, inclusive=(True, True), reverse: bool = False) -> Iterator[Event]:
        """ Create an iterator of events between `start` and `end`.

            Both `start` and `end` default to `None` which is automatically
            inclusive of the beginning and end.

            The argument `inclusive` is a pair of booleans that indicates whether
            the start and end ought to be included in the range,
            respectively. The default is ``(True, True)`` such that the range is
            inclusive of both start and end.)
        """ 
        return (self._events[key] for key in self._events.irange(start, end, inclusive, reverse))
    
    def get_event(self, time: Fraction) -> Optional[Event]:
        """ Get the event at an exact time or None if no event exists at that time.
        """
        return self._events[time]
    
    def get_chords_and_rests(self, start: Fraction = None, end: Fraction = None, borders = (True, False), reverse: bool = False) -> Iterator[ChordRest]:
        """ Create an iterator of chords and rests between `start` and `end`.

            Both `start` and `end` default to `None` which is automatically
            inclusive of the beginning and end.

            The argument `inclusive` is a pair of booleans that indicates whether
            the start and end ought to be included in the range,
            respectively. The default is ``(True, True)`` such that the range is
            inclusive of both start and end.)
        """ 
        for event in self.get_events(start, end, borders, reverse):
            yield event._chord_rests.values()

    def get_measure(self, time: Fraction) -> Measure:
        return self._measures[time]
    
    def get_measure_by_index(self, idx: int) -> Measure:
        return self._measures.values()[idx]
    
    def get_clef(self, time: Fraction) -> Clef:
        return self._clefs[time]
    
    def get_clefs(self) -> Iterable[tuple[Fraction, Clef]]:
        return self._clefs.items()
    
    def get_key_signature(self, time: Fraction) -> KeySignature:
        return self._key_signatures[time]
    
    def get_key_signatures(self) -> Iterable[tuple[Fraction, KeySignature]]:
        return self._key_signatures.items()
    
    def get_time_signature(self, time: Fraction) -> TimeSignature:
        return self._time_signatures[time]
    
    def get_time_signatures(self) -> Iterable[tuple[Fraction, TimeSignature]]:
        return self._time_signatures.items()
    
    def get_ottavation(self, time: Fraction) -> Ottavation:
        range = self._octave_shifts[time]
        return None if range is None else range._ottavation
    
    def insert_measure(self, onset: Fraction, measure: Measure):
        self._measures[onset] = measure
        measure._staff = self
        measure._onset = onset

    def insert_clef(self, onset: Fraction, clef: Clef):
        self._clefs[onset] = clef

    def insert_key_signature(self, onset: Fraction, key_signature: KeySignature):
        self._key_signatures[onset] = key_signature

    def insert_time_signature(self, onset: Fraction, time_signature: TimeSignature):
        self._time_signatures[onset] = time_signature

    def insert_octave_shift(self, octave_shift: OctaveShift):
        self._octave_shifts[octave_shift._onset] = octave_shift

    def get_onset(self) -> Fraction:
        if len(self._events) == 0:
            return Fraction(0, 1)
        self._events[0]._onset

    def get_offset(self) -> Fraction:
        if len(self._events) == 0:
            return Fraction(0, 1)
        return self._events.values()[-1].get_offset()
