## MusicModel

The Geometry Package is a Python library designed to compute geometric properties and provide access to topological information of various geometric primitives used in computational grids and simulations. The project features following geometric primitives which are all derived from an abstract `Geometry` class:
- Segment
- Triangle
- Quadrilateral
- Tetrahedron

Additionally, the package includes a `Point` class, which inherits from Python's tuple and serves as a fundamental building block for defining positions in Cartesian coordinates.
The `Face` interface provides access to the boundaries and properties of the defined primitives, while also extending the `Geometry` interface. All available interfaces and classes, as well as their methods and relations are illustrated in this class diagram:

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
cd geometry
pip install .
```
After that, all classes will be accessible within the `geometry` package namespace.

Example Usage
=======================

```python
from geometry import Point, Triangle

# create a triangle in 2D domain and query its area:
p1 = Point(0.0, 0.0)
p2 = Point(4.0, 0.0)
p3 = Point(2.0, 3.0)
triangle = Triangle(p1, p2, p3)
area = triangle.get_volume()

# print outer normal vector from all the faces of the triangle
for face in triangle.get_faces():
    print(face.get_outer_normal_vector())
```
