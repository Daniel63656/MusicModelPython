from fractions import Fraction
from .enums import ClefType


class Clef():
    """
    Represents a musical clef.

    Attributes:
    clef_type (ClefType): The type of the clef (G, F, C, etc.)
    octave (int): The octave of the clef. Can be different from the standard octave for G and F clefs.
    """
    def __init__(self, clef_type: ClefType, octave_shift: int=0):
        """
        Initialize the clef.

        Parameters:
        clef_type (ClefType): The type of the clef (G, F, C, etc.)
        octave_shift (int): The shift in octave relative to the standard octave of the `ClefType`.
        """
        self._clef_type = clef_type
        if octave_shift != 0 and clef_type != ClefType.TREBLE and clef_type != ClefType.BASS:
            raise ValueError("Only G and F clefs can have octave variations.")
        self._octave = clef_type.value[2] + octave_shift if clef_type.value[2] is not None else None
        self._C0_reference_line = None
        if clef_type.value[1] is not None:
            self._C0_reference_line = (clef_type.value[0] - 1) * 2 - clef_type.value[1].get_diatonic_index() - self._octave * 7
    
    def get_clef_type(self) -> ClefType:
        return self._clef_type
    
    def get_octave(self) -> int:
        return self._octave
    
    def get_octave_shift(self) -> int:
        """
        Returns the shift in octave relative to the standard octave of the `ClefType`.
        """
        return self._octave - self._clef_type.get_standard_octave()

    def get_staff_line(self) -> int:    #TODO do I need this?
        """
        Returns the staff line position of the clef. Used for pitch calculations.

        staff line positions (slp) count every possible note position in a staff, counted upwards and starting from the bottom line
        of the staff as being 0
        """
        return (self.clef_type.value[0] - 1) * 2

    def get_C0_reference_line(self):
        """
        Returns the staff line position of C0 in the clef. Useful for pitch calculations.
        """
        return self._C0_reference_line
    
    def equals(self, other) -> bool:
        """
        Compares two clefs for semantic equality. Does not interfere with hashing strategy for the class.
        """
        if not isinstance(other, self.__class__):
            return False
        return self._clef_type == other._clef_type and self._octave == other._octave


class KeySignature:
    """
    Represents a musical key signature.

    Attributes:
    fifths (int): The number of sharps (positive) or flats (negative) in the key signature. 0 for any number of naturals when resolving to C major/A minor.
    mode (bool): `True` for major, `False` for minor.
    """
    chromatic_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    flattened_chromatic_names = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

    def __init__(self, fifths, minor=False):
        self._fifths = fifths
        self._minor = minor

    def get_fifths(self) -> int:
        return self._fifths

    def is_major(self) -> bool:
        return not self._minor

    def is_minor(self) -> bool:
        return self._minor

    def pitch_has_key_accidental(self, pitch) -> bool:
        """
        Returns `True` if the key has an accidental for the given pitch. For example,\n
        A Major/F# Minor returns `True` for pitch % 12 = 0 (C -> C#), 5 (F -> F#) and 7 (G -> G#) and\n
        Eb Major/C Minor returns `True` for pitch % 12 = 4 (E -> Eb), 9 (A -> Ab) and 11 (B -> Bb).\n
        The number of `True` pitch values in an octave corresponds to the number of fifths in the key signature.
        Useful for converting from natural to absolute pitch.
        """
        for i in range(1, abs(self._fifths) + 1):
            if self._fifths > 0:
                if (10 + 7 * i) % 12 == pitch % 12:
                    return True
            if self._fifths < 0:
                if (6 + 5 * i) % 12 == pitch % 12:
                    return True
        return False
    
    def pitch_is_natural(self, pitch) -> bool:
        """
        Returns `True` if the given pitch is part of the key's diatonic scale, and `False`
        otherwise (therefore needing an alteration). This will always be true for 7 out of the 12 pitches. 
        For A Major/F# Minor these are: 
        pitch % 12 = 1 (C#), 2 (D), 4 (E), 6 (F#), 8 (G#), 9 (A) and 11 (B).
        """
        pitch = pitch + 1200 - self._fifths * 7
        return len(self.chromatic_names[pitch % 12]) < 2

    # TODO this was used in Java Controller to create notes from lines. What is difference between this and the other methods?
    # this supposedly takes effect when abs(fifths) >= 6 as there are now more key accs then black keys. Until then it is
    # exactly !pitch_is_natural()

    # def pitch_needs_accidental(self, pitch) -> bool:
    #     pitch = pitch + 1200 - self._fifths * 7
    #     for i in range(0, abs(self._fifths) // 5 + 1):
    #         if len(self.chromatic_names[(pitch - i * (1 if self._fifths > 0 else -1)) % 12]) > 1:
    #             return True
    #     return False
    
    def equals(self, other) -> bool:
        """
        Compares two key signatures for semantic equality. Does not interfere with hashing strategy for the class.
        """
        if not isinstance(other, self.__class__):
            return False
        return self._fifths == other._fifths and self._minor == other._minor

    def __str__(self):
        major_minor = " Minor" if self._minor else " Major"
        if self._fifths >= 0:
            return self.chromatic_names[(self._fifths*7 + 9*self._minor) % 12] + major_minor
        return self.flattened_chromatic_names[(self._fifths*7 + 9*self._minor + 1200) % 12] + major_minor


class TimeSignature:
    """
    Represents a musical time signature.

    Attributes:
    numerator (int): The number of beats in a measure.
    denominator (int): The note value that represents one beat.
    symbolic (bool): Whether the time signature is represented symbolically (for 4/4 and 2/2).
    """
    def __init__(self, numerator, denominator, symbolic: bool = False):
        if numerator <= 0 or denominator <= 0:
            raise ValueError(f"The time signature {numerator}/{denominator} is not allowed.")
        if symbolic and numerator not in (4, 2) and  denominator not in (4, 2):
            raise ValueError(f"Only 4/4 and 2/2 time signatures can have symbolic appearances.")
        # don't use fraction directly, since it gets reduced!
        self._numerator = numerator
        self._denominator = denominator
        self._symbolic = symbolic

    def get_as_fraction(self) -> Fraction:
        return Fraction(self._numerator, self._denominator)
    
    def is_symbolic(self) -> bool:
        return self._symbolic
    
    def get_beats(self) -> int:
        return self._numerator
    
    def get_beat_type(self) -> int:
        return self._denominator
    
    def equals(self, other) -> bool:
        """
        Compares two time signatures for semantic equality. Does not interfere with hashing strategy for the class.
        """
        if not isinstance(other, self.__class__):
            return False
        return self._numerator == other._numerator and self._denominator == other._denominator and self._symbolic == other._symbolic
