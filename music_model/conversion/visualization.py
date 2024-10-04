from music_model import *
NL = ',\n'


def embed_in_html(content: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VexFlow Music Notation</title>
    <script src="https://unpkg.com/vexflow/releases/vexflow-min.js"></script>
</head>
<body>
    <div id="output"></div>
    <script>
    {content}
    </script>
</body>
</html>"""

def parse_to_js(score: Score) -> str:
    def parse_chord(chord: Chord) -> str:
        keys = ', '.join(f'"{note._note_name.name}/{note._octave}"' for note in chord._notes)
        duration = f"{chord._note_type.value.denominator}" + "." * chord._dots
        result = "new StaveNote({ "
        result += f"keys: [{keys}], duration: \"{duration}\""
        if chord._stem is not None:
            result += f", stem_direction: {chord._stem.value}"
        return result + " })"
    #.addModifier(new Accidental("b")),

    def parse_rest(rest: Rest) -> str:
        keys = "b/4"    # TODO position rest properly
        return f"new StaveNote({{ keys: [\"{keys}\"], duration: \"{rest._nominal_duration.denominator}r\" }})"

    def parse_voice(voice: Voice) -> str:
        stave_notes = []
        for chord_rest in voice.get_chords_and_rests():
            if isinstance(chord_rest, Chord):
                stave_notes.append(parse_chord(chord_rest))
            else:
                stave_notes.append(parse_rest(chord_rest))
        return f"new Voice().addTickables([\n{NL.join(stave_notes)}\n])"


    result = """const { Renderer, Stave, StaveNote, Voice, Formatter } = Vex.Flow;
const div = document.getElementById("output");
const renderer = new Renderer(div, Renderer.Backends.SVG);
renderer.resize(500, 500);
const context = renderer.getContext();

const stave = new Stave(0, 0, 400);
stave.addClef("treble").addTimeSignature("4/4");
stave.setContext(context).draw();
"""
    # parse voices
    voices = []
    for voice in score.get_parts()[0].get_voices():
        voices.append(parse_voice(voice))
    result += f"const voices = [\n{NL.join(voices)}\n];"
    # render voices
    result += """
new Formatter().joinVoices(voices).format(voices, 350);
voices.forEach(function (v) {
    v.draw(context, stave);
});
"""
    return result
