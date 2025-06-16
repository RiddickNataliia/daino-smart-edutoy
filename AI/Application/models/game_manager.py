from modes.learn_shapes import LearnShapesMode
from modes.test_shapes import TestShapesMode
from modes.learn_colors import LearnColorsMode
from modes.test_colors import TestColorsMode
from stats import StatsManager

class GameManager:
    def __init__(self):
        self.current_mode = None
        self.stats = StatsManager()
        self.modes = {
            "Learn Shapes": LearnShapesMode,
            "Test Shapes": TestShapesMode,
            "Learn Colors": LearnColorsMode,
            "Test Colors": TestColorsMode
        }

    def switch_mode(self, mode_name):
        if self.current_mode:
            self.current_mode.end()
        mode_class = self.modes.get(mode_name)
        if mode_class:
            self.current_mode = mode_class(self.stats)
            self.current_mode.start()
