import random
from os import listdir
from os.path import join
from constants import AUDIO_DIRS

def get_random_encouragement():
    encouragement_dir = AUDIO_DIRS["encouragement"]
    files = listdir(encouragement_dir)
    return join(encouragement_dir, random.choice(files))