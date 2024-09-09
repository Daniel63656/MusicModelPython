from __future__ import annotations
from abc import ABC, abstractmethod
from sortedcontainers import SortedDict, SortedSet
from fractions import Fraction
from .abstract import Range

import typing as t
if t.TYPE_CHECKING:
    from .score import Score


class RepeatMark(ABC):
    def __init__(self):
        self._score = None
        self._onset = None

    # comparison methods for sorting
    def __gt__(self, other):
        return self._onset > other._onset
    def __lt__(self, other):
        return self._onset < other._onset


class RepeatStart(RepeatMark):
    pass


class Coda(RepeatMark):
    pass


class Segno(RepeatMark):
    pass


class RepeatCommand(ABC):
    def __init__(self):
        self._score = None
        self._onset = None

    @abstractmethod
    def jump(self) -> Fraction:
        pass

    # comparison methods for sorting
    def __gt__(self, other):
        return self._onset > other._onset
    def __lt__(self, other):
        return self._onset < other._onset


class RepeatEnd(RepeatCommand):
    def __init__(self):
        super().__init__()
        self._iterations = 2

    def jump(self) -> Fraction:
        # jump to closest prior repeat start by finding lower entry. If None, return begin of score
        idx = self._score._repeat_starts.bisect_left(self._onset)
        if idx > 0:     # idx > 0 if such an entry exists
            return self._score._repeat_starts.values()[idx - 1]._onset
        return Fraction(0, 1)


class DaCapo(RepeatCommand):
    def __init__(self, al: str=''):
        super().__init__()
        if al not in {'', 'Fine', 'Coda'}:
            raise ValueError(f"Invalid value for 'al': {al}. Must be empty, 'Fine' or 'Coda'.")
        self._al = al

    def jump(self) -> Fraction:
        return Fraction(0, 1)
    
    def __str__(self):
        return f"D.C.{f' al {self._al}' if self._al else ''}"


class DalSegno(RepeatCommand):
    def __init__(self, al: str=''):
        super().__init__()
        if al not in {'', 'Fine', 'Coda'}:
            raise ValueError(f"Invalid value for 'al': {al}. Must be empty, 'Fine' or 'Coda'.")
        self._al = al

    def jump(self) -> Fraction:
        # jump to closest prior Segno by finding lower entry. If None, throw error
        idx = self._score._segnos.bisect_left(self._onset)
        if idx > 0:     # idx > 0 if such an entry exists
            return self._score._segnos[idx - 1]._onset
        raise ValueError("No Segno found to jump to.")
    
    def __str__(self):
        return f"D.S.{f' al {self._al}' if self._al else ''}"


class ToCoda(RepeatCommand):
    def __init__(self):
        super().__init__()

    def jump(self) -> Fraction:
        # jump to next coda by finding higher entry. If None, throw error
        idx = self._score._codas.bisect_right(self._onset)
        if idx < len(self._score._codas):
            return self._score._codas[idx]._onset
        raise ValueError("No Coda found to jump to.")
    
    def __str__(self):
        return "To Coda"
    

class Fine(RepeatCommand):
    def __init__(self):
        super().__init__()

    def jump(self) -> Fraction:
        return self._score.get_offset()
    
    def __str__(self):
        return "Fine"


class Ending(RepeatCommand):
    def __init__(self, onset: Fraction, offset: Fraction, numbers: set[int]):
        super().__init__()
        self._onset = onset
        self._offset = offset
        self._numbers = numbers

    def jump(self) -> Fraction:
        # only call if repeat_count not in self._numbers
        return self._offset


import heapq
class Cursor:
    def __init__(self, score, start_time: Fraction = Fraction(0, 1)):
        self._score = score
        self._time = start_time
        self._repeat_iteration = 1
    
    def _get_next_jump(self) -> RepeatCommand:
        closest = None
        # TODO only check repeat ends if not in DS/DC
        idx = self._score._repeat_ends.bisect_right(self._time)
        if idx < len(self._score._repeat_ends):
            candidate = self._score._repeat_ends.values()[idx]
            if closest is None or candidate._onset < closest._onset:
                closest = candidate
        # check commands
        idx = self._score._repeat_commands.bisect_right(self._time)
        if idx < len(self._score._repeat_commands):
            candidate = self._score._repeat_commands.values()[idx]
            if closest is None or candidate._onset < closest._onset:
                closest = candidate
        # return closest or stop
        if closest is None:
            raise StopIteration
        return closest

    def __iter__(self):
        return self  # Cursor is its own iterator

    def __next__(self):
        while True:
            next_jump = self._get_next_jump()
            if isinstance(next_jump, RepeatEnd):
                # maximal number of repeats done, reset repeat_iteration and ignore RepeatEnd
                if self._repeat_iteration >= next_jump._iterations:
                    self._repeat_iteration = 1
                else:
                    self._repeat_iteration += 1
                    self._time = next_jump.jump()
                    return next_jump._onset, self._time
            elif isinstance(next_jump, RepeatCommand):
                self._time = next_jump.jump()
                return next_jump._onset, self._time
            # if not applied, advance time to unapplied jump onset
            self._time = next_jump._onset

        
        






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
