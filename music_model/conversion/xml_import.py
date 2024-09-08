from music_model import *
from fractions import Fraction
import os, xml.etree.ElementTree as ET
from ..collection import SafeDict
accidental_by_common_name = {
    "sharp": Accidental.SHARP,
    "flat": Accidental.FLAT,
    "natural": Accidental.NATURAL,
    "double-sharp": Accidental.DOUBLE_SHARP,
    "flat-flat": Accidental.FLAT_FLAT,
    "sharp-sharp": Accidental.SHARP_SHARP,
    "natural-sharp": Accidental.NATURAL_SHARP,
    "natural-flat": Accidental.NATURAL_FLAT
}


def import_xml(filepath) -> Score:

    def process_part(root, part):
        # declare outer scope variables
        divisions_per_quarter_note = None
        longest_voice_offset, current_onset, cursor = Fraction(0, 1), Fraction(0, 1), Fraction(0, 1)
        pending_notes = []
        voice_stacks = SafeDict(lambda id: init_voice_stack(id))    # map id to list where first in list is Voice and rest (nested) Tuplets
        site = None
        active_beams = {}   # <voice-id, Beam> (non grace beams (grace beams can occur within normal beams))
        grace_beam = None
        grace_chords = []   # save grace chords with beam_info and voice-id until their chord is specified
        octave_shifts = {}  # <Staff, (onset: Fraction, Octavation)>
        # cache <onset, signature> to apply signature without number at the end when all staffs defined
        key_signatures = {}
        time_signatures = {}

        def init_voice_stack(id):
            voice_stacks[id] = []
            voice_stacks[id].append(part._voices[id])
        
        def process_time(root):
            number = root.attrib.get("number")
            numerator = 1
            denominator = 1
            for elem in root:
                if elem.tag == "beats":
                    numerator = int(elem.text)
                elif elem.tag == "beat-type":
                    denominator = int(elem.text)
                else:
                    raise ValueError("Symbolic time signature must be 4/4 or 2/2.")
            symbolic = root.attrib.get("symbol") == "common" or root.attrib.get("symbol") == "cut"
            if number is not None:
                part._staffs[int(number) - 1].insert_time_signature(cursor, TimeSignature(numerator, denominator, symbolic))
            else:
                time_signatures[cursor] = TimeSignature(numerator, denominator, symbolic)

        def process_key(root):
            number = root.attrib.get("number")
            accIndex = 0
            mode = True
            for elem in root:
                if elem.tag == "fifths":
                    accIndex = int(elem.text)
                elif elem.tag == "mode":
                    mode = elem.text == "minor"
            if number is not None:
                part._staffs[int(number) - 1].insert_key_signature(cursor, KeySignature(accIndex, mode))
            else:
                key_signatures[cursor] = KeySignature(accIndex, mode)

        def process_clef(root):
            # clef is different, here no number means first staff
            number = root.attrib.get("number")
            staff_number = 0
            clef_type = None
            octave_shift = 0
            if number is not None:
                staff_number = int(number) - 1
            for elem in root:
                if elem.tag == "sign":
                    clef_name = elem.text
                    if clef_name == "G":
                        clef_type = ClefType.TREBLE
                    elif clef_name == "F":
                        clef_type = ClefType.BASS
                    elif clef_name == "C":
                        clef_type = ClefType.ALTO    # standard C-clef if no line given -> line=3
                    elif clef_name == "percussion":
                        clef_type = ClefType.PERCUSSION
                    elif clef_name == "TAB":
                        raise NotImplementedError("TABs not supported due to lack of tests.")
                    else:
                        raise ValueError(f"Couldn't resolve clef with name: {clef_name}")
                elif elem.tag == "line":
                    if clef_type == ClefType.ALTO:
                        staff_line = int(elem.text)
                        if staff_line == 1:
                            clef_type = ClefType.SOPRANO
                        elif staff_line == 2:
                            clef_type = ClefType.MEZZO_SOPRANO
                        elif staff_line == 3:
                            clef_type = ClefType.ALTO
                        elif staff_line == 4:
                            clef_type = ClefType.TENOR
                        elif staff_line == 5:
                            clef_type = ClefType.BARITONE
                        else:
                            raise ValueError(f"Invalid line parameter {staff_line} for C clef.")
                elif elem.tag == "clef-octave-change":
                    octave_shift = int(elem.text)
            if clef_type is None:
                raise ValueError("Mandatory attribute 'sign' missing from clef definition.")
            part._staffs[staff_number].insert_clef(cursor, Clef(clef_type, octave_shift))
                    
        def tie_if_needed(note, tie_start, tie_stop):
            if tie_stop:
                for i, n in enumerate(pending_notes):
                    if n._pitch == note._pitch:
                        # can't use Note.tie_notes() here because notes are not yet added to chords!
                        n._next_tied = note
                        note._previous_tied = n
                        pending_notes.pop(i)
                        break
            if tie_start:
                pending_notes.append(note)

        def process_tuplet(root, time_mod):
            # 'useless' tuplet. preinitialize time mod, but values must be present and overwritten!
            if time_mod is None:
                time_mod = [1, NoteType.QUARTER, 0, 1]
            # make sure if no values are provided, those specified in time_mod are used
            normal = [time_mod[0], time_mod[1], time_mod[2]]
            actual = [time_mod[3], time_mod[1], time_mod[2]]
            for elem in root.iter():
                if elem.tag == "tuplet-normal":
                    normal[0] = 0   # prepare dots field to be written to
                    for child in elem:
                        if child.tag == "tuplet-number":
                            normal[0] = int(child.text)
                        elif child.tag == "tuplet-type":
                            normal[1] = NoteType.from_common_name(child.text)
                        elif child.tag == "tuplet-dot":
                            normal[2] += 1
                elif elem.tag == "tuplet-actual":
                    actual[0] = 0   # prepare dots field to be written to
                    for child in elem:
                        if child.tag == "tuplet-number":
                            actual[0] = int(child.text)
                        elif child.tag == "tuplet-type":
                            actual[1] = NoteType.from_common_name(child.text)
                        elif child.tag == "tuplet-dot":
                            actual[2] += 1
            return Tuplet(*normal, *actual)

        def process_note(root):
            nonlocal current_onset
            nonlocal cursor
            nonlocal site
            nonlocal grace_beam
            invisible = root.attrib.get("print-object") == "no"
            note_name = None
            note_type = None
            octave = None
            dots = 0
            pitch = 12
            accidental = None
            stem = None
            voice_id = None
            staff = part._staffs[0] # staff node not listed for treble only scores
            duration = None
            is_grace = False
            is_rest = False
            is_chord = False
            tie_start = False
            tie_stop = False
            beam_info = None
            time_mod = None     # [normal_notes, normal_type, normal_dots, actual_notes]
            num_tuplet_ends = 0
            expressions = []
            has_fermata = False

            for elem in root:
                if elem.tag == "grace":
                    is_grace = True
                elif elem.tag == "pitch":
                    for child in elem:
                        if child.tag in ["step", "display-step"]:
                            text = child.text
                            note_name = NoteName[text]     # python equivalent to Javas 'valueOf()'
                            pitch += note_name.value
                        elif child.tag in ["octave", "display-octave"]:
                            octave = int(child.text)
                            pitch += octave * 12
                elif not is_rest and elem.tag == "alter":
                    pitch += int(elem.text)
                elif elem.tag == "dot":
                    dots += 1
                elif elem.tag == "beam":
                    if elem.attrib.get("number") == "1":
                        beam_info = elem.text
                elif elem.tag == "accidental":
                    accidental = accidental_by_common_name[elem.text]
                elif elem.tag == "stem":
                    text = elem.text
                    if text == "up":
                        stem = Stem.UP
                    elif text == "down":
                        stem = Stem.DOWN
                elif elem.tag == "voice":
                    voice_id = int(elem.text)
                    voice_stacks[voice_id]  # make sure entry exists
                elif elem.tag == "chord":
                    is_chord = True
                elif elem.tag == "staff":
                    staff = part._staffs[int(elem.text) - 1]
                elif elem.tag == "rest":
                    is_rest = True
                elif elem.tag == "duration":
                    duration = Fraction(int(elem.text), divisions_per_quarter_note * 4)
                elif elem.tag == "type":
                    note_type = NoteType.from_common_name(elem.text)
                elif elem.tag == "time-modification":
                    normal_notes, normal_dots, actual_notes = 0, 0, 0
                    normal_type = None
                    for child in elem:
                        if child.tag == "normal-notes":
                            normal_notes = int(child.text)
                        elif child.tag == "normal-type":
                            normal_type = NoteType.from_common_name(child.text)
                        elif child.tag == "normal-dot":
                            normal_dots += 1
                        elif child.tag == "actual-notes":
                            actual_notes = int(child.text)
                    if normal_type is None:     # if normal_type is absent, use note_type
                        normal_type = note_type
                        normal_dots = dots
                    time_mod = [normal_notes, normal_type, normal_dots, actual_notes]
                elif elem.tag == "notations":
                    for child in elem:
                        if child.tag == "tuplet":
                            if child.attrib.get("type") == "start":
                                tuplet = process_tuplet(child, time_mod)
                                voice_stacks[voice_id][-1].append_tuplet(tuplet)    # append directly to voice so that functions work properly
                                voice_stacks[voice_id].append(tuplet)
                            elif child.attrib.get("type") == "stop":
                                num_tuplet_ends += 1    # delay tuplet removal from stack after note has gotten correct site
                        elif child.tag == "arpeggiate":
                            expressions.append(Expression.ARPEGGIO)
                        elif child.tag == "ornaments":
                            for c in child:
                                if c.tag == "trill-mark":
                                    expressions.append(Expression.TRILL)
                                elif c.tag == "mordent":
                                    expressions.append(Expression.MORDENT)
                        elif child.tag == "articulations":
                            for c in child:
                                if c.tag == "accent":
                                    expressions.append(Expression.ACCENT)
                                elif c.tag == "strong-accent":
                                    expressions.append(Expression.MARCATO)
                                elif c.tag == "staccato":
                                    expressions.append(Expression.STACCATO)
                                elif c.tag == "staccatissimo":
                                    expressions.append(Expression.STACCATISSIMO)
                                elif c.tag == "tenuto":
                                    expressions.append(Expression.TENUTO)
                        elif child.tag == "dynamics":
                            for dynamic in child:
                                staff._dynamics[cursor] = Dynamics(dynamic.tag)
                        elif child.tag == "fermata":
                            has_fermata = True
                elif elem.tag == "tie":
                    if elem.attrib.get("type") == "stop":
                        tie_stop = True
                    elif elem.attrib.get("type") == "start":
                        tie_start = True
            # finally process all the info and create the element
            if not is_chord:
                current_onset = cursor
            if is_grace:
                if is_chord:
                    assert len(grace_chords) > 0, "Assumed GraceChord to be present here."
                    grace_chord = grace_chords[-1][0]
                    note = Note(note_name, octave, pitch, accidental)
                    tie_if_needed(note, tie_start, tie_stop)
                    grace_chord.add_note(note)
                else:
                    grace_chord = GraceChord(note_type, dots, stem)
                    grace_chord._expressions = expressions
                    note = Note(note_name, octave, pitch, accidental)
                    tie_if_needed(note, tie_start, tie_stop)
                    grace_chord.add_note(note)
                    grace_chords.append((grace_chord, beam_info))
            else:
                # get current site (Voice/Tuplet). Chord notes reuse their first note's site
                if not is_chord:
                    site = voice_stacks[voice_id][-1]
                if note_type is None:
                    # measure rest - use XML specified duration and set to standard NoteType (WHOLE)
                    assert is_rest, "Expected measure rest here"
                    site.insert_chord_or_rest(current_onset, Rest(NoteType.WHOLE, 0, measure_duration=duration, invisible=invisible), staff)
                    cursor += duration
                else:
                    # calculate duration yourself because musicxml's is wrong for nested tuplets
                    duration = note_type.get_value(dots)
                    if time_mod is not None:
                        duration *= Fraction(time_mod[0], time_mod[3])
                    if is_chord:
                        chord_to_add = site._elements.values()[-1]
                        assert isinstance(chord_to_add, Chord), "Expected to find chord as last element in voice"
                        note = Note(note_name, octave, pitch, accidental)
                        tie_if_needed(note, tie_start, tie_stop)
                        chord_to_add.add_note(note)
                    else:
                        chord_rest = None
                        if is_rest:
                            chord_rest = Rest(note_type, dots, invisible=invisible)
                            site.insert_chord_or_rest(current_onset, chord_rest, staff)
                        else:
                            note = Note(note_name, octave, pitch, accidental)
                            tie_if_needed(note, tie_start, tie_stop)
                            chord_rest = site.insert_note(current_onset, note, staff, note_type, dots, stem)
                            chord_rest._expressions = expressions
                            if has_fermata:
                                chord_rest._event._fermata = True
                            # append potential grace chords with beams (can occur within normal beam)
                            for grace_info in grace_chords:
                                chord_rest.add_grace_chord(grace_info[0])
                                if grace_info[1] == "begin":
                                    grace_beam = BeamGroup()
                                    grace_beam.add_chord_or_rest(grace_info[0])
                                elif grace_info[1] == "continue":
                                    grace_beam.add_chord_or_rest(grace_info[0])
                                elif grace_info[1] == "end":
                                    grace_beam.add_chord_or_rest(grace_info[0])
                            grace_chords.clear()
                            grace_beam = None
                        # handle beam of chord/rest
                        if beam_info == "begin":
                            beam_group = BeamGroup()
                            active_beams[voice_id] = beam_group
                            beam_group.add_chord_or_rest(chord_rest)
                        elif beam_info == "continue":
                            active_beams[voice_id].add_chord_or_rest(chord_rest)
                        elif beam_info == "end":
                            active_beams.pop(voice_id).add_chord_or_rest(chord_rest)
                        # chords and rests can have fermata
                        if has_fermata:
                            chord_rest._fermata = True
                        # advance cursor
                        cursor += duration
                    # pop tuplet ends from stack (chords will reuse their first note's site)
                    for _ in range(num_tuplet_ends):
                        voice_stacks[voice_id].pop()
        
        def process_attributes(root):
            for elem in root:
                if elem.tag == "divisions":
                    nonlocal divisions_per_quarter_note
                    divisions_per_quarter_note = int(elem.text)
                elif elem.tag == "time":
                    process_time(elem)
                elif elem.tag == "key":
                    process_key(elem)
                elif elem.tag == "clef":
                    process_clef(elem)

        def process_direction(root):
            staff = None
            octavation = None
            octavation_start = None
            dynamics = None
            # extract information
            for elem in root:
                if elem.tag == "direction-type":
                    for child in elem:
                        if child.tag == "octave-shift":
                            octavation_start = True
                            # musicxml means visual shift not pitch shift, so 'up is down'
                            if child.attrib.get("type") == "up":     # this is 'bassa' (shift notes up visually)
                                octavation = Octavation(-(int(child.attrib.get("size")) // 7))
                            elif child.attrib.get("type") == "down": # this is 'alta' (shift notes down visually)
                                octavation = Octavation(int(child.attrib.get("size")) // 7)
                            elif child.attrib.get("type") == "stop":
                                octavation_start = False
                        elif child.tag == "dynamics":
                            # musicXML allows several dynamics. For now, last rules
                            for dynamic in child:
                                dynamics = dynamic.tag
                        elif child.tag == "coda":
                            part._score._repeat_manager._repeat_marks[cursor] = RepeatMark.CODA
                        elif child.tag == "segno":
                            part._score._repeat_manager._repeat_marks[cursor] = RepeatMark.SEGNO
                        elif child.tag == "words":
                            if child.text == "Fine":
                                part._score._repeat_manager._repeat_marks[cursor] = RepeatMark.FINE
                            elif child.text == "D.C.":
                                part._score._repeat_manager._repeat_commands[cursor] = RepeatCommand.DA_CAPO
                            elif child.text == "D.C. al Fine":
                                part._score._repeat_manager._repeat_commands[cursor] = RepeatCommand.DA_CAPO_AL_FINE
                            elif child.text == "D.C. al Coda":
                                part._score._repeat_manager._repeat_commands[cursor] = RepeatCommand.DA_CAPO_AL_CODA
                            elif child.text == "D.S.":
                                part._score._repeat_manager._repeat_commands[cursor] = RepeatCommand.DAL_SEGNO
                            elif child.text == "D.S. al Fine":
                                part._score._repeat_manager._repeat_commands[cursor] = RepeatCommand.DAL_SEGNO_AL_FINE
                            elif child.text == "D.S. al Coda":
                                part._score._repeat_manager._repeat_commands[cursor] = RepeatCommand.DAL_SEGNO_AL_CODA
                elif elem.tag == "staff":
                    staff = part._staffs[int(elem.text) - 1]
            # parse collected information
            if octavation_start is not None:
                if octavation_start:
                    octave_shifts[staff] = (cursor, octavation)
                else:
                    assert octave_shifts[staff], "Found octave shift without a start."
                    onset, octavation = octave_shifts[staff]
                    octave_shift = OctaveShift(staff, onset, current_onset, octavation)
                    staff.insert_octave_shift(octave_shift)
            if dynamics is not None:
                staff._dynamics[cursor] = Dynamics(dynamics)
        
        def process_measure(root):
            nonlocal cursor
            nonlocal longest_voice_offset
            measure_onset = cursor
            # loop over elements
            for elem in root:
                if elem.tag == "attributes":
                    process_attributes(elem)
                elif elem.tag == "note":
                    process_note(elem)
                elif elem.tag == "backup":
                    longest_voice_offset = max(longest_voice_offset, cursor)
                    cursor -= Fraction(int(elem[0].text), divisions_per_quarter_note * 4)
                elif elem.tag == "forward":
                    cursor += Fraction(int(elem[0].text), divisions_per_quarter_note * 4)
                elif elem.tag == "direction":
                    process_direction(elem)
                elif elem.tag == "barline":
                    for child in elem:
                        if child.tag == "repeat":
                            if child.attrib.get("direction") == "forward": 
                                part._score._repeat_manager._repeat_starts.add(cursor)
                            elif child.attrib.get("direction") == "backward":
                                part._score._repeat_manager._repeat_ends.add(cursor)
                        elif child.tag == "coda":
                            part._score._repeat_manager._repeat_marks[cursor] = RepeatMark.CODA
                        elif child.tag == "segno":
                            part._score._repeat_manager._repeat_marks[cursor] = RepeatMark.SEGNO
            # advance onset to end of measure
            longest_voice_offset = max(longest_voice_offset, cursor)
            cursor = longest_voice_offset
            longest_voice_offset = Fraction(0, 1)
            # create measure object
            part.insert_measure(measure_onset, Measure())

        # end of subfunction declarations
        for elem in root:
            if elem.tag == "measure":
                process_measure(elem)
        # handle signatures meant for all staves (now safely defined)
        for onset, key in key_signatures.items():
            for staff in part.get_staffs():
                staff.insert_key_signature(onset, key)
        for onset, time in time_signatures.items():
            for staff in part.get_staffs():
                staff.insert_time_signature(onset, time)
        return part

    # =============== READ THE FILE =============
    extension = os.path.splitext(filepath)[1]
    if extension != ".xml" and extension != ".musicxml":
        raise ValueError("Invalid file extension. Must be .xml or .musicxml.")
    
    with open(filepath, "r") as file:
        tree = ET.parse(file)
        root = tree.getroot()
        if root.tag != 'score-partwise':
            raise Exception(f"Cannot parse MusicXML files in {root.tag}.")
        
        score = Score()
        # traverse xml elements only once
        for elem in root:
            if elem.tag == "part":
                part = Part()
                score.append_part(part)
                part = process_part(elem, part)
            
    return score
