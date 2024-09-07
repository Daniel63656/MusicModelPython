import math
from enum import Enum
from fractions import Fraction
from typing import Optional
from . import Self


class Accidental(Enum):
    SHARP = 1
    SHARP_UP = 1
    SHARP_DOWN = 1
    SLASH_SHARP = 1
    DOUBLE_SHARP = 2
    DOUBLE_SHARP_DOWN = 2
    DOUBLE_SHARP_UP = 2
    SHARP_SHARP = 2
    TRIPLE_SHARP = 3
    FLAT = -1
    FLAT_UP = -1
    FLAT_DOWN = -1
    SLASH_FLAT = -1
    FLAT_FLAT = -2
    FLAT_FLAT_DOWN = -2
    FLAT_FLAT_UP = -2
    DOUBLE_SLASH_FLAT = -2
    TRIPLE_FLAT = -3
    NATURAL = 0
    NATURAL_UP = 0
    NATURAL_DOWN = 0
    NATURAL_FLAT = 0
    NATURAL_SHARP = 0
    DOUBLE_NATURAL = 0
    KORON = 0
    OTHER = 0
    SORI = 0
    NONE = 0

    def get_alter(self):
        return self.value

    @staticmethod
    def from_index(idx):
        if idx == 2:
            return Accidental.DOUBLE_SHARP
        elif idx == 1:
            return Accidental.SHARP
        elif idx == 0:
            return Accidental.NATURAL
        elif idx == -1:
            return Accidental.FLAT
        elif idx == -2:
            return Accidental.FLAT_FLAT
        else:
            return Accidental.NONE
        

class NoteName(Enum):
    """
    An enumeration representing (English) musical note names with chromatic and diatonic indices.

    The chromatic index represents the position of the note name in the chromatic scale, ranging
    from C=0 to 11. It corresponds to the `value` of the enum member, e.g., NoteName.E has a chromatic index of 4.

    The diatonic index represents the position of the note name in the diatonic scale (white piano keys), ranging
    from C=0 to 6. It corresponds to the enum definition order, e.g., NoteName.E has a diatonic index of 2.
    
    Example Usage:
        NoteName['E']   # return NoteName.E by designation\n
        NoteName(4)     # return NoteName.E by chromatic index\n
        NoteName.from_diatonic_index(2)  # Returns NoteName.E from diatonic index
    """
    C = 0
    D = 2
    E = 4
    F = 5
    G = 7
    A = 9
    B = 11

    def get_chromatic_index(self):
        return self.value
    
    def get_diatonic_index(self):
        return list(NoteName).index(self)
    
    @classmethod
    def from_diatonic_index(cls, diatonic_index):
        return list(cls)[diatonic_index]
 

class ClefType(Enum):
    TREBLE = (2, NoteName.G, 4)
    BASS = (4, NoteName.F, 3)
    SOPRANO = (1, NoteName.C, 4)
    MEZZO_SOPRANO = (2, NoteName.C, 4)
    ALTO = (3, NoteName.C, 4)
    TENOR = (4, NoteName.C, 4)
    BARITONE = (5, NoteName.C, 4)
    TAB = (5, NoteName.F, 5)
    PERCUSSION = (3, None, None)
    JIANPU = (0, None, None)

    def get_staff_line(self) -> int:
        """
        counted staff-lines with the lowest being 1 and highest 5.
        """
        return self.value[0]
    
    def get_note_name(self) -> Optional[NoteName]:
        return self.value[1]
    
    def get_standard_octave(self) -> Optional[int]:
        return self.value[2]


