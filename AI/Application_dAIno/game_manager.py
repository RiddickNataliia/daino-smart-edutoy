import socket
import protocol
from shape_learning_game import LearningShapesMode
from shape_testing_game import ShapeTestingMode
from color_learning_game import LearningColorsMode
from color_testing_game import ColorTestingMode
import time

class GameManager:
    def __init__(self, pi_ip='192.168.168.167'):
        self.pi_ip = pi_ip
        self.pi_socket = None
        self._connect_to_pi()

    def _connect_to_pi(self):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.pi_socket = socket.socket()
                self.pi_socket.connect((self.pi_ip, 8888))
                print(f"Connected to Pi at {self.pi_ip}")
                return
            except ConnectionRefusedError:
                print(f"Connection attempt {attempt+1} failed")
                time.sleep(2)
        raise ConnectionError("Could not connect to Pi")

    def send_to_pi(self, shape, duration, correct=True, color=None):
        try:
            if color:
                cmd = protocol.create_command(protocol.SET_LED_COLOR, {"color": color})
            elif correct:
                cmd = protocol.create_command(protocol.LEARNING_SHAPE, {"shape": shape, "duration": duration})
            else:
                cmd = protocol.create_command(protocol.SET_LED_COLOR, {"color": "red"})
            self.pi_socket.sendall(cmd)
        except (ConnectionResetError, BrokenPipeError):
            print("Reconnecting to Pi...")
            self._connect_to_pi()
            self.pi_socket.sendall(cmd)

    def run_mode(self, mode_name):
        if mode_name == "testing":
            tester = ShapeTestingMode()
        elif mode_name == "learning":
            tester = LearningShapesMode()
        elif mode_name == "color_learning":
            tester = LearningColorsMode()
        elif mode_name == "color_testing":
            tester = ColorTestingMode()
        else:
            print("Unknown mode.")
            return

        tester.send_to_pi = self.send_to_pi  # Injecting dependency
        tester.pi_socket = self.pi_socket
        tester.run()

if __name__ == "__main__":
    manager = GameManager()
    print("Enter the number of the mode you choose:")
    print("1. Learn Shapes")
    print("2. Test Shapes")
    print("3. Learn Colors")
    print("4. Test Colors")
    choice = input("Your choice: ").strip()

    if choice == "1":
        manager.run_mode("learning")
    elif choice == "2":
        manager.run_mode("testing")
    elif choice == "3":
        manager.run_mode("color_learning")
    elif choice == "4":
        manager.run_mode("color_testing")
    else:
        print("Invalid choice. Please enter 1, 2, 3, or 4.")
