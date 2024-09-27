import math
from enum import Enum
from fractions import Fraction
from typing import Optional
from . import Self


class Accidental(Enum):
    """
    Represents the different types of accidentals in music notation.
    """
    SHARP = 1
    DOUBLE_SHARP = 2
    FLAT = -1
    FLAT_FLAT = -2
    NATURAL = 0
    # ALIASES from older notation, default to main types when instantiated
    SHARP_SHARP = 2     ##
    NATURAL_FLAT = -1
    NATURAL_SHARP = 1
    NATURAL_NATURAL = 0

    def get_alter(self):
        return self.value
        

class NoteName(Enum):
    """
    Represents (English) musical note names with chromatic and diatonic indices.

    The `chromatic index` represents the position of the note name in the chromatic scale, ranging
    from C=0 to 11. It corresponds to the `value` of the enum member, e.g., NoteName.E has a chromatic index of 4.

    The `diatonic index` represents the position of the note name in the diatonic scale (white piano keys), ranging
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
    """
    Represents the different types of clefs in music notation.
    """
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
        Returns staff line of the clef with the lowest line being 1 and highest line being 5.
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
    Represents symbolic duration types such as 'whole' and 'quarter'.

    Attributes:
    value (Fraction): Nominal duration of the note type.
    base2_exponent (int): Exponent used to raise 2 to obtain the nominal duration, e.g., 2**(-2) = 1/4, corresponding to 'quarter' type.
    common_name (str): Name of the type used in the U.S. system.
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
        self._base2_exponent = int(round(math.log(float(value)) / (math.log(2) + 1e-10)))
        self._common_name = self.__common_name(value)
        _note_type_by_common_name[self._common_name] = self
        _note_type_by_base2_exponent[self._base2_exponent] = self

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

    def get_value(self, dots: int=0) -> Fraction:
        if dots == 0:
            return self.value
        return self.value * ((Fraction(1, 1) - Fraction(1, 2) ** (dots + 1)) / Fraction(1, 2))
    
    def get_base2_exponent(self) -> int:
        return self._base2_exponent
    
    def get_common_name(self) -> str:
        return self._common_name
        
    @staticmethod
    def from_base2_exponent(base2_exponent):
        return _note_type_by_base2_exponent[base2_exponent]
    
    @staticmethod
    def from_common_name(common_name):
        return _note_type_by_common_name[common_name]

    @staticmethod
    def from_duration(duration: Fraction) -> tuple[Self, int]:
        if 256 % duration.denominator != 0:
            raise ValueError("Specified duration must be multiple of 1/256 to be expressed as NoteType and dots.")
        if duration > NoteType.MAXIMA.value:
            raise ValueError("Specified duration is too big to be expressed as NoteType!")
        # calculate NoteType and dots using binary arithmetic
        number = duration.numerator * 256 // duration.denominator
        highest_set_exponent_bit = -1
        dots = 0
        for bit in range(NoteType.MAXIMA._base2_exponent - NoteType.NT256._base2_exponent, -1, -1):
            if number & (1 << bit):
                if highest_set_exponent_bit == -1:
                    highest_set_exponent_bit = bit
                else:
                    if highest_set_exponent_bit - dots - 1 > bit:
                        raise ValueError("Couldn't infer valuable NoteType, dots combination for specified duration!")
                    dots += 1
        return NoteType.from_base2_exponent(NoteType.NT256._base2_exponent + highest_set_exponent_bit), dots
    
    @staticmethod
    def types_from_duration(duration: Fraction) -> list[tuple[Self, int]]:
        if 256 % duration.denominator != 0:
            raise ValueError("Specified duration must be multiple of 1/256 to be expressed as NoteType and dots.")
        if duration > NoteType.MAXIMA.value:
            raise ValueError("Specified duration is too big to be expressed as NoteType!")
        # calculate NoteType and dots using binary arithmetic
        ntpd_list = []  # List to hold NoteType and dot combinations
        number = duration.numerator * 256 // duration.denominator
        highest_set_exponent_bit = -1
        dots = 0
        for bit in range(NoteType.MAXIMA._base2_exponent - NoteType.NT256._base2_exponent, -1, -1):
            if number & (1 << bit):
                if highest_set_exponent_bit == -1:
                    highest_set_exponent_bit = bit
                else:
                    if highest_set_exponent_bit - dots - 1 > bit:
                        # Add current NoteType and dot combination to the list
                        ntpd_list.append((NoteType.from_base2_exponent(NoteType.NT256._base2_exponent + highest_set_exponent_bit), dots))
                        highest_set_exponent_bit = bit
                        dots = 0
                    else:
                        dots += 1
        # add the last NoteType and dot combination
        ntpd_list.append((NoteType.from_base2_exponent(NoteType.NT256._base2_exponent + highest_set_exponent_bit), dots))
        return ntpd_list

    def __str__(self):
        return self._common_name


class Octavation(Enum):
    """
    Represents the different octavations an `OctaveShift` can have. Value describes the shift in pitch, measured in octaves.
    """
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
    """
    Represents the different directions of stems in music notation.
    """
    UP = 1
    DOWN = 0


class Expression(Enum):
    """
    Represents different types of musical expressions, applicable to chords and grace chords.
    """
    ACCENT = 0
    MARCATO = 1
    STACCATO = 2
    STACCATISSIMO = 3
    TENUTO = 4
    ARPEGGIO = 5
    TRILL = 6
    MORDENT = 7


class Dynamics(Enum):
    """
    Represents different types of musical dynamics.
    """
    MEZZO_PIANO = "mp"
    PIANO = "p"
    PIANISSIMO = "pp"
    PIANO_PIANISSIMO = "ppp"
    MEZZO_FORTE = "mf"
    FORTE = "f"
    FORTISSIMO = "ff"
    FORTE_FORTISSIMO = "fff"


class Instrument(Enum):
    """
    Instrument according to MIDI standard. Values are program numbers, which are used to select the instrument sound on a MIDI device.
    """
    ACOUSTIC_PIANO = 0
    BRIGHT_PIANO = 1
    ELECTRIC_GRAND_PIANO = 2
    HONKY_TONK_PIANO = 3
    ELECTRIC_PIANO_1 = 4
    ELECTRIC_PIANO_2 = 5
    HARPICHORD = 6
    CLAVI = 7
    CELESTA = 8
    GLOCKENSPIEL = 9
    MUSICAL_BOX = 10
    VIBRAPHONE = 11
    MARIMBA = 12
    XYLOPHONE = 13
    TUBULAR_BELL = 14
    DULCIMER = 15
    DRAWBAR_ORGAN = 16
    PERCUSSIVE_ORGAN = 17
    ROCK_ORGAN = 18
    CHURCH_ORGAN = 19
    REED_ORGAN = 20
    ACCORDION = 21
    HARMONICA = 22
    TANGO_ACCORDION = 23
    ACOUSTIC_GUITAR_NYLON = 24
    ACOUSTIC_GUITAR_STEEL = 25
    ELECTRIC_GUITAR_JAZZ = 26
    ELECTRIC_GUITAR_CLEAN = 27
    ELECTRIC_GUITAR_MUTED = 28
    OVERDRIVEN_GUITAR = 29
    DISTORTION_GUITAR = 30
    GUITAR_HARMONICS = 31
    ACOUSTIC_BASS = 32
    ELECTRIC_BASS_FINGER = 33
    ELECTRIC_BASS_PICK = 34
    FRETLESS_BASS = 35
    SLAP_BASS_1 = 36
    SLAP_BASS_2 = 37
    SYNTH_BASS_1 = 38
    SYNTH_BASS_2 = 39
    VIOLIN = 40
    VIOLA = 41
    CELLO = 42
    DOUBLE_BASS = 43
    TREMOLO_STRINGS = 44
    PIZZICATO_STRINGS = 45
    ORCHESTRAL_HARP = 46
    TIMPANI = 47
    ENSEMBLE_1 = 48
    ENSEMBLE_2 = 49
    SYNTH_STRINGS_1 = 50
    SYNTH_STRINGS_2 = 51
    VOICE_AAHS = 52
    VOICE_OOHS = 53
    SYNTH_VOICE = 54
    ORCHESTRAL_HIT = 55
    TRUMPET = 56
    TROMBONE = 57
    TUBA = 58
    MUTED_TRUMPET = 59
    FRENCH_HORN = 60
    BASS_SECTION_1 = 61
    SYNTH_BRASS_1 = 62
    SYNTH_BRASS_2 = 63
    SOPRANO_SAX = 64
    ALTO_SAX = 65
    TENOR_SAX = 66
    BARITONE_SAX = 67
    OBOE = 68
    ENGLISH_HORN = 69
    BASSOON = 70
    CLARINET = 71
    PICCOLO = 72
    FLUTE = 73
    RECORDER = 74
    PAN_FLUTE = 75
    BLOWN_BOTTLE = 76
    SHAKUHACHI = 77
    WHISTLE = 78
    OCARINA = 79
    LEAD_SQUARE = 80
    LEAD_SAWTOOTH = 81
    LEAD_CALLIOPE = 82
    LEAD_CHIFF = 83
    LEAD_CHARRANG = 84
    LEAD_VOICE = 85
    LEAD_FIFTHS = 86
    LEAD_BASS_LEAD = 87
    PAD_FANTASIA = 88
    PAD_WARM = 89
    PAD_POLYSYNTH = 90
    PAD_CHOIR = 91
    PAD_BOWED = 92
    PAD_METALLIC = 93
    PAD_HALO = 94
    PAD_SWEEP = 95
    FX_RAIN = 96
    FX_SOUNDTRACK = 97
    FX_CRYSTAL = 98
    FX_ATMOSPHERE = 99
    FX_BRIGHTNESS = 100
    FX_GOBLINS = 101
    FX_ECHOES = 102
    FX_SCI_FI = 103
    SITAR = 104
    BANJO = 105
    SHAMISEN = 106
    KOTO = 107
    KALIMBA = 108
    BAGPIPE = 109
    FIDDLE = 110
    SHANAI = 111
    TINKLE_BELL = 112
    AGOGO = 113
    DRUMS = 114
    WOODBLOCK = 115
    TAIKO_DRUM = 116
    MELODIC_TOM = 117
    SYNTH_DRUM = 118
    REVERSE_CYMBAL = 119
    GUITAR_FRET = 120
    BREATH_NOISE = 121
    SEASHORE = 122
    BIRD_TWEET = 123
    TELEPHONE_RING = 124
    HELICOPTER = 125
    APPLAUSE = 126
    GUNSHOT = 127
    DRUM_KIT = 128

    def get_program(self) -> int:
        return self.value % 128

    def is_percussion(self) -> bool:
        return self.value >= 128

    instrument_categories = ["Piano", "Chromatic Percussion", "Organ", "Guitar", "Bass", "Strings", "Ensemble", "Brass", 
                             "Reed", "Pipe", "Synth Lead", "Synth Pad", "Synth Effects", "Ethnic", "Percussive", "Sound Effects"]
    def get_category(self):
        if self.is_percussion():
            return "Drums"
        return Instrument.instrument_categories[self.value // 8]
