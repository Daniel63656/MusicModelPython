import os
from music_model import *
from music_model.conversion import *
resources_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")

def test_songs():
    for file in os.listdir(resources_dir):
        filepath = os.path.join(resources_dir, file)
        score = import_xml(filepath)
        show_xml(score)