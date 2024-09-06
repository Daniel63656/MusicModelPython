from __future__ import annotations
from .abstract import NavigableRange, ChordRest
from .enums import NoteType, Stem, Ornament

import typing as t
if t.TYPE_CHECKING:
    from . import Self
    from typing import Optional, Iterable
    from fractions import Fraction
    from .staff import Staff
    from .voice import Voice
    from .measure import Measure
    from .note import Note
    from .beam_group import BeamGroup


class Chord(ChordRest):
    def __init__(self, note_type: NoteType, dots: int = 0, stem: Stem = None):
        super().__init__(note_type, dots)
        if note_type is NoteType.WHOLE and stem is not None:
            raise ValueError("chords with NoteType 'whole' can't have a stem.")
        self._grace_chords = []
        self._ornaments = set()
        self._notes = set()
        self._stem = stem

    def add_note(self, note: Note):
        self._notes.add(note)
        note._chord = self

    def get_notes(self) -> Iterable[Note]:
        return self._notes
    
    def get_stem(self) -> Stem:
        return self._stem
    
    def get_grace_chords(self) -> Iterable[GraceChord]:
        return self._grace_chords

    def add_grace_chord(self, grace_chord: GraceChord):
        self._grace_chords.append(grace_chord)
        grace_chord._chord = self
        grace_chord._idx = len(self._grace_chords)

    def add_ornament(self, ornament: Ornament):
        self._ornaments.add(ornament)

    def get_ornament(self) -> Iterable[Ornament]:
        return self._ornaments

    def get_duration(self) -> Fraction:
        duration = self._note_type.get_value(self._dots)
        site = self._site
        # can't use isinstance here becuase this would cause circular dependencies!
        while hasattr(site, "_site"):
            duration *= site._time_mod
            site = site._site
        return duration
    
    def __str__(self):
        dots_str = '.' * self._dots
        notes_str = ', '.join(str(note) for note in self._notes)
        return f"Chord({self._note_type}{dots_str}, Notes: [{notes_str}])"
    

class GraceChord(NavigableRange):
    def __init__(self, note_type: NoteType, dots: int = 0, stem: Stem = None):
        if note_type is NoteType.WHOLE and stem is not None:
            raise ValueError("chords with NoteType 'whole' can't have a stem.")
        self._chord = None
        self._idx = None
        self._note_type = note_type
        self._dots = dots
        self._ornaments = set()
        self._notes = set()
        self._stem = stem
        self._beam_group = None

    def get_note_type(self) -> NoteType:
        return self._note_type
    
    def get_dots(self) -> int:
        return self._dots
    
    def get_stem(self) -> Stem:
        return self._stem
    
    def get_notes(self) -> Iterable[Note]:
        return self._notes
    
    def add_ornament(self, ornament: Ornament):
        self._ornaments.add(ornament)

    def get_ornament(self) -> Iterable[Ornament]:
        return self._ornaments

    def get_staff(self) -> Staff:
        return self._chord.get_staff()

    def get_measure(self) -> Measure:
        return self._chord.get_measure()
    
    def get_voice(self) -> Voice:
        return self._chord.get_voice()
    
    def get_beam_group(self) -> BeamGroup:
        return self._beam_group
    
    def get_onset(self) -> Fraction:
        return self._chord.get_onset()
        
    def get_offset(self) -> Fraction:
        return Fraction(0, 1)
    
    def next(self) -> Optional[Self]:
        if self._idx + 1 >= len(self._chord._grace_chords):
            return None
        return self._chord._grace_chords[self._idx + 1]
    
    def previous(self) -> Optional[Self]:
        if self._idx < 1:
            return None
        return self._chord._grace_chords[self._idx - 1]
    
    def get_index(self) -> int:
        return self._idx

    def add_note(self, note: Note):
        self._notes.add(note)
        note._chord = self
    
    def __str__(self):
        dots_str = '.' * self._dots
        notes_str = ', '.join(str(note) for note in self._notes)
        return f"GraceChord({self._note_type}{dots_str}, Notes: [{notes_str}])"
