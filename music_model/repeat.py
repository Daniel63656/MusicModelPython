from abc import ABC, abstractmethod
from fractions import Fraction
from music_model import ZERO
from .abstract import Range



class RepeatMark(ABC):
    """
    Abstract base class for marks that indicate return or jump points but do not trigger jumps themselves.
    They are positioned at measure onsets. Should not be instantiated directly.
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


class RepeatAction(ABC):
    """
    Abstract base class for objects that trigger a jump in the score (if certain condidions are fulfilled).
    They are placed at measure offsets, while `Endings` must start and end on measure boundaries.
    Should not be instantiated directly.
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


class RepeatEnd(RepeatAction):
    def __init__(self):
        super().__init__()
        self._iterations = 2

    def jump(self) -> Fraction:
        entry = self._score._repeat_starts.lower_entry(self._onset)
        if entry is None:
            return ZERO
        return entry[0]


class ToCoda(RepeatAction):
    def __init__(self):
        super().__init__()

    def jump(self) -> Fraction:
        # jump to next coda by finding higher entry. If None, throw error
        entry = self._score._codas.higher_entry(self._onset)
        if entry is None:
            raise ValueError("No Coda found to jump to.")
        return entry[0]
    
    def __str__(self):
        return "To Coda"


class Fine(RepeatAction):
    def __init__(self):
        super().__init__()

    def jump(self) -> Fraction:
        # jump to end of score
        return self._score.get_offset()
    
    def __str__(self):
        return "Fine"


class Ending(RepeatAction, Range):
    def __init__(self, onset: Fraction, offset: Fraction, numbers: set[int]):
        super().__init__()
        self._onset = onset
        self._offset = offset
        self._numbers = numbers

    def jump(self) -> Fraction:
        # applied skip if ending not applied
        return self._offset
    
    def get_numbers(self) -> set[int]:
        return self._numbers
    
    def get_onset(self) -> Fraction:
        return self._onset
        
    def get_offset(self) -> Fraction:
        return self._offset


class RepeatCommand(RepeatAction):
    """
    Abstract base class for repeat commands of the form: Da/Dal [return point] (al [destination]), where the 
    jump to the return point is followed by continuous play until the destination (`Fine`, `ToCoda` or `Self`)
    is reached. Should not be instantiated directly.
    """
    def __init__(self, al: str=''):
        super().__init__()
        if al not in {'', 'Fine', 'Coda'}:
            raise ValueError(f"Invalid value for 'al': {al}. Must be empty, 'Fine' or 'Coda'.")
        self._al = al

    def get_destination(self) -> RepeatAction:
        if self._al == '':
            return self
        if self._al == 'Fine':
            # jump to fine by finding higher entry. If None, throw error
            entry = self._score._fines.higher_entry(self._onset)
            if entry is None:
                raise ValueError("Fine not found.")
            return entry[1]
        if self._al == 'Coda':
            # jump to next ToCoda by finding higher entry. If None, throw error
            entry = self._score._to_codas.higher_entry(self._onset)
            if entry is None:
                raise ValueError("No ToCoda destination found.")
            return entry[1]

    def __str__(self):
        return f"{self.prefix}{f' al {self._al}' if self._al else ''}"


class DaCapo(RepeatCommand):
    def __init__(self, al: str=''):
        super().__init__(al)

    def jump(self) -> Fraction:
        return ZERO

    def __str__(self):
        return f"D.C.{f' al {self._al}' if self._al else ''}"


class DalSegno(RepeatCommand):
    def __init__(self, al: str=''):
        super().__init__(al)

    def jump(self) -> Fraction:
        #TODO what if Segno lies in the future?
        entry = self._score._segnos.lower_entry(self._onset)
        if entry is None:
            raise ValueError("No Segno found to jump to.")
        return entry[0]
    
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
    def __init__(self, score, start_time: Fraction = ZERO):
        """
        Initializes the JumpIterator.

        Parameters:
            score (Score): The musical score object to be iterated on.
            start_time (Fraction): The starting time in the score from which to begin iteration. Defaults to `0`.
        """
        self._score = score
        self._time = start_time
        # make sure commands are handled only once <RepeatCommand, int>
        self._handled_commands = {}
        # save destination for next iteration
        self._al = None
        
    def __iter__(self):
        return self  # Cursor is its own iterator
    
    def _get_next_unexecuted_action(self, collection):
        idx = collection.bisect_right(self._time)
        while idx < len(collection):
            cmd = collection.values()[idx]
            # don't execute commands twice
            if cmd in self._handled_commands:
                idx += 1
            else:
                return cmd
        return None
    
    def _execute_repeat_end(self, end):
        self._handled_commands[end] = 1
        self._time = end.jump()
        #print(f"backward jump {end._onset} -> {self._time}")
        return end._onset, self._time 
    
    def _execute_repeat_command(self, cmd):
        self._handled_commands[cmd] = 1
        destination = cmd.get_destination()
        self._time = destination._onset     
        if cmd._al != '':
            self._al = destination
        #print(f"backward jump {cmd._onset} -> {cmd.jump()}")
        return cmd._onset, cmd.jump()

    def __next__(self):
        # RULES:
        # - The most recent (last seen) |: is paired to :| (starts override prior starts which remain unmatched).
        # - Begin Of Score (BOS) can act as |:, but EOS not as :|. Unmatched |: are considered notation error.
        # - Repeats should not "combine and cut" sections. In practice, however, one can contrive such cases:  |: ... :| ... :|
        #       this is handled by reusing the start for both ends and ignoring inner end the second time.
        # - As described before, repeat ends are only executed once (execution includes repeating multiple times in accordance to endings)
        # - repeats are handled before Da Capo/Dal Segno commands. If :| and D.C./D.S. coincide, :| takes presedence.
        # - D.C./D.S. are only executed if outside an active repeat range. (|: ... :|).
        # - Executing D.C./D.S. blocks all other actions until the command reaches its destination (Coda, Fine, or command itself if no al)

        # first, check if instruction from last iteration carries over
        if isinstance(self._al, Fine):
            raise StopIteration
        if isinstance(self._al, ToCoda):
            old_time = self._time
            self._time = self._al.jump()
            self._al = None
            #print(f"forward jump {old_time} -> {self._time}")
            return old_time, self._time
        # not the case, fetch next RepeatEnd and next RepeatCommand
        end = self._get_next_unexecuted_action(self._score._repeat_ends)
        cmd = self._get_next_unexecuted_action(self._score._repeat_commands)
        if end is not None:
            repeat_start_onset = end.jump()
            if cmd is None or repeat_start_onset < cmd._onset:
                # no command or in active repeat
                return self._execute_repeat_end(end)
            # not the case, execute repeat command instead
            return self._execute_repeat_command(cmd)
        else:
            if cmd is not None:
                return self._execute_repeat_command(cmd)
            raise StopIteration # both were None
    
    def get_time(self) -> Fraction:
        """
        Returns the current time of the iterator. This is useful for extracting the end time after iteration.
        Note that due to the presence of `Fine`, this value might differ from `Score.get_offset()`.
        """
        return self._time
