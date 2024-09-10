from __future__ import annotations
import warnings
from fractions import Fraction
from sortedcontainers import SortedDict
from .collection import DiscontinuousRangeMap
from .abstract import Range
from .repeat import RepeatStart, RepeatEnd, Coda, Segno, ToCoda, Fine, Ending
from .repeat import JumpIterator

import typing as t
if t.TYPE_CHECKING:
    from typing import Iterable
    from .part import Part
    from .repeat import RepeatMark, RepeatAction


class Score(Range):
    def __init__(self):
        self._parts = []
        # repeat related
        # repeat marks (points to jump to but don't initiate jumps itself)
        self._repeat_starts = SortedDict()
        self._segnos = SortedDict()
        self._codas = SortedDict()
        # repeat commands
        self._repeat_ends = SortedDict()
        self._to_codas = SortedDict()
        self._fines = SortedDict()  # TODO restrict to one?
        self._repeat_commands = SortedDict()    # only allows one command at a time
        # endings can act as both repeat marks and commands
        self._endings = DiscontinuousRangeMap()

    def get_parts(self) -> Iterable[Part]:
        return self._parts

    def append_part(self, part: Part):
        self._parts.append(part)
        part._score = self
        part._idx = len(self._parts) - 1

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
        return Fraction(0, 1)

    def get_offset(self) -> Fraction:
        max_offset = Fraction(0, 1)
        for part in self._parts:
            for staff in part._staffs.values():
                if len(staff._events) > 0:
                    max_offset = max(max_offset, staff._events.values()[-1].get_offset())
        return max_offset

    def unfold(self):
        cursor = JumpIterator(self)
        time = Fraction(0, 1)
        for jump in cursor:
            print(f"{time} - {jump[0]}")
            time = jump[1]
        print(f"{time} - {cursor._time}")
