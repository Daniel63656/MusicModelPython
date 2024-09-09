from __future__ import annotations
import heapq
import warnings
from sortedcontainers import SortedDict, SortedSet
from .collection import DiscontinuousRangeMap
from .repeat import RepeatStart, RepeatEnd, Coda, Segno, Fine, Ending
from .repeat import Cursor

import typing as t
if t.TYPE_CHECKING:
    from fractions import Fraction
    from typing import Iterable
    from .part import Part
    from .repeat import RepeatMark, RepeatCommand


class Score():
    def __init__(self):
        self._parts = []
        # repeat related
        # repeat marks (points to jump to but don't initiate jumps itself)
        self._repeat_starts = SortedDict()
        self._segnos = SortedSet()
        self._codas = SortedSet()
        # repeat commands (conditionally triggered)
        self._repeat_ends = SortedDict()
        self._repeat_commands = SortedDict()    # only allows one repeat command at a time
        self._fines = SortedDict()
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

    def insert_repeat_command(self, onset, repeat_cmd: RepeatCommand):
        if isinstance(repeat_cmd, RepeatEnd):
            self._repeat_ends[onset] = repeat_cmd
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

    def unfold(self):
        cursor = Cursor(self)
        for jump in cursor:
            print(jump)
