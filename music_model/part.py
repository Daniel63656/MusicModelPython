from __future__ import annotations
from .collection import SafeDict, ContinuousRangeMap
from .staff import Staff
from .voice import Voice

import typing as t
if t.TYPE_CHECKING:
    from typing import Iterable, Optional
    from fractions import Fraction
    from .score import Score
    from .measure import Measure
    from .abstract import ChordRest


class Part():
    def __init__(self):
        self._score = None
        self._idx = None
        self._instrument = None     #TODO read from xml
        # these will auto-add staffs/voices if querrying a new key
        self._staffs = SafeDict(lambda id: self.insert_staff(id, Staff()))
        self._voices = SafeDict(lambda id: self.insert_voice(id, Voice()))
        self._measures = ContinuousRangeMap()

    def get_score(self) -> Score:
        return self._score

    def get_idx(self) -> int:
        return self._idx

    def get_staffs(self) -> Iterable[Staff]:
        return self._staffs.values()
    
    def get_staff(self, id) -> Optional[Staff]:
        return self._staffs.get(id)
    
    def get_voices(self) -> Iterable[Voice]:
        return self._voices.values()
    
    def get_voice(self, id) -> Optional[Voice]:
        return self._voices.get(id)
    
    def get_measure(self, time: Fraction) -> Measure:
        return self._measures[time]
    
    def get_measures(self) -> Iterable[Measure]:
        return self._measures.values()
    
    def get_measure_by_index(self, idx: int) -> Measure:
        return self._measures.values()[idx]
    
    def get_chords_and_rests(self, start: Fraction=None, end: Fraction=None, borders=(True, False), reverse: bool=False, use_unfolded_time: bool=False) -> Iterable[ChordRest]:
        for staff in self._part._staffs.values():
            yield from staff.get_chords_and_rests(start, end, borders, reverse, use_unfolded_time)

    def insert_staff(self, id: int, staff: Staff):
        self._staffs[id] = staff
        staff._part = self
        staff._id = id

    def insert_voice(self, id: int, voice: Voice):
        self._voices[id] = voice
        voice._part = self
        voice._id = id

    def insert_measure(self, onset: Fraction, measure: Measure):
        self._measures[onset] = measure
        measure._part = self
        measure._onset = onset
