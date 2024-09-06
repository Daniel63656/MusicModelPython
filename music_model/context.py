from fractions import Fraction
from .enums import ClefType


class Clef():
    def __init__(self, clef_type: ClefType, octave_shift: int=0):
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
        return self.get_octave_shift

    def get_staff_line_position(self) -> int:
        """
        staff line positions (slp) count every possible note position in a staff, counted upwards and starting from the bottom line
        of the staff as being 0
        """
        return (self.clef_type.value[0] - 1) * 2

    def get_C0_reference_line(self):
        """
        returns: staff line position (slp) of C0 in the clef. Used for pitch calculations.
        """
        return self._C0_reference_line


class KeySignature:
    """
    Represents a musical key signature, including the number of accidentals (fifths) and the mode (major or minor).

    `fifths` describes the number of sharps (positive) or flats (negative) in the key signature.
    It is 0 for any number of naturals when resolving to C major/A minor.
    """
    chromatic_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    flattened_chromatic_names = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

    def __init__(self, fifths=0, mode=True):
        self._fifths = fifths
        self._mode = mode

    def get_fifths(self) -> int:
        return self._fifths

    def is_major(self) -> bool:
        return self._mode

    def is_minor(self) -> bool:
        return not self._mode

    def chromatic_index_has_accidental(self, idx) -> bool:
        for i in range(1, abs(self._fifths) + 1):
            if self._fifths > 0:
                if (11 + 7 * i) % 12 == idx:
                    return True
            if self._fifths < 0:
                if (5 + 5 * i) % 12 == idx:
                    return True
        return False

    def pitch_has_accidental(self, pitch) -> bool:
        pitch = pitch + 1200 - self._fifths * 7
        for i in range(0, abs(self._fifths) // 5 + 1):
            if len(self.chromatic_names[(pitch - i * (1 if self._fifths > 0 else -1)) % 12]) > 1:
                return True
        return False

    def pitch_is_natural(self, pitch) -> bool:
        pitch = pitch + 1200 - self._fifths * 7
        return len(self.chromatic_names[pitch % 12]) < 2

    def __str__(self):
        major_minor = " Major" if self._mode else " Minor"
        if self._fifths >= 0:
            return self.chromatic_names[(self._fifths * 7) % 12] + major_minor
        return self.flattened_chromatic_names[((self._fifths + 1200) * 7) % 12] + major_minor


class TimeSignature:
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
