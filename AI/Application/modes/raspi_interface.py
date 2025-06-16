import socket
import protocol
import time

class RaspiInterface:
    def __init__(self, pi_ip='192.168.168.167'):
        self.pi_ip = pi_ip
        self.pi_socket = None
        self.connect_to_pi()

    def connect_to_pi(self):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.pi_socket = socket.socket()
                self.pi_socket.connect((self.pi_ip, 8888))
                return
            except ConnectionRefusedError:
                time.sleep(2)
        raise ConnectionError("Could not connect to Pi")

    def set_led(self, color):
        cmd = protocol.create_command('SET_LED', {'color': color})
        self.pi_socket.sendall(cmd)

    def move_servo(self, position):
        cmd = protocol.create_command('MOVE_SERVO', {'position': position})
        self.pi_socket.sendall(cmd)

    def rainbow_led(self, duration):
        cmd = protocol.create_command('RAINBOW_LED', {'duration': duration})
        self.pi_socket.sendall(cmd)
