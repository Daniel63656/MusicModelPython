from __future__ import annotations
from sortedcontainers import SortedDict, SortedSet
from .abstract import Range
from enum import Enum

import typing as t
if t.TYPE_CHECKING:
    from fractions import Fraction


class RepeatMark(Enum):
    CODA = 0
    SEGNO = 1
    FINE = 2
    # BAR_REPEAT = 3


class RepeatCommand(Enum):
    DA_CAPO = (None, None)
    DA_CAPO_AL_FINE = (None, RepeatMark.FINE)
    DA_CAPO_AL_CODA = (None, RepeatMark.CODA)
    DAL_SEGNO = (RepeatMark.SEGNO, None)
    DAL_SEGNO_AL_FINE = (RepeatMark.SEGNO, RepeatMark.FINE)
    DAL_SEGNO_AL_CODA = (RepeatMark.SEGNO, RepeatMark.CODA)


class RepeatManager():
    def __init__(self):
        self._repeat_starts = SortedSet()
        self._repeat_ends = SortedSet()
        self._endings = SortedDict()
        self._repeat_marks = SortedDict()       # only allows one repeat mark at a time
        self._repeat_commands = SortedDict()    # only allows one repeat command at a time

    def solve_repeats(self):
        pass      

    def invalidate(self):
        pass





class Repeat(Range):
    """
    Class to model a repetition inclusive different endings (volta brackets). Onset and offset describe the whole range
    inclusive endings.
            1,2___3____4_____,
      |:    |    :|   :|     |
    onset   e1    e2   e3  offset        where endings = {(e1 -> 2), (e2 -> 1), (e3 -> 1)}
    """
    def __init__(self, onset: Fraction, offset: Fraction):
        self._score = None
        self._onset = onset
        self._offset = offset
        # ending's offset is equal to the next ending's onset or to repetition offset if last ending
        self._endings = SortedDict()
    
    def add_ending(self, onset: Fraction, count: int=1):
        self._endings[onset] = count

    def get_onset(self) -> Fraction:
        return self._onset
        
    def get_offset(self) -> Fraction:
        return self._offset
