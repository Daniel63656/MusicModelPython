from abc import ABC, abstractmethod
from sortedcontainers import SortedDict
from fractions import Fraction
from .abstract import Range



class RepeatMark(ABC):
    """
    Base class for marks that indicate return or jump points but do not trigger jumps themselves.
    They are positioned at measure onsets.
    """
    def __init__(self):
        self._score = None
        self._onset = None

    # comparison methods for sorting
    def __gt__(self, other):
        return self._onset > other._onset
    def __lt__(self, other):
        return self._onset < other._onset


class RepeatStart(RepeatMark):
    def __init__(self):
        super().__init__()


class Coda(RepeatMark):
    def __init__(self):
        super().__init__()


class Segno(RepeatMark):
    def __init__(self):
        super().__init__()


class RepeatCommand(ABC):
    """
    Base class for commands that trigger a jump in the score (if certain condidions are fulfilled).
    They are placed at measure offsets, while `Endings` must start and end on measure boundaries.
    """
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


class ToCoda(RepeatCommand):
    def __init__(self):
        super().__init__()

    def jump(self) -> Fraction:
        # jump to next coda by finding higher entry. If None, throw error
        idx = self._score._codas.bisect_right(self._onset)
        if idx < len(self._score._codas):
            return self._score._codas.values()[idx]._onset
        raise ValueError("No Coda found to jump to.")
    
    def __str__(self):
        return "To Coda"


class Fine(RepeatCommand):
    def __init__(self):
        super().__init__()

    def jump(self) -> Fraction:
        # jump to end of score
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
        # applied skip if ending not appled
        return self._offset


class RepeatAdvance(RepeatCommand):
    """
    Repeat command of the form: Da/Dal [return point] (al [destination]), where the jump to the return point 
    is followed by continuous play until the destination (`Fine`, `ToCoda` or `Self`) is reached.
    """
    def __init__(self, al: str=''):
        super().__init__()
        if al not in {'', 'Fine', 'Coda'}:
            raise ValueError(f"Invalid value for 'al': {al}. Must be empty, 'Fine' or 'Coda'.")
        self._al = al

    def get_destination(self) -> RepeatCommand:
        if self._al is '':
            return self
        if self._al == 'Fine':
            # jump to fine by finding higher entry. If None, throw error
            idx = self._score._fines.bisect_right(self._onset)
            if idx < len(self._score._fines):
                return self._score._fines.values()[idx]
            raise ValueError("Fine not found.")
        if self._al == 'Coda':
            # jump to next ToCoda by finding higher entry. If None, throw error
            idx = self._score._to_codas.bisect_right(self._onset)
            if idx < len(self._score._to_codas):
                return self._score._to_codas.values()[idx]
            raise ValueError("No ToCoda destination found.")
    
    # to keep class abstract
    @abstractmethod
    def prefix(self) -> str:
        pass

    def __str__(self):
        return f"{self.prefix}{f' al {self._al}' if self._al else ''}"


class DaCapo(RepeatAdvance):
    def __init__(self, al: str=''):
        super().__init__()
        if al not in {'', 'Fine', 'Coda'}:
            raise ValueError(f"Invalid value for 'al': {al}. Must be empty, 'Fine' or 'Coda'.")
        self._al = al

    def jump(self) -> Fraction:
        return Fraction(0, 1)
    
    def prefix(self) -> str:
        return "D.C."
    
    def __str__(self):
        return f"D.C.{f' al {self._al}' if self._al else ''}"


class DalSegno(RepeatAdvance):
    def __init__(self, al: str=''):
        super().__init__()
        if al not in {'', 'Fine', 'Coda'}:
            raise ValueError(f"Invalid value for 'al': {al}. Must be empty, 'Fine' or 'Coda'.")
        self._al = al

    def jump(self) -> Fraction:
        #TODO what if Segno lies in the future?
        # jump to closest prior Segno by finding lower entry. If None, throw error
        idx = self._score._segnos.bisect_left(self._onset)
        if idx > 0:     # idx > 0 if such an entry exists
            return self._score._segnos.values()[idx - 1]._onset
        raise ValueError("No Segno found to jump to.")
    
    def prefix(self) -> str:
        return "D.S."
    
    def __str__(self):
        return f"D.S.{f' al {self._al}' if self._al else ''}"


