# define what should be imported with 'from music_model import *'
__all__ = [
    'Accidental', 'ClefType', 'Clef', 'NoteName', 'NoteType', 'Stem', 'Octavation', 'Ornament', 'Dynamics',
    'Score', 'Part', 'Staff', 'Voice', 'Event', 'Element', 'ChordRest', 'Chord', 'GraceChord', 'Rest', 'Note',
    'OctaveShift', 'KeySignature', 'TimeSignature', 'BeamGroup', 'Tuplet', 'Measure', 'Site', 'Self'
]

# import Self type regardless of python version
import sys
if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

from .enums import Accidental, NoteName, ClefType, NoteType, Stem, Octavation, Ornament, Dynamics
from .score import Score
from .part import Part
from .site import Site
from .staff import Staff
from .voice import Voice
from .event import Event
from .abstract import Element, ChordRest
from .chord import Chord, GraceChord
from .rest import Rest
from .note import Note
from .context import Clef, KeySignature, TimeSignature
from .octave_shift import OctaveShift
from .beam_group import BeamGroup
from .tuplet import Tuplet
from .measure import Measure
