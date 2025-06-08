import os
import random
import pygame

class AudioPlayer:
    def __init__(self):
        pygame.mixer.init()
        volume = pygame.mixer.music.set_volume(0.7)

    def play_file(self, path):
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            continue

    def play_start_prompt(self, mode):
        self.play_file(f"audio/start/start_{mode}_game.mp3")

    def play_request(self, type, value):
        self.play_file(f"audio/requests/request_{value}.mp3")

    def play_rejection(self, detected):
        self.play_file("audio/rejections/reject_general.mp3")
        self.play_file(f"audio/names/{detected}.mp3")

    def play_success(self):
        self.play_file(random.choice([
            "audio/success/good_job.mp3",
            "audio/success/well_done.mp3"
        ]))