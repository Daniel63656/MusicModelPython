from __future__ import annotations
from .abstract import NavigableRange, ChordRest
from .enums import NoteType, Stem
from music_model import ZERO

import typing as t
if t.TYPE_CHECKING:
    from . import Self
    from typing import Optional, Iterable
    from fractions import Fraction
    from .enums import Expression
    from .staff import Staff
    from .voice import Voice
    from .measure import Measure
    from .note import Note
    from .beam_group import BeamGroup


class Chord(ChordRest):
    """
    A class that represents a collection of `Note`s played simultaneously, sharing the same `Voice`, `Staff`, `Stem` and duration.

    Inherits:
    site (Site): The owning `Site` of the chord.
    event (Event): The owning `Event` of the chord.
    beam_group (BeamGroup): The `BeamGroup` that contains this chord (optional).
    note_type (NoteType): The duration type of the element. Together with `dots`, this specifies nominal duration.
    dots (int): The number of dots.
    fermata (bool): Whether the chord has a fermata.

    Attributes:
    notes (set[Note]): The notes that belong to the chord.
    stem (Stem): The stem of the chord (optional).
    grace_chords (list[GraceChord]): The grace chords that are played before the chord.
    expressions (set[Expression]): The expressions that are applied to the chord.
    """
    def __init__(self, note_type: NoteType, dots: int=0, stem: Stem=None, visible: bool=True):
        super().__init__(note_type, dots, visible)
        if note_type is NoteType.WHOLE and stem is not None:
            raise ValueError("chords with NoteType 'whole' can't have a stem.")
        self._notes = set()
        self._stem = stem
        self._grace_chords = []
        self._expressions = set()

    def get_notes(self) -> Iterable[Note]:
        return self._notes
    
    def get_stem(self) -> Stem:
        return self._stem
    
    def get_grace_chords(self) -> Iterable[GraceChord]:
        return self._grace_chords

    def add_expression(self, expression: Expression):
        self._expressions.add(expression)

    def get_expression(self) -> Iterable[Expression]:
        return self._expressions
    
    def add_note(self, note: Note):
        self._notes.add(note)
        note._chord = self

    def add_grace_chord(self, grace_chord: GraceChord):
        self._grace_chords.append(grace_chord)
        grace_chord._chord = self
        grace_chord._idx = len(self._grace_chords)
    
    def __str__(self):
        dots_str = '.' * self._dots
        notes_str = ', '.join(str(note) for note in self._notes)
        return f"Chord({self._note_type}{dots_str}, Notes: [{notes_str}])"

    def to_json(self):
        return {
            "staff": self.get_staff().get_id(),
            "note_type": self._note_type.name,
            "dots": self._dots,
            "fermata": self._fermata,
            "notes": [note.to_json() for note in self._notes],
            "stem": self._stem.name if self._stem is not None else None,
            "grace_chords": [grace_chord.to_json() for grace_chord in self._grace_chords],
            "expressions": [expression.name for expression in self._expressions],
            "visible": self._visible
        }


class GraceChord(NavigableRange):
    """
    A class that represents a collection of `Note`s played together as grace notes.

    Attributes:
    chord (Chord): The owning `Chord` of the grace chord.
    idx (int): The index of the grace chord in the owning chord's list, used as unique identifier and for navigation.
    note_type (NoteType): The duration type of the element. Together with `dots`, this specifies nominal duration.
    dots (int): The number of dots.
    stem (Stem): The stem of the grace chord (optional).
    beam_group (BeamGroup): The `BeamGroup` that contains this grace chord (optional).
    notes (set[Note]): The notes that belong to the grace chord.
    expressions (set[Expression]): The expressions that are applied to the grace chord.
    """
        
    def __init__(self, note_type: NoteType, dots: int = 0, stem: Stem = None):
        if note_type is NoteType.WHOLE and stem is not None:
            raise ValueError("chords with NoteType 'whole' can't have a stem.")
        self._chord = None
        self._idx = None
        self._note_type = note_type
        self._dots = dots
        self._stem = stem
        self._beam_group = None
        self._notes = set()
        self._expressions = set()

    def get_chord(self) -> Chord:
        return self._chord
    
    def get_index(self) -> int:
        return self._idx
    
    def get_note_type(self) -> NoteType:
        return self._note_type
    
    def get_dots(self) -> int:
        return self._dots
    
    def get_stem(self) -> Stem:
        return self._stem
    
    def get_beam_group(self) -> BeamGroup:
        return self._beam_group
    
    def get_notes(self) -> Iterable[Note]:
        return self._notes

    def get_expression(self) -> Iterable[Expression]:
        return self._expressions

    def get_staff(self) -> Staff:
        return self._chord.get_staff()

    def get_measure(self) -> Measure:
        return self._chord.get_measure()
    
    def get_voice(self) -> Voice:
        return self._chord.get_voice()
    
    def get_onset(self) -> Fraction:
        return self._chord.get_onset()
        
    def get_offset(self) -> Fraction:
        return self._chord.get_onset()
    
    def get_duration(self) -> Fraction:
        return ZERO
    
    def add_note(self, note: Note):
        self._notes.add(note)
        note._chord = self

    def add_expression(self, expression: Expression):
        self._expressions.add(expression)
    
    def next(self) -> Optional[Self]:
        if self._idx + 1 >= len(self._chord._grace_chords):
            return None
        return self._chord._grace_chords[self._idx + 1]
    
    def previous(self) -> Optional[Self]:
        if self._idx < 1:
            return None
        return self._chord._grace_chords[self._idx - 1]
    
    def __str__(self):
        dots_str = '.' * self._dots
        notes_str = ', '.join(str(note) for note in self._notes)
        return f"GraceChord({self._note_type}{dots_str}, Notes: [{notes_str}])"

    def to_json(self):
        return {
            "note_type": self._note_type.name,
            "dots": self._dots,
            "notes": [note.to_json() for note in self._notes],
            "stem": self._stem.name if self._stem is not None else None,
            "expressions": [expression.name for expression in self._expressions]
        }
