from music_model import *
from fractions import Fraction
from xml.etree import ElementTree as ET
import xml.dom.minidom as dom
import os, math, functools, subprocess, tempfile
from IPython.display import display, Image
XML_VERSION = 3.1
PATH_TO_MUSESCORE_EXE = "C:/Program Files/MuseScore 3/bin/MuseScore3.exe"


def _parse_to_xml(score: Score, pretty: bool = False) -> str:
    """ parse to musicXML using 'score-partwise' encoding.
    """
    clefs_with_note_names = {ClefType.TREBLE, ClefType.BASS, ClefType.SOPRANO, ClefType.MEZZO_SOPRANO, ClefType.ALTO, ClefType.TENOR, ClefType.BARITONE}
    to_accidental_text = {
        Accidental.SHARP: "sharp",
        Accidental.FLAT: "flat",
        Accidental.NATURAL: "natural",
        Accidental.DOUBLE_SHARP: "double-sharp",
        Accidental.FLAT_FLAT: "flat-flat"
    }
    first_attributes_in_score = True

    def get_export_division(score: Score):
        denominators = set()
        for part in score._parts:
            for staff in part._staffs.values():
                for time in staff._events.keys():
                    denominators.add(time.denominator)
        # compute least common denominator
        return functools.reduce(lambda x, y: abs(x*y) // math.gcd(x, y), denominators, 1)
    division = get_export_division(score)

    def to_division(time):
        return (time.numerator*4*division) // time.denominator
    
    def create_title(xml_root):
        work = ET.SubElement(xml_root, "work")
        work_title = ET.SubElement(work, "work-title")
        work_title.text = "Songtitle"  # TODO: save title in score class

    def create_default_page_layout(xml_root):
        xml_defaults = ET.SubElement(xml_root, "defaults")
        scaling = ET.SubElement(xml_defaults, "scaling")
        ET.SubElement(scaling, "millimeters").text = "7.04"
        ET.SubElement(scaling, "tenths").text = "40"
        # A4 page layout (297mm x 210mm). all measures are in tenths
        page_layout = ET.SubElement(xml_defaults, "page-layout")
        ET.SubElement(page_layout, "page-height").text = "1687.5"
        ET.SubElement(page_layout, "page-width").text = "1193.2"
        page_margins = ET.SubElement(page_layout, "page-margins", attrib={"type": "both"})
        ET.SubElement(page_margins, "left-margin").text = "56"
        ET.SubElement(page_margins, "right-margin").text = "56"
        ET.SubElement(page_margins, "top-margin").text = "56"
        ET.SubElement(page_margins, "bottom-margin").text = "113"

    def create_part_list(xml_root, score: Score):
        part_list = ET.SubElement(xml_root, "part-list")
        for i, _ in enumerate(score._parts):
            score_part = ET.SubElement(part_list, "score-part", id=f"P{i+1}")
            part_name = ET.SubElement(score_part, "part-name")
            part_name.text = "Music"
    
    # =============== BEGIN OF PART SCOPE =============
    def create_part(xml_part, part: Part):
        # keep track to do these only once
        created_contexts = set()
        created_octave_shifts = set()
        closed_octave_shifts = set()
        beam_info = {}  # map ChorRests to list of beam info once start of BeamGroup is encountered

        def create_backup(xml_measure, duration):
            backup = ET.SubElement(xml_measure, "backup")
            ET.SubElement(backup, "duration").text = str(to_division(duration))

        def create_forward(xml_measure, duration):
            forward = ET.SubElement(xml_measure, "forward")
            ET.SubElement(forward, "duration").text = str(to_division(duration))

        def create_key(xml_attributes, key_signature):
            xml_key = ET.SubElement(xml_attributes, "key")
            ET.SubElement(xml_key, "fifths").text = str(key_signature._fifths)

        def create_time(xml_attributes, time_signature):
            xml_time = ET.SubElement(xml_attributes, "time")
            if (time_signature._symbolic):
                if time_signature._numerator == 4:
                    xml_time.set("symbol", "common")
                elif time_signature._numerator == 2:
                    xml_time.set("symbol", "cut")
            ET.SubElement(xml_time, "beats").text = str(time_signature._numerator)
            ET.SubElement(xml_time, "beat-type").text = str(time_signature._denominator)

        def create_clef(xml_attributes, clef, number):
            xml_clef = ET.SubElement(xml_attributes, "clef", number=str(number))
            ET.SubElement(xml_clef, "sign").text = clef._clef_type.get_note_name().name if clef._clef_type in clefs_with_note_names else clef._clef_type.name
            ET.SubElement(xml_clef, "line").text = str(clef._clef_type.get_staff_line())
            if clef._clef_type == ClefType.TREBLE and clef._octave != 4:
                ET.SubElement(xml_clef, "clef-octave-change").text = str(clef._octave - 4)
            elif clef._clef_type == ClefType.BASS and clef._octave != 3:
                ET.SubElement(xml_clef, "clef-octave-change").text = str(clef._octave - 3)
            
        def create_time_modification_if_necessary(xml_note, chord_rest):
            # cumulate time-mods from tuplets
            time_mod = Fraction(1, 1)
            site = chord_rest._site
            while isinstance(site, Tuplet):
                time_mod *= site._time_mod
                site = site._site
            if time_mod != 1:
                xml_time_mod = ET.SubElement(xml_note, "time-modification")
                ET.SubElement(xml_time_mod, "actual-notes").text = str(time_mod.denominator)
                ET.SubElement(xml_time_mod, "normal-notes").text = str(time_mod.numerator)
                # TODO when to add normal-type and normal-dot here?

        def create_tuplet_if_necessary(xml_note, chord_rest):
            tuplets = []
            site = chord_rest._site
            while isinstance(site, Tuplet):
                tuplets.append(site)
                site = site._site
            # create tuplets from outer most to inner most
            for i in range(len(tuplets)):
                tuplet = tuplets[-1-i]  # reverse access tuplets
                # tuplet start
                if tuplet.get_first_chord_or_rest() is chord_rest:
                    xml_notations = ET.SubElement(xml_note, "notations")
                    xml_tuplet = ET.SubElement(xml_notations, "tuplet", type="start")
                    xml_tuplet.set("number", str(i+1))
                    # TODO get this from beam if beam exists with same elements instead of 'yes'
                    xml_tuplet.set("bracket", "yes")
                    if len(tuplets) > 1:
                        xml_actual = ET.SubElement(xml_tuplet, "tuplet-actual")
                        ET.SubElement(xml_actual, "tuplet-number").text = str(tuplet._actual_count)
                        ET.SubElement(xml_actual, "tuplet-type").text = tuplet._actual_type.common_name
                        for _ in range(tuplet._actual_dots):
                            ET.SubElement(xml_actual, "tuplet-dot")
                        xml_normal = ET.SubElement(xml_tuplet, "tuplet-normal")
                        ET.SubElement(xml_normal, "tuplet-number").text = str(tuplet._normal_count)
                        ET.SubElement(xml_normal, "tuplet-type").text = tuplet._note_type.common_name
                        for _ in range(tuplet._dots):
                            ET.SubElement(xml_normal, "tuplet-dot")
                # tuplet end
                elif tuplet.get_last_chord_or_rest() is chord_rest:
                    xml_notations = ET.SubElement(xml_note, "notations")
                    xml_tuplet = ET.SubElement(xml_notations, "tuplet", type="stop")
                    xml_tuplet.set("number", str(i+1))

        def create_beam_info_if_necessary(chord_rest):
            beam_group = chord_rest.get_beam_group()
            if beam_group is not None and beam_group.get_chords_and_rests()[0] == chord_rest:
                chord_rests = beam_group.get_chords_and_rests()
                numbers = [-chord_rest._note_type.base2_exponent - 2 for chord_rest in chord_rests]
                for i, number in enumerate(numbers):
                    info = []
                    for n in range(number):
                        if i == 0 or n+1 > numbers[i-1]:
                            if i == len(numbers)-1:
                                info.append("backward hook")
                            else:
                                if n+1 <= numbers[i+1]:
                                    info.append("begin")
                                else:
                                    info.append("forward hook")
                        else:
                            if i == len(numbers)-1 or n+1 > numbers[i+1]:
                                info.append("end")
                            else:
                                info.append("continue")
                    beam_info[chord_rests[i]] = info

        def create_rest(xml_measure, rest):
            create_beam_info_if_necessary(rest)
            xml_note = ET.SubElement(xml_measure, "note")
            if rest._invisible:
                xml_note.set("print-object", "no")
            if rest._is_measure_rest:
                ET.SubElement(xml_note, "rest", measure="yes")
                ET.SubElement(xml_note, "duration").text = str(to_division(rest.get_duration()))
                ET.SubElement(xml_note, "voice").text = str(rest.get_voice()._id)
            else:
                ET.SubElement(xml_note, "rest", measure="yes")
                ET.SubElement(xml_note, "duration").text = str(to_division(rest.get_duration()))
                ET.SubElement(xml_note, "voice").text = str(rest.get_voice()._id)
                ET.SubElement(xml_note, "type").text = rest._note_type.common_name
                for _ in range(rest._dots):
                    ET.SubElement(xml_note, "dot")
                create_time_modification_if_necessary(xml_note, rest)
            ET.SubElement(xml_note, "staff").text = str(rest.get_staff()._id + 1)
            create_tuplet_if_necessary(xml_note, rest)

        def create_chord(xml_measure, chord, grace = False):
            create_beam_info_if_necessary(chord)
            # go over notes
            for i, note in enumerate(chord._notes):
                xml_note = ET.SubElement(xml_measure, "note")
                if grace:
                    ET.SubElement(xml_note, "grace")
                if i > 0:
                    ET.SubElement(xml_note, "chord")
                xml_pitch = ET.SubElement(xml_note, "pitch")
                ET.SubElement(xml_pitch, "step").text = note._note_name.name
                alter = note.get_alter()
                if alter != 0:
                    ET.SubElement(xml_pitch, "alter").text = str(alter)
                ET.SubElement(xml_pitch, "octave").text = str(note._octave)
                if not grace:
                    ET.SubElement(xml_note, "duration").text = str(to_division(note.get_duration()))
                if note._next_tied:
                    ET.SubElement(xml_note, "tie", type="start")
                if note._previous_tied:
                    ET.SubElement(xml_note, "tie", type="stop")
                ET.SubElement(xml_note, "voice").text = str(note._chord.get_voice()._id)
                ET.SubElement(xml_note, "type").text = note._chord._note_type.common_name
                for _ in range(note._chord._dots):
                    ET.SubElement(xml_note, "dot")
                if note._accidental is not None:
                    ET.SubElement(xml_note, "accidental").text = to_accidental_text[note._accidental]
                if not grace:
                    create_time_modification_if_necessary(xml_note, note._chord)
                if note._chord._stem:
                    ET.SubElement(xml_note, "stem").text = "up" if note._chord._stem == Stem.UP else "down"
                ET.SubElement(xml_note, "staff").text = str(note._chord.get_staff()._id + 1)
                if i == 0:
                    if chord in beam_info:
                        for i, state in enumerate(beam_info[chord]):
                            ET.SubElement(xml_note, 'beam', number=str(i+1)).text = state
                    if not grace:
                        create_tuplet_if_necessary(xml_note, note._chord)
                if note._next_tied:
                    xml_tied = ET.SubElement(xml_note, "notations")
                    ET.SubElement(xml_tied, "tied", type="start")
                if note._previous_tied:
                    xml_tied = ET.SubElement(xml_note, "notations")
                    ET.SubElement(xml_tied, "tied", type="stop")

        def create_attributes_if_necessary(xml_measure, staff, onset):
            nonlocal first_attributes_in_score
            # Create xml_attributes element but don't add to xml_measure directly
            xml_attributes = ET.Element("attributes")
            if first_attributes_in_score:
                ET.SubElement(xml_attributes, "divisions").text = str(division)
            # do key signature
            key = staff._key_signatures.get(onset)  # None if no key exists at that onset
            if key and key not in created_contexts:
                create_key(xml_attributes, key)
                created_contexts.add(key)
            # do time signature
            time = staff._time_signatures.get(onset)  # None if no time exists at that onset
            if time and time not in created_contexts:
                create_time(xml_attributes, time)
                created_contexts.add(time)
            # aff number of staffs if first attributes in score
            if first_attributes_in_score:
                ET.SubElement(xml_attributes, "staves").text = str(len(part._staffs))
            # do clefs
            clef = staff._clefs.get(onset)  # None if no clef exists at that onset
            if clef and clef not in created_contexts:
                create_clef(xml_attributes, clef, staff._id + 1)
                created_contexts.add(clef)
            # finally, append to xml_measure if attributes are not empty
            if len(xml_attributes) > 0:
                xml_measure.append(xml_attributes)
                first_attributes_in_score = False

        def create_octave_shift_start_if_necessary(xml_measure, staff, onset):
            if staff._octave_shifts.get(onset):
                octave_shift = staff._octave_shifts.get(onset)
                # if not already handled
                if octave_shift in created_octave_shifts:
                    return
                shift = octave_shift._ottavation.value
                xml_direction = ET.SubElement(xml_measure, "direction", placement="above" if shift > 0 else "below")
                xml_dir_type = ET.SubElement(xml_direction, "direction-type")
                ET.SubElement(xml_dir_type, "octave-shift", type="down" if shift > 0 else "up", size=str(abs(shift*7) + 1), number="1")
                ET.SubElement(xml_direction, "staff").text = str(staff._id + 1)
                created_octave_shifts.add(octave_shift)

        def create_octave_shift_end_if_necessary(xml_measure, staff, onset):
            octave_shift = staff._octave_shifts[onset]
            if octave_shift and octave_shift.get_offset() == onset:
                # if not already handled
                if octave_shift in closed_octave_shifts:
                    return
                shift = octave_shift._ottavation.value
                xml_direction = ET.SubElement(xml_measure, "direction", placement="above" if shift > 0 else "below")     # mayve add placement
                xml_dir_type = ET.SubElement(xml_direction, "direction-type")
                ET.SubElement(xml_dir_type, "octave-shift", type="stop", size=str(abs(shift*7) + 1), number="1")
                ET.SubElement(xml_direction, "staff").text = str(staff._id + 1)
                closed_octave_shifts.add(octave_shift)

        def create_measure(xml_measure, part, measure):
            onset = measure._onset
            if measure._repetition_start:
                xml_barline = ET.SubElement(xml_measure, "barline")
                ET.SubElement(xml_barline, "repeat", direction="forward")
            for voice in part._voices.values():
                # backup to measure onset if necessary (from prior voices)
                if onset > measure._onset:
                    create_backup(xml_measure, onset - measure._onset)
                    onset = measure._onset
                # loop over elements of voice within measure
                for chord_rest in voice.get_chords_and_rests(measure._onset, measure.get_offset(), (True, False)):
                    # forward to element's onset if needed
                    if onset < chord_rest.get_onset():
                        create_forward(xml_measure, chord_rest.get_onset() - onset)
                        onset = chord_rest.get_onset()
                    # check if attributes are required for current staff and onset
                    create_attributes_if_necessary(xml_measure, chord_rest.get_staff(), onset)
                    create_octave_shift_start_if_necessary(xml_measure, chord_rest.get_staff(), onset)
                    # create element itself
                    if isinstance(chord_rest, Chord):
                        for grace_chord in chord_rest._grace_chords:
                            create_chord(xml_measure, grace_chord, grace=True)
                        create_chord(xml_measure, chord_rest)
                    else:
                        create_rest(xml_measure, chord_rest)
                    create_octave_shift_end_if_necessary(xml_measure, chord_rest.get_staff(), onset)
                    onset += chord_rest.get_duration()
            # all voices handled
            # create forward to bar offset if voice ends prematurely
            if onset < measure.get_offset():
                create_forward(xml_measure, measure.get_offset() - onset)
            if measure._repetition_end:
                xml_barline = ET.SubElement(xml_measure, "barline")
                ET.SubElement(xml_barline, "repeat", direction="backward")

        # =============== END OF PART SCOPE FUNCTION DECLARATIONS =============
        for measure in part._staffs[0]._measures.values():
            xml_measure = ET.SubElement(xml_part, "measure", number=str(measure.get_index() + 1))
            create_measure(xml_measure, part, measure)
    # =============== END OF PART SCOPE =============
            
    # =============== END OF SCORE SCOPE FUNCTION DECLARATIONS =============
    root = ET.Element("score-partwise", version=str(XML_VERSION))
    #create_title(root)
    xml_identification = ET.SubElement(root, "identification")
    xml_encoding = ET.SubElement(xml_identification, "encoding")
    # ET.SubElement(xml_encoding, 'supports', {
    #     'element': 'print',
    #     'attribute': 'new-system',
    #     'type': 'yes',
    #     'value': 'yes'
    # })
    ET.SubElement(xml_encoding, 'supports', {
        'element': 'beam',
        'type': 'yes'
    })
    create_default_page_layout(root)
    create_part_list(root, score)
    # create parts one by one
    for i, part in enumerate(score._parts):
        xml_part = ET.SubElement(root, "part", id=f"P{i+1}")
        create_part(xml_part, part)
    # convert the resulting XML structure to string
    result = ET.tostring(root, encoding="unicode", xml_declaration=True)
    if not pretty:
        return result
    parsed = dom.parseString(result)
    return parsed.toprettyxml(indent="  ")


def write_xml_file(score: Score, filepath: str):
    xml_content = _parse_to_xml(score, pretty=True)
    with open(filepath, 'w', encoding='utf-8') as xml_file:
        xml_file.write(xml_content)


def show_xml(score: Score):
    print(_parse_to_xml(score, pretty=True))


def show(score: Score, dpi: int = 100, margin_in_px: int = 0):
    xml_content = _parse_to_xml(score)
    # get the system's temp directory
    with tempfile.TemporaryDirectory() as temp:
        # create a temporary file for the XML content
        xml_file_path = os.path.join(temp, 'score.xml')
        with open(xml_file_path, 'w') as xml_file:
            xml_file.write(xml_content)
        output_image_path = os.path.join(temp, 'score.png')
        # run MuseScore to create images
        command = [
            PATH_TO_MUSESCORE_EXE,
            xml_file_path,
            "-o", output_image_path,
            "-r", str(dpi),
            "-T", str(margin_in_px)
        ]
        subprocess.run(command, check=True)
        # Display the generated image(s) in the Jupyter notebook
        display(Image(filename=temp + "\score" + "-1" + ".png"))  # TODO handle multiple pages and -01 indexing
