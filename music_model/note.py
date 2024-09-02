from __future__ import annotations
from .abstract import Range

import typing as t
if t.TYPE_CHECKING:
    from typing import Optional
    from fractions import Fraction
    from .enums import NoteName, Accidental


class Note(Range):
    def __init__(self, note_name: NoteName, octave: int, pitch: int, accidental: Accidental=None):
        self._chord = None
        self._note_name = note_name
        self._octave = octave
        self._pitch = pitch
        self._accidental = accidental
        self._previous_tied = None
        self._next_tied = None

    def get_note_name(self) -> NoteName:
        return self._note_name
    
    def get_octave(self) -> int:
        return self._octave
    
    def get_pitch(self) -> int:
        return self._pitch
    
    def get_accidental(self) -> Accidental:
        return self._accidental
    
    def get_previous_tied(self) -> Optional[Note]:
        return self._previous_tied
    
    def get_next_tied(self) -> Optional[Note]:
        return self._next_tied

    def get_alter(self) -> int:
        return self._pitch - (self._octave+1)*12 - self._note_name.value
    
    def get_onset(self) -> Fraction:
        return self._chord.get_onset()
    
    def get_offset(self) -> Fraction:
        return self.get_onset() + self._chord.get_duration()
    
    @staticmethod
    def tie_notes(note1: Note, note2: Note):
        if note1._pitch != note2._pitch:
            raise RuntimeError("Can't tie notes with different pitches.")
        if note1.get_onset() > note2.get_onset():
            note1, note2 = note2, note1
        note1._next_tied = note2
        note2._previous_tied = note1
    
    def __str__(self):
        if self._accidental is None:
            return f"{self._note_name}{self.octave}({self.pitch})"
        return f"{self._note_name}{self.accidental}{self.octave}({self.pitch})"
