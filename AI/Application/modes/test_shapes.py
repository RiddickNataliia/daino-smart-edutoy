from .base_mode import BaseMode
from raspi_interface import RaspiInterface
from audio_manager import AudioManager
import time

class TestShapesMode(BaseMode):
    def __init__(self, stats_manager):
        super().__init__(stats_manager)
        self.raspi = RaspiInterface()
        self.audio = AudioManager()
        self.shapes = ['triangle', 'square', 'circle', 'pentagon', 'star']
        self.shape_counts = {shape: 5 for shape in self.shapes}
        self.correct_streak = 0
        self.total_correct = 0
        self.total_incorrect = 0
        self.running = False

    def start(self):
        self.running = True
        self.raspi.set_led('white')
        self.audio.play('request_first_shape')
        self.next_shape()

    def next_shape(self):
        # Logic to select and request the next shape
        pass

    def handle_shape_inserted(self, shape, multiple=False):
        if multiple:
            self.raspi.set_led('red')
            self.audio.play('rejection_multiple')
            return

        if shape == self.expected_shape and self.shape_counts[shape] > 0:
            self.raspi.set_led('green')
            self.audio.play('swallow')
            self.raspi.move_servo('close')
            self.shape_counts[shape] -= 1
            self.correct_streak += 1
            self.total_correct += 1
            if self.correct_streak in [3, 5, 10]:
                self.raspi.rainbow_led(5)
                self.audio.play(f'streak_{self.correct_streak}')
            if all(count == 0 for count in self.shape_counts.values()):
                self.audio.play('game_over')
                self.raspi.rainbow_led(10)
                self.end()
            else:
                self.next_shape()
        else:
            self.raspi.set_led('red')
            self.audio.play(f'named_{shape}')
            self.audio.play('remove_wrong')
            self.audio.play('request_again')
            self.correct_streak = 0
            self.total_incorrect += 1

    def end(self):
        self.running = False
        self.stats.record('Test Shapes', 'total_correct', self.total_correct)
        self.stats.record('Test Shapes', 'total_incorrect', self.total_incorrect)
        self.stats.record('Test Shapes', 'longest_streak', self.correct_streak)