class JumpIterator:
    """
    An iterator for traversing a musical score and yielding jumps as (jump from, jump to) pairs.
    
    This iterator handles jumps based on the repeat marks and commands of the musical score, starting from a specified time. Jumps are 
    expressed in `ScoreTime`, and iteration begins at the provided `start_time`.

    Example usage to unfold the score into contiguous sections:
        >>> it = JumpIterator(score)
        >>> current_time = Fraction(0, 1)
        >>> for jump in it:
        >>>     print(f"{current_time} - {jump[0]}")
        >>>     current_time = jump[1]
        >>> print(f"{current_time} - {it.get_time()}")
    """
    def __init__(self, score, start_time: Fraction = Fraction(0, 1)):
        """
        Initializes the JumpIterator.

        Parameters:
            score (Score): The musical score object to be iterated on.
            start_time (Fraction): The starting time in the score from which to begin iteration. Defaults to `0`.
        """
        self._score = score
        self._time = start_time
        self._handled_commands = {}
        self._al = None

    # RULES:
    # - The most recent (last seen) |: is paired to :| (starts override prior starts which remain unmatched).
    # - Begin Of Score (BOS) can act as |:, but EOS not as :|. Unmatched |: are considered notation error.
    # - Repeats should not "combine and cut" sections. In practice, however, one can contrive such cases:  |: ... :| ... :|
    #       this is handled by reusing the start for both ends and ignoring inner end the second time.
    # - As described before, repeat ends are only executed once (execution includes repeating multiple times in accordance to endings)
    # - repeats are handled before Da Capo/Dal Segno commands. If :| and D.C./D.S. coincide, :| takes presedence.
    # - D.C./D.S. are only executed if outside an active repeat range. (|: ... :|).
    # - Executing D.C./D.S. block repeats (and other commands?) until the command reaches its destination (Coda, Fine, or command itself if no al)
    # - To Coda and Fine jump is only executed if actively in a D.C./D.S. al Coda command.
        
    def __iter__(self):
        return self  # Cursor is its own iterator

    def __next__(self):
        if isinstance(self._al, Fine):
            raise StopIteration
        if isinstance(self._al, ToCoda):
            old_time = self._time
            self._time = self._al.jump()
            self._al = None
            #print(f"forward jump {old_time} -> {self._time}")
            return old_time, self._time
        # check repeat commands
        idx = self._score._repeat_commands.bisect_right(self._time)
        while idx < len(self._score._repeat_commands):
            cmd = self._score._repeat_commands.values()[idx]
            # don't execute commands twice
            if cmd in self._handled_commands:
                idx += 1
            else:
                self._handled_commands[cmd] = 1
                # return but then advance cursor to destination
                destination = cmd.get_destination()
                self._time = destination._onset    
                # cache next action if al is not empty        
                if cmd._al != '':
                    self._al = destination
                # return backward jump to repeat marker
                #print(f"backward jump {cmd._onset} -> {cmd.jump()}")
                return cmd._onset, cmd.jump()
        raise StopIteration
    
    def get_time(self) -> Fraction:
        """
        Returns the current time of the iterator. This is useful for extracting the end time after iteration.
        Note that due to the presence of `Fine`, this value might differ from `Score.get_offset()`.
        """
        return self._time

    # def __next__(self):
    #     while True:
    #         next_jump = self._get_next_jump()
    #         if isinstance(next_jump, RepeatEnd):
    #             # maximal number of repeats done, reset repeat_iteration and ignore RepeatEnd
    #             if self.__repeat_iteration >= next_jump._iterations:
    #                 self.__repeat_iteration = 1
    #                 self.__time = next_jump._onset
    #             else:
    #                 self.__repeat_iteration += 1
    #                 self.__time = next_jump.jump()
    #                 return next_jump._onset, self.__time
    #         elif isinstance(next_jump, RepeatCommand):
    #             self.__time = next_jump.jump()
    #             return next_jump._onset, self.__time





# TODO preprocessed but cached range for repeats. Necessary?
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
