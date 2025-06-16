# pi_controller.py
from rpi5_ws2812.ws2812 import Color, WS2812SpiDriver
from RPi import GPIO
import socket
import time
import protocol
import json

class DinoController:
    def __init__(self):
        # Servo Setup
        self.servo_pin = 5
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.servo_pin, GPIO.OUT)
        self.servo_pwm = GPIO.PWM(self.servo_pin, 50)  # 50Hz frequency
        self.servo_pwm.start(6)  # Start in open position (duty cycle 6%)
        
        # LED Strip Setup
        self.led_strip = WS2812SpiDriver(spi_bus=1, spi_device=0, led_count=8).get_strip()
        self.set_led(Color(255, 255, 255))  # Initial white
        
    def set_led(self, color):
        self.led_strip.set_all_pixels(color)
        self.led_strip.show()
    
    def mouth_action(self, close_time=1):
        """Close and open mouth once"""
        self.servo_pwm.ChangeDutyCycle(8.5)  # Close
        time.sleep(close_time)
        self.servo_pwm.ChangeDutyCycle(6)  # Open
    
    def handle_command(self, data):
        action = data.get('action')
        payload = data.get('payload')
        
        if action == protocol.LEARNING_SHAPE:
            try:
                duration = float(payload.get('duration', 2.0))
                self.set_led(Color(0, 255, 0))  # Green
                time.sleep(duration)  # Wait for audio
                self.mouth_action()
                self.set_led(Color(255, 255, 255))  # White
            except KeyError:
                print("Invalid payload format")

    def cleanup(self):
        self.servo_pwm.stop()
        GPIO.cleanup()
        self.set_led(Color(0, 0, 0))
        self.led_strip.close()

def run_server():
    dino = DinoController()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 8888))
    server.listen(1)
    print("Server started. Waiting for connections...")
    
    try:
        while True:
            conn, addr = server.accept()
            print(f"Connected to {addr}")
            try:
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    try:
                        decoded = json.loads(data.decode())
                        dino.handle_command(decoded)
                    except json.JSONDecodeError:
                        print("Invalid JSON received")
            except ConnectionResetError:
                print("Client disconnected abruptly")
            finally:
                conn.close()
                print("Connection closed")
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        dino.cleanup()
        server.close()

if __name__ == "__main__":
    run_server()
