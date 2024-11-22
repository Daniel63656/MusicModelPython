import os
from io import StringIO
from fractions import Fraction
from music_model import *
from music_model.conversion import *
from music_model.conversion.xml_export import parse_to_xml
from music_model import ZERO
resources_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")


def test_musicxml_io():
    for file in os.listdir(resources_dir):
        filepath = os.path.join(resources_dir, file)
        print(filepath)
        score = import_xml(filepath)
        # check export for crashes
        parse_to_xml(score)

def test_beams():
    # MUSICXML DOES NOT EXPORT BEAMED RESTS, SO THEY ARE NOT TESTED
    score = import_xml(os.path.join(resources_dir, "beams.musicxml"))
    staff = score.get_parts()[0].get_staff(0)
    # test both way referencing
    bg = next(iter(staff.get_chords_and_rests_at(ZERO))).get_beam_group()
    assert len(bg.get_chords_and_rests()) == 5
    assert bg.get_offset() == Fraction(3, 8)
    assert bg.get_duration() == Fraction(3, 8)
    for chord_rest in bg.get_chords_and_rests():
        assert chord_rest.get_beam_group() == bg
    bg = next(iter(staff.get_chords_and_rests_at(Fraction(2, 4)))).get_beam_group()
    assert len(bg.get_chords_and_rests()) == 6
    assert bg.get_offset() == Fraction(11, 16)
    assert bg.get_duration() == Fraction(3, 16)
    for chord_rest in bg.get_chords_and_rests():
        assert chord_rest.get_beam_group() == bg
    bg = next(iter(staff.get_chords_and_rests_at(Fraction(6, 8)))).get_beam_group()
    assert len(bg.get_chords_and_rests()) == 2
    assert bg.get_offset() == Fraction(14, 16)
    assert bg.get_duration() == Fraction(1, 8)
    for chord_rest in bg.get_chords_and_rests():
        assert chord_rest.get_beam_group() == bg
    # grace beam group
    chord = next(iter(staff.get_chords_and_rests_at(Fraction(1, 1))))
    grace_bg = None
    for grace_chord in chord.get_grace_chords():
        if grace_bg is None:
            grace_bg = grace_chord.get_beam_group()
        else:
            assert grace_bg == grace_chord.get_beam_group()
    assert grace_bg.get_duration() == ZERO
    assert grace_bg._grace_beam == True

def test_tuplet_durations():
    score = import_xml(os.path.join(resources_dir, "simple_nested_tuplet.musicxml"))
    voice = score.get_parts()[0].get_voice(1)
    outer_tuplet = voice.get_element(Fraction(1, 2))
    assert outer_tuplet.get_duration() == Fraction(1, 4)
    inner_tuplet = outer_tuplet.get_element(Fraction(2, 3))
    assert inner_tuplet.get_duration() == Fraction(1, 12)

# TODO test tuplet with no time mod
    
# TODO test tuplet with different normal/actual types/dots

def test_rest_durations():
    score = import_xml(os.path.join(resources_dir, "rest_durations.musicxml"))
    durations = [Fraction(3, 4), Fraction(3, 4), Fraction(2, 4), Fraction(1, 12), Fraction(1, 12), Fraction(1, 12), Fraction(5, 4), Fraction(5, 12), Fraction(5, 12), Fraction(5, 12), Fraction(4, 4), Fraction(1, 4), Fraction(4, 4), Fraction(4, 4)]
    measure_rest = [True, False, False, False, False, False, True, False, False, False, False, False, True, False]
    i = 0
    for rest in score.get_parts()[0].get_staff(1).get_chords_and_rests():
        if isinstance(rest, Rest):
            assert rest.get_duration() == durations[i]
            assert rest.is_measure_rest() == measure_rest[i]
            if measure_rest[i]:
                assert rest.get_note_type() == NoteType.WHOLE
                assert rest.get_dots() == 0
            i += 1

