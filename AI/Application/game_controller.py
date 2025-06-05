# game_controller.py
import random

class GameController:
    def __init__(self, audio, led, servo, ai, cam):
        self.audio = audio
        self.led = led
        self.servo = servo
        self.ai = ai
        self.cam = cam

    def start_game(self, mode):
        self.audio.play_start_prompt(mode)
        while True:
            target = self.request_next(mode)
            self.audio.play_request(mode, target)
            frame = self.cam.capture_frame()
            detected = self.ai.detect(frame, mode)
            self.handle_input(mode, target, detected)

    def request_next(self, mode):
        return random.choice(["red", "green", "blue"] if mode == "color" else ["circle", "square", "triangle"])

    def handle_input(self, mode, target, detected):
        if detected == target:
            self.audio.play_success()
            self.led.set_color("green")
            self.servo.activate()
        else:
            self.audio.play_rejection(detected)
            self.led.set_color("red")