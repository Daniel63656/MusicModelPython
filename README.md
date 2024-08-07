## MusicModel

```mermaid
classDiagram
    class Score {
    }

    class Part {
        Score : score
        Instrument : instrument
    }

    class Staff {
        Part : part
        int : id
    }

    class Event {
        Fraction : onset
    }

    class Clef {
        int : staff_line
        NoteName : note_name
        int : octave
    }

    class KeySignature {
        int : fifths
        boolean : mode
    }

    class TimeSignature {
        int : beats
        int : beat_type
    }

    class OctaveShift {
        Staff : staff
        Fraction : onset
        Fraction : offset
        Ottavation : ottavation
    }

    class Measure {
        Staff : staff
        Fraction : onset
    }

    class Voice {
        Part : part
        int : id
    }

    class Tuplet {
        Fraction : onset
        int : normal_count
        int : actual_count
        NoteType : normal_type
        NoteType : actual_type
        int : normal_dots
        int : actual_dots
    }

    class Element {
        Site : site
        NoteType : note_type
        int : dots
    }

    class ChordRest {
        Event : event
        BeamGroup : beam_group
    }

    class Chord {
        Stem : stem
    }

    class Rest {
        Fraction : nominal_duration
    }

    class GraceChord {
        Chord : chord
        int : index
        NoteType : note_type
        int : dots
        Stem : stem
        BeamGroup : beam_group
    }

    class Note {
        NoteName : note_name
        int : octave
        int : pitch
        Accidental : accidental
    }

    class BeamGroup {
        Voice : voice
    }

    class Site {
    }

    Score "1" --> "*" Part
    Part "id" --> "*" Staff
    Part "id" --> "*" Voice
    Staff "onset" --> Event
    Staff "onset" --> Clef
    Staff "onset" --> KeySignature
    Staff "onset" --> TimeSignature
    Staff "onset" --> OctaveShift
    Staff "onset" --> Measure
    Voice "onset" --> BeamGroup
    Site <|-- Voice
    Site <|-- Tuplet
    Event "voice" --> "*" ChordRest
    BeamGroup "*" o-- "*" ChordRest
    BeamGroup "*" o-- "*" GraceChord
    Element <|-- Tuplet
    Voice "onset" --> Element
    Tuplet "onset" --> Element
    Element <|-- ChordRest
    ChordRest <|-- Chord
    ChordRest <|-- Rest
    Chord "*" --> "*" Note
    Note "2" o-- Note
    Chord "*" --> "*" GraceChord
    GraceChord "*" --> "*" Note
```


Installation
=======================

To use this package in your project, clone the repository, navigate into its root directory and install the package into your Python environment:
```bash
cd MusicModelPython
pip install .
```
After that, all classes will be accessible within the `music_model` package namespace.