def check_shifts(shifts, staff):
    assert len(shifts) == 5
    assert shifts[0].get_octavation() == Octavation.O8va
    assert shifts[0].get_onset() == Fraction(1, 4)
    assert shifts[0].get_offset() == Fraction(6, 4)
    assert shifts[1].get_octavation() == Octavation.O8vb
    assert shifts[1].get_onset() == Fraction(6, 4)
    assert shifts[1].get_offset() == Fraction(8, 4)
    assert shifts[2].get_octavation() == Octavation.O8vb
    assert shifts[2].get_onset() == Fraction(8, 4)
    assert shifts[2].get_offset() == Fraction(10, 4)
    assert shifts[3].get_octavation() == Octavation.O15mb
    assert shifts[3].get_onset() == Fraction(12, 4)
    assert shifts[3].get_offset() == Fraction(13, 4)
    assert shifts[4].get_octavation() == Octavation.O15ma
    assert shifts[4].get_onset() == Fraction(14, 4)
    assert shifts[4].get_offset() == Fraction(16, 4)
    # test range access (especially offset exclusive)
    assert staff.get_octavation(Fraction(6, 4)) == Octavation.O8vb
    assert staff.get_octavation(Fraction(10, 4)) == None
    assert staff.get_octavation(Fraction(12, 4)) == Octavation.O15mb
    assert staff.get_octavation(Fraction(13, 4)) == None
    assert staff.get_octavation(Fraction(14, 4)) == Octavation.O15ma
    assert staff.get_octavation(Fraction(15, 4)) == Octavation.O15ma

def test_octave_shifts():
    score = import_xml(os.path.join(resources_dir, "octave_shifts.musicxml"))
    staff = score.get_parts()[0].get_staff(0)
    shifts = list(staff.get_octave_shifts())
    check_shifts(shifts, staff)
    # also check export as this is tricky
    xml_content = parse_to_xml(score, pretty=True)
    score = import_xml(StringIO(xml_content))
    staff = score.get_parts()[0].get_staff(0)
    shifts = list(staff.get_octave_shifts())
    check_shifts(shifts, staff)

def test_clef_import():
    # MuseScore strangely does not IMPORT treble 15mb clefs, so don't be surprised when visualizing
    # they are imported, exported and tested though
    score = import_xml(os.path.join(resources_dir, "various_clefs.musicxml"))
    staff = score.get_parts()[0].get_staff(0)
    assert staff.get_clef(ZERO).equals(Clef(ClefType.TREBLE, octave_shift=1))
    assert staff.get_clef(Fraction(1, 4)).equals(Clef(ClefType.TREBLE, octave_shift=2))
    assert staff.get_clef(Fraction(2, 4)).equals(Clef(ClefType.TREBLE, octave_shift=-1))
    assert staff.get_clef(Fraction(3, 4)).equals(Clef(ClefType.TREBLE, octave_shift=-2))
    assert staff.get_clef(Fraction(1, 1)).equals(Clef(ClefType.TREBLE))
    assert staff.get_clef(Fraction(8, 4)).equals(Clef(ClefType.SOPRANO))
    assert staff.get_clef(Fraction(9, 4)).equals(Clef(ClefType.MEZZO_SOPRANO))
    assert staff.get_clef(Fraction(10, 4)).equals(Clef(ClefType.ALTO))
    assert staff.get_clef(Fraction(11, 4)).equals(Clef(ClefType.TENOR))
    assert staff.get_clef(Fraction(12, 4)).equals(Clef(ClefType.BARITONE))
    staff = score.get_parts()[0].get_staff(1)
    assert staff.get_clef(ZERO).equals(Clef(ClefType.BASS, octave_shift=1))
    assert staff.get_clef(Fraction(1, 4)).equals(Clef(ClefType.BASS, octave_shift=2))
    assert staff.get_clef(Fraction(2, 4)).equals(Clef(ClefType.BASS, octave_shift=-1))
    assert staff.get_clef(Fraction(3, 4)).equals(Clef(ClefType.BASS, octave_shift=-2))
    assert staff.get_clef(Fraction(1, 1)).equals(Clef(ClefType.BASS))
    # test 'before-barline' attribute
    assert score.get_parts()[0].get_staff(0).get_clef(Fraction(1, 1))._after_barline == None
    assert score.get_parts()[0].get_staff(1).get_clef(Fraction(1, 1))._after_barline == True
    assert score.get_parts()[0].get_staff(0).get_clef(Fraction(2, 1))._after_barline == True
    assert score.get_parts()[0].get_staff(0).get_clef(Fraction(3, 1))._after_barline == True

