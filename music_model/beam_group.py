from __future__ import annotations
from .abstract import Range
from .chord import GraceChord
from sortedcontainers import SortedList

import typing as t
if t.TYPE_CHECKING:
    from typing import Iterator, Union
    from fractions import Fraction
    from .abstract import ChordRest
    from .voice import Voice
    

class BeamGroup(Range):
    """
    A group of chords and rests that are beamed together. Beams can only encompass chords and rests of the same voice.

    Attributes:
    voice (Voice): The voice that the beam group belongs to.
    chord_rests (SortedList): A sorted list of the chords and rests contained in the beam group.
    """
    def __init__(self) -> None:
        self._voice = None
        self._grace_beam = False    # True if the beam group contains grace chords. Can't have both.
        self._chord_rests = SortedList(key=lambda e: e.get_index() if isinstance(e, GraceChord) else e.get_onset())

    def add_chord_or_rest(self, chord_rest: Union[GraceChord, ChordRest]):
        try:
            voice = chord_rest.get_voice()
        except:
            raise ValueError("No voice found. Add chords and rests to their site and grace chord to its chord respectively before adding to beam.")
        if self._voice is None:
            self._voice = voice
            if isinstance(chord_rest, GraceChord):
                self._grace_beam = True
        else:
            assert chord_rest.get_voice() == self._voice, "Beamed chords and rests must share the same voice."
            assert isinstance(chord_rest, GraceChord) == self._grace_beam, "Beams can't encompass both grace and non grace chords."
        assert chord_rest._note_type._base2_exponent < -2, "Can't beam chords and rests of this NoteType."
        self._chord_rests.add(chord_rest)
        chord_rest._beam_group = self

    def get_voice(self) -> Voice:
        return self._voice
    
    def get_chords_and_rests(self) -> Iterator[Union[GraceChord, ChordRest]]:
        return self._chord_rests
    
    def get_onset(self) -> Fraction:
        return self._chord_rests[0].get_onset()
        
    def get_offset(self) -> Fraction:
        return self._chord_rests[-1].get_onset()
    
    def encloses(self, time: Fraction) -> bool:
        # make end key incluse
        return self.get_onset() <= time <= self.get_offset()
