from music_model import *


def embed_in_html(content: str) -> str:
    return f"""
    <!DOCTYPE html>
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
    </html>
    """


def parse_to_js(score: Score) -> str:
    result = """
    const { Factory, EasyScore, System } = Vex.Flow;

    const vf = new Factory({
    renderer: { elementId: 'output', width: 500, height: 200 },
    });
    const score = vf.EasyScore();
    const system = vf.System();

    system
    .addStave({
        voices: [
        score.voice(score.notes('C#5/q, B4, A4, G#4', { stem: 'up' })),
        score.voice(score.notes('C#4/h, C#4', { stem: 'down' })),
        ],
    })
    .addClef('treble')
    .addTimeSignature('4/4');

    vf.draw();
    """
    return result
