from game_controller import GameController
from ai_handler import AIHandler
from audio_player import AudioPlayer
from camera_handler import CameraHandler
from led_controller import LEDController
from servo_controller import ServoController
from raspi_client import RaspiClient

client = RaspiClient()

def main():
    audio = AudioPlayer()
    led = LEDController()
    servo = ServoController()
    ai = AIHandler()
    cam = CameraHandler()
    game = GameController(audio, led, servo, ai, cam)

    game.start_game("color")  # or "shape"

    client.send("LED green")
    client.send("SERVO")

if __name__ == "__main__":
    main()