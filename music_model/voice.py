from __future__ import annotations
from .site import Site
from .enums import NoteType, Stem

import typing as t
if t.TYPE_CHECKING:
    from .part import Part
    from .note import Note
    from .staff import Staff
    from .chord import Chord
    from .abstract import ChordRest, Tuplet


class Voice(Site):
    """
    Musical voice, owned by a part. Extends the `Site` class.

    Inherits:
    elements (SortedDict): A sorted dictionary of elements contained in the voice.

    Attributes:
    part (Part): The part the voice belongs to.
    id (int): The index of the voice in the part collection, serving as unique identifier.
    """
    def __init__(self):
        super().__init__()
        self._part = None
        self._id = None

    def get_part(self) -> Part:
        return self._part

    def get_id(self) -> int:
        return self._id
    
    def append_note(self, note: Note, staff: Staff, note_type: NoteType, dots=0, stem: Stem = None) -> Chord:
        return self.insert_note(self.get_offset(), note, staff, note_type, dots, stem)
    
    def append_chord_or_rest(self, chord_rest: ChordRest, staff: Staff):
        self.insert_chord_or_rest(self.get_offset(), chord_rest, staff)
        
    def append_tuplet(self, tuplet: Tuplet):
        self.insert_tuplet(self.get_offset(), tuplet)
    
    def to_json(self):
        # Collect beams from elements
        beams = set()
        for cr in self.get_chords_and_rests():
            if cr.get_beam_group() is not None:
                beams.add(cr.get_beam_group())
            if cr.__class__.__name__ == "Chord":
                for grace_chord in cr.get_grace_chords():
                    if grace_chord.get_beam_group() is not None:
                        beams.add(grace_chord.get_beam_group())
        sorted_beams = sorted(beams, key=lambda b: b.get_onset())

        return {
            "id": self._id,
            "elements": {str(onset): element.to_json() for onset, element in self._elements.items()},
            "beams": [beam.to_json() for beam in sorted_beams]
        }
