import os
from music_model import *
from music_model.conversion import *
resources_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")


def test_pitch_retrieval():
    midi_pitches = [68, 68, 66, 67, 61, 73, 68, 65, 60, 72, 67, 65]
    score = import_xml(os.path.join(resources_dir, "acc_and_keys.musicxml"))
    for i, chord in enumerate(score.get_parts()[0].get_staff(0).get_chords_and_rests()):
        assert next(iter(chord.get_notes())).get_pitch() == midi_pitches[i] 

def test_pitch_calculation():
    score = import_xml(os.path.join(resources_dir, "chromatic_keys.musicxml"))
    for i, chord in enumerate(score.get_parts()[0].get_staff(0).get_chords_and_rests()):
        if isinstance(chord, Chord):
            note = next(iter(chord.get_notes()))
            key = chord.get_staff().get_key_signature(chord.get_onset())

            # check natural pitch -> absolute pitch conversion, assuming note is not influenced by other accidentals
            pitch = (note._octave+1)*12 + note._note_name.value        
            if note._accidental:
                pitch += note._accidental.value
            # here prior accidentals would be checked
            # elif ...
            elif key.pitch_has_key_accidental(pitch):   # not key.pitch_is_natural(pitch) works as well but only for up to 5 fifths
                if key._fifths > 0:
                    pitch += 1
                else:
                    pitch -= 1
            assert note._pitch == pitch

            # check absolute pitch -> natural pitch conversion
            ascending = (i // 12) % 2 == 0
            name, octave, _ = Note.calculate_natural_pitch(key, note.get_pitch(), flatten=not ascending)
            print(i % 12, i //24, name, octave)
            assert note._note_name == name
            assert note._octave == octave

def test_natural_pitch_calculation():
    score = import_xml(os.path.join(resources_dir, "acc_test.musicxml"))
    flatten = [True, None, False, True, None, False, True, None, None, False]
    names = [NoteName.F, NoteName.F, NoteName.F, NoteName.B, NoteName.B, NoteName.B, NoteName.E, NoteName.E, NoteName.F, NoteName.F]
    alterations = [0, 1, 2, -2, -1, 0, 0, 1, 1, 2]
    i = 0
    for chord in score.get_parts()[0].get_staff(0).get_chords_and_rests():
        if isinstance(chord, Chord):
            note = next(iter(chord.get_notes()))
            key = chord.get_staff().get_key_signature(chord.get_onset())
            # check absolute pitch -> natural pitch conversion
            name, _, alteration = Note.calculate_natural_pitch(key, note.get_pitch(), flatten=True if flatten[i] is True else False)
            assert name == names[i]
            assert alteration == alterations[i]
            i += 1