def test_dynamics_import():
    score = import_xml(os.path.join(resources_dir, "dynamics_and_fermatas.musicxml"))
    staff = score.get_parts()[0].get_staff(0)
    assert len(staff._dynamics) == 4
    assert staff._dynamics.get(Fraction(1, 4)) == Dynamics.MEZZO_FORTE
    assert staff._dynamics.get(Fraction(2, 4)) == Dynamics.PIANISSIMO
    assert staff._dynamics.get(Fraction(3, 4)) == Dynamics.FORTE_FORTISSIMO
    assert staff._dynamics.get(Fraction(1, 1)) == Dynamics.PIANO
    staff = score.get_parts()[0].get_staff(1)
    assert len(staff._dynamics) == 2
    assert staff._dynamics.get(Fraction(1, 1)) == Dynamics.FORTE
    assert staff._dynamics.get(Fraction(3, 2)) == Dynamics.MEZZO_PIANO

def test_fermata_import():
    score = import_xml(os.path.join(resources_dir, "dynamics_and_fermatas.musicxml"))
    staff = score.get_parts()[0].get_staff(0)
    assert next(iter(staff.get_chords_and_rests_at(Fraction(7, 4)))).has_fermata() == True
    assert next(iter(staff.get_chords_and_rests_at(Fraction(8, 4)))).has_fermata() == False
    assert next(iter(staff.get_chords_and_rests_at(Fraction(10, 4)))).has_fermata() == True
    staff = score.get_parts()[0].get_staff(1)
    assert next(iter(staff.get_chords_and_rests_at(Fraction(8 , 4)))).has_fermata() == True
    assert next(iter(staff.get_chords_and_rests_at(Fraction(10, 4)))).has_fermata() == True

# TODO test expression import

def test_standard_contexts():
    score = Score()
    part = Part()
    score.append_part(part)
    staff1 = Staff()
    staff2 = Staff()
    # inserting to part adds standard contexts to staffs
    part.insert_staff(0, staff1)
    part.insert_staff(1, staff2)
    assert staff1.get_clef(ZERO).equals(Clef(ClefType.TREBLE))
    assert staff1.get_key_signature(ZERO).equals(KeySignature(0))
    assert staff1.get_time_signature(ZERO).equals(TimeSignature(4, 4))
    assert staff2.get_clef(ZERO).equals(Clef(ClefType.BASS))
    assert staff2.get_key_signature(ZERO).equals(KeySignature(0))
    assert staff2.get_time_signature(ZERO).equals(TimeSignature(4, 4))
    # check if standard measure has been created in part
    assert part._measures is not None

def test_ending_import():
    score = import_xml(os.path.join(resources_dir, "endings.musicxml"))
    e1 = score._endings.get(Fraction(1, 1))
    assert e1 == score._endings.get_by_offset(Fraction(2, 1))
    assert 1 in e1._numbers
    e2 = score._endings.get(Fraction(2, 1))
    assert e2 == score._endings.get_by_offset(Fraction(3, 1))
    assert 2 in e2._numbers
    e3 = score._endings.get(Fraction(4, 1))
    assert e3 == score._endings.get_by_offset(Fraction(5, 1))
    assert 1 in e3._numbers
    assert 2 in e3._numbers
    e4 = score._endings.get(Fraction(5, 1))
    assert e4 == score._endings.get_by_offset(Fraction(6, 1))
    assert 3 in e4._numbers
    