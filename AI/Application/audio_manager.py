import pygame
import os
from threading import Thread

class AudioManager:
    def __init__(self):
        pygame.init()
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
        self.audio_files = {}
        self.load_audio_files()

    def load_audio_files(self):
        categories = ['shapes', 'colors', 'system']
        for cat in categories:
            path = f"audio/{cat}/"
            if os.path.exists(path):
                for file in os.listdir(path):
                    if file.endswith('.mp3'):
                        name = file[:-4]
                        self.audio_files[name] = pygame.mixer.Sound(os.path.join(path, file))

    def play(self, name):
        if name in self.audio_files:
            Thread(target=self._play_thread, args=(name,)).start()

    def _play_thread(self, name):
        sound = self.audio_files[name]
        sound.play()
        while pygame.mixer.get_busy():
            pass
