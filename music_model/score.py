from __future__ import annotations
import warnings
from music_model import ZERO
from .collection import SortedMap, DiscontinuousMap
from .abstract import Range
from .measure import Measure
from .repeat import RepeatStart, RepeatEnd, Coda, Segno, ToCoda, Fine, Ending
from .repeat import JumpIterator

import typing as t
if t.TYPE_CHECKING:
    from fractions import Fraction
    from typing import Iterable
    from .part import Part
    from .repeat import RepeatMark, RepeatAction


class Score(Range):
    """
    Musical score. Contains score-level information and parts.

    Attributes:
    parts (List[Part]): The parts of the score.
    repeat_starts (SortedDict[Fraction, RepeatStart]): The repeat marks that start a repeat.
    segnos (SortedDict[Fraction, Segno]): The segno marks.
    codas (SortedDict[Fraction, Coda]): The coda marks.
    repeat_ends (SortedDict[Fraction, RepeatEnd]): The repeat marks that end a repeat.
    to_codas (SortedDict[Fraction, ToCoda]): The to coda marks.
    fines (SortedDict[Fraction, Fine]): The fine marks.
    repeat_commands (SortedDict[Fraction, RepeatAction]): The repeat commands.
    endings (DiscontinuousMap[Fraction, Ending]): The endings.
    """
    def __init__(self):
        self._parts = []
        # repeat related
        # repeat marks (points to jump to but don't initiate jumps itself)
        self._repeat_starts = SortedMap()
        self._segnos = SortedMap()
        self._codas = SortedMap()
        # repeat commands
        self._repeat_ends = SortedMap()
        self._to_codas = SortedMap()
        self._fines = SortedMap()  # TODO restrict to one?
        self._repeat_commands = SortedMap()    # only allows one command at a time
        # endings can act as both repeat marks and commands
        self._endings = DiscontinuousMap()

    def get_parts(self) -> Iterable[Part]:
        return self._parts

    def append_part(self, part: Part):
        """
        Append a part to the score, inserted at the end of the part list. If thr part has no
        measures, a default measure is inserted at 0.
        """
        self._parts.append(part)
        part._score = self
        part._idx = len(self._parts) - 1
        # insert standard measure if none exists
        if not part._measures:
            part.insert_measure(ZERO, Measure())

    def insert_repeat_mark(self, onset: Fraction, repeat_mark: RepeatMark):
        if isinstance(repeat_mark, RepeatStart):
            self._repeat_starts[onset] = repeat_mark
        elif isinstance(repeat_mark, Coda):
            self._codas[onset] = repeat_mark
        elif isinstance(repeat_mark, Segno):
            self._segnos[onset] = repeat_mark
        repeat_mark._score = self
        repeat_mark._onset = onset

    def insert_repeat_command(self, onset, repeat_cmd: RepeatAction):
        if isinstance(repeat_cmd, RepeatEnd):
            self._repeat_ends[onset] = repeat_cmd
        elif isinstance(repeat_cmd, ToCoda):
            self._to_codas[onset] = repeat_cmd
        elif isinstance(repeat_cmd, Fine):
            self._fines[onset] = repeat_cmd
        elif isinstance(repeat_cmd, Ending):
            self._endings[repeat_cmd._onset] = repeat_cmd
            warnings.warn("The 'onset' parameter is being ignored. This still works, but using 'add_ending()' for endings is recommended.", UserWarning)
        else:
            self._repeat_commands[onset] = repeat_cmd
        repeat_cmd._score = self
        repeat_cmd._onset = onset

    def add_ending(self, ending: Ending):
        self._endings[ending._onset] = ending
        ending._score = self

    def get_onset(self) -> Fraction:
        return ZERO

    def get_offset(self) -> Fraction:
        max_offset = ZERO
        for part in self._parts:
            for staff in part._staffs.values():
                if len(staff._events) > 0:
                    max_offset = max(max_offset, staff._events.values()[-1].get_offset())
        return max_offset

    def unfold(self):
        """
        Unfold all repeat marks and commands and return an `Iterator` of continuous sections, each defined by a tuple of start and end
        in score time. Useful for playback.
        """
        cursor = JumpIterator(self)
        time = ZERO
        for jump in cursor:
            print(f"{time} - {jump[0]}")
            time = jump[1]
        print(f"{time} - {cursor._time}")

    def to_json(self):
        return {
            "parts": [part.to_json() for part in self._parts]
        }
