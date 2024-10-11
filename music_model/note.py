from __future__ import annotations
from .enums import NoteName

import typing as t
if t.TYPE_CHECKING:
    from typing import Optional, Union
    from fractions import Fraction
    from .chord import Chord, GraceChord
    from .enums import Accidental, KeySignature


class Note():
    """
    Musical note, representing a pitch in a chord.
    
    Notes are specified by both an abolute pitch as well as a natural
    pitch (`NoteName` and octave). They can also have an `Accidental`, and can be tied to other notes.

    Attributes:
    chord (Chord | GraceChord): The (grace) chord the note belongs to.
    note_name (NoteName): The name of the note.
    octave (int): The octave of the note.
    pitch (int): The absolute pitch of the note.
    accidental (Accidental): The accidental of the note (optional).
    previous_tied (Note): The previous note tied to this one (optional).
    next_tied (Note): The next note tied to this one (optional).
    """
    def __init__(self, note_name: NoteName, octave: int, pitch: int, accidental: Accidental=None):
        self._chord = None
        self._note_name = note_name
        self._octave = octave
        self._pitch = pitch
        self._accidental = accidental
        self._previous_tied = None
        self._next_tied = None

    def get_chord(self) -> Union[Chord, GraceChord]:
        return self._chord

    def get_note_name(self) -> NoteName:
        return self._note_name
    
    def get_octave(self) -> int:
        return self._octave
    
    def get_pitch(self) -> int:
        return self._pitch
    
    def get_accidental(self) -> Accidental:
        return self._accidental
    
    def get_alteration(self) -> int:
        """
        Returns difference between natural and absolute pitch.
        """
        return self._pitch - (self._octave+1)*12 - self._note_name.value
    
    def get_previous_tied(self) -> Optional[Note]:
        return self._previous_tied
    
    def get_next_tied(self) -> Optional[Note]:
        return self._next_tied
    
    def is_tie_start(self) -> bool:
        return self._previous_tied is None and self._next_tied is not None
    
    def is_tie_end(self) -> bool:
        return self._previous_tied is not None and self._next_tied is None
    
    def get_onset(self) -> Fraction:
        return self._chord.get_onset()
    
    @staticmethod
    def tie_notes(note1: Note, note2: Note):
        if note1._pitch != note2._pitch:
            raise ValueError("Can't tie notes with different pitch values.")
        if note1.get_onset() > note2.get_onset():
            note1, note2 = note2, note1
        note1._next_tied = note2
        note2._previous_tied = note1

    def untie_with_next(self):
        if self._next_tied is None:
            return
        self._next_tied._previous_tied = None
        self._next_tied = None

    def untie_with_previous(self):
        if self._previous_tied is None:
            return
        self._previous_tied._next_tied = None
        self._previous_tied = None

    def untie(self):
        self.untie_with_next()
        self.untie_with_previous()

    @staticmethod
    def calculate_natural_pitch(key_signature: KeySignature, pitch: int, flatten: bool=False):
        """
        Compute the natural pitch for a given pitch in a given key signature.

        Parameters:
        key_signature (KeySignature): The current key signature.
        pitch (int): The absolute pitch value.
        flatten (bool): Whether to lower or raise the pitch by a semitone if it is non natural in the key signature.
        """
        alteration = 0
        # make pitch natural in this key
        if not key_signature.pitch_is_natural(pitch):
            if flatten:
                alteration = -1
            else:
                alteration = 1
        # account for accidentals of key signature (function of sharp/flat/natural can be different symbol in given key)
        if key_signature._fifths > 0:
            if key_signature.pitch_has_key_accidental(pitch - alteration - 1):
                alteration += 1
        elif key_signature._fifths < 0:
            if key_signature.pitch_has_key_accidental(pitch - alteration + 1):
                alteration -= 1
        # calculate octave and name
        octave = ((pitch - alteration) // 12) - 1
        name = NoteName((pitch - alteration) % 12)
        return name, octave, alteration
    
    def __str__(self):
        if self._accidental is None:
            return f"{self._note_name.name}{self._octave}({self._pitch})"
        return f"{self._note_name.name}{self._accidental}{self._octave}({self._pitch})"
    
    def to_json(self):
        return {
            "note_name": self._note_name.name,
            "octave": self._octave,
            "pitch": self._pitch,
            "accidental": self._accidental.value if self._accidental is not None else None,
            "previous_tied": False if self._previous_tied is None else True,
            "next_tied": False if self._next_tied is None else True
        }
