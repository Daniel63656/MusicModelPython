from __future__ import annotations
from fractions import Fraction
from music_model import ZERO
from .collection import SafeDict, ContinuousMap
from .context import Clef, KeySignature, TimeSignature
from .enums import ClefType
from .staff import Staff
from .voice import Voice

import typing as t
if t.TYPE_CHECKING:
    from typing import Iterable, Optional
    from .score import Score
    from .enums import Instrument
    from .measure import Measure
    from .abstract import ChordRest


class Part():
    """
    Musical part in a score, representing a single instrument or 'track'. Holds staffs, voices and measures.

    Attributes:
    score (Score): The parent score of the part.
    idx (int): The index of the part in the score, serving as unique identifier.
    instrument (Instrument): The instrument of the part.
    staffs (dict): A dictionary for storing `Staff` objects with their respective id as key.
    voices (dict): A dictionary for storing `Voice` objects with their respective id as key.
    measures (dict): A dictionary for storing `Measure` objects as continuous `Range`s.
    """
    def __init__(self):
        self._score = None
        self._idx = None
        self._instrument = None     #TODO read from xml
        # these will auto-add staffs/voices if querrying a new key
        self._staffs = SafeDict(lambda id: self.insert_staff(id, Staff()))
        self._voices = SafeDict(lambda id: self.insert_voice(id, Voice()))
        self._measures = ContinuousMap()

    def get_score(self) -> Score:
        return self._score

    def get_idx(self) -> int:
        return self._idx
    
    def get_instrument(self) -> Instrument:
        return self._instrument

    def get_staffs(self) -> Iterable[Staff]:
        return self._staffs.values()
    
    def get_staff(self, id) -> Optional[Staff]:
        return self._staffs.get(id)
    
    def get_voices(self) -> Iterable[Voice]:
        return self._voices.values()
    
    def get_voice(self, id) -> Optional[Voice]:
        return self._voices.get(id)
    
    def get_measures(self) -> Iterable[Measure]:
        return self._measures.values()
    
    def get_measure(self, time: Fraction) -> Measure:
        return self._measures[time]
    
    def get_measure_by_index(self, idx: int) -> Measure:
        return self._measures.values()[idx]
    
    def get_chords_and_rests(self, start: Fraction=None, end: Fraction=None, borders=(True, False), reverse: bool=False) -> Iterable[ChordRest]:
        for staff in self._part._staffs.values():
            yield from staff.get_chords_and_rests(start, end, borders, reverse)

    def insert_staff(self, id: int, staff: Staff):
        """
        Insert a staff into the part. If the staff does not yet have context classes, standard contexts
        will be added to the staff. These are C Major, 4/4 and treble or bass clef depending on the staff `idx`.
        """
        self._staffs[id] = staff
        staff._part = self
        staff._id = id
        if not staff._clefs:
            if id == 0:
                staff.insert_clef(ZERO, Clef(ClefType.TREBLE))
            elif id == 1:
                staff.insert_clef(ZERO, Clef(ClefType.BASS))
        if not staff._key_signatures:
            staff.insert_key_signature(ZERO, KeySignature(0))
        if not staff._time_signatures:
            staff.insert_time_signature(ZERO, TimeSignature(4, 4))

    def insert_voice(self, id: int, voice: Voice):
        self._voices[id] = voice
        voice._part = self
        voice._id = id

    def insert_measure(self, onset: Fraction, measure: Measure):
        self._measures[onset] = measure
        measure._part = self
        measure._onset = onset

    def to_json(self):
        return {
            "instrument": self._instrument,
            "staffs": {staff_id: staff.to_json() for staff_id, staff in self._staffs.items()},
            "voices": {voice_id: voice.to_json() for voice_id, voice in self._voices.items()},
            "measures": [str(onset) for onset in self._measures.keys()]    # measures have no special attributes
        }