_note_type_by_common_name = {}
_note_type_by_base2_exponent = {}
class NoteType(Enum):
    """
    Enumeration representing symbolic note types such as 'whole' and 'quarter'.

    Attributes:
        value (Fraction): nominal duration of the note type
        base2_exponent (int): exponent used to raise 2 to obtain the nominal duration, e.g., 2**(-2) = 1/4, corresponding to 'quarter' type
        common_name (str): name of the type used in the U.S. system
    """
    MAXIMA = Fraction(8, 1)
    LONG = Fraction(4, 1)
    BREVE = Fraction(2, 1)
    WHOLE = Fraction(1, 1)
    HALF = Fraction(1, 2)
    QUARTER = Fraction(1, 4)
    EIGHTH = Fraction(1, 8)
    NT16 = Fraction(1, 16)
    NT32 = Fraction(1, 32)
    NT64 = Fraction(1, 64)
    NT128 = Fraction(1, 128)
    NT256 = Fraction(1, 256)

    def __init__(self, value: Fraction):
        # value is already set in __new__ but must be parameter of __init__
        self.base2_exponent = int(round(math.log(float(value)) / (math.log(2) + 1e-10)))
        self.common_name = self.__common_name(value)
        _note_type_by_common_name[self.common_name] = self
        _note_type_by_base2_exponent[self.base2_exponent] = self

    def __common_name(self, value: Fraction):
        if value.denominator == 1:
            if value.numerator == 1:
                return "whole"
            elif value.numerator == 2:
                return "breve"
            elif value.numerator == 4:
                return "long"
            elif value.numerator == 8:
                return "maxima"
            else:
                raise RuntimeError(f"{value} is not a valid NoteType!")
        elif value.denominator == 2:
            return "half"
        elif value.denominator == 4:
            return "quarter"
        elif value.denominator == 8:
            return "eighth"
        elif value.denominator == 32:
            return "32nd"
        else:
            return f"{value.denominator}th"
        
    @staticmethod
    def from_base2_exponent(base2_exponent):
        return _note_type_by_base2_exponent[base2_exponent]
    
    @staticmethod
    def from_common_name(common_name):
        return _note_type_by_common_name[common_name]

    @staticmethod
    def from_duration(duration: Fraction) -> tuple[Self, int]:
        # fractions are automatically provided in reduced form in python
        if 256 % duration.denominator != 0:
            raise ValueError("Specified duration must be multiple of 1/256 to be expressed as NoteType and dots.")
        if duration > NoteType.MAXIMA.value:
            raise ValueError("Specified duration is too big to be expressed as NoteType!")
        # calculate NoteType and dots using binary arithmetic
        number = duration.numerator * 256 // duration.denominator
        highest_set_exponent_bit = -1
        dots = 0
        for bit in range(NoteType.MAXIMA.base2_exponent - NoteType.NT256.base2_exponent, -1, -1):
            if number & (1 << bit):
                if highest_set_exponent_bit == -1:
                    highest_set_exponent_bit = bit
                else:
                    if highest_set_exponent_bit - dots - 1 > bit:
                        raise ValueError("Couldn't infer valuable NoteType, dots combination for specified duration!")
                    dots += 1
        return NoteType.from_base2_exponent(NoteType.NT256.base2_exponent + highest_set_exponent_bit), dots

    def get_value(self, dots: int = 0) -> Fraction:
        if dots == 0:
            return self.value
        return self.value * ((Fraction(1, 1) - Fraction(1, 2) ** (dots + 1)) / Fraction(1, 2))

    def __str__(self):
        return self.common_name


class Octavation(Enum):
    O8va = 1
    O8vb = -1
    O15ma = 2
    O15mb = -2
    O22ma = 3
    O22mb = -3

    def get_shift(self):
        return self.value

    def __str__(self):
        return self.name[1:]


class Stem(Enum):
    UP = 1
    DOWN = 0


class Ornament(Enum):
    ACCENT = 0
    MARCATO = 1
    STACCATO = 2
    STACCATISSIMO = 3
    TENUTO = 4
    ARPEGGIO = 5
    TRILL = 6
    MORDENT = 7


class Dynamics(Enum):
    MEZZO_PIANO = "mp"
    PIANO = "p"
    PIANISSIMO = "pp"
    PIANO_PIANISSIMO = "ppp"
    MEZZO_FORTE = "mf"
    FORTE = "f"
    FORTISSIMO = "ff"
    FORTE_FORTISSIMO = "fff"
