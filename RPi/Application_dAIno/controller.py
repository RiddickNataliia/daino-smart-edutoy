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
        self.servo_pwm = GPIO.PWM(self.servo_pin, 50)
        self.servo_pwm.start(0)

        # LED Strip Setup
        self.led_strip = WS2812SpiDriver(spi_bus=1, spi_device=0, led_count=8).get_strip()
        time.sleep(0.1)
        self.set_led(Color(255, 255, 255))
        time.sleep(0.05)
        self.set_led(Color(255, 255, 255))
        self._move_servo_safe(6)
        time.sleep(0.5)

    def _move_servo_safe(self, duty_cycle):
        self.servo_pwm.ChangeDutyCycle(duty_cycle)
        time.sleep(0.5)
        self.servo_pwm.ChangeDutyCycle(0)

    def set_led(self, color):
        self.led_strip.set_all_pixels(color)
        self.led_strip.show()

    def mouth_action(self, close_time=1):
        self._move_servo_safe(8)
        time.sleep(close_time)
        self._move_servo_safe(6)

    def handle_command(self, data):
        action = data.get('action')
        payload = data.get('payload')

        if action == protocol.LEARNING_SHAPE:
            try:
                duration = float(payload.get('duration', 2.0))
                print(f"Learning shape action received: duration={duration}")
                self.set_led(Color(0, 255, 0))
                time.sleep(duration)
                self.mouth_action()
                self.set_led(Color(255, 255, 255))
            except Exception as e:
                print(f"Error handling LEARNING_SHAPE: {e}")

        elif action == protocol.SET_LED_COLOR:
            color = payload.get("color", "white")
            print(f"Set LED color command received: {color}")
            if color == "red":
                self.set_led(Color(255, 0, 0))
            elif color == "green":
                self.set_led(Color(0, 255, 0))
            elif color == "soft_yellow":
                self.set_led(Color(255, 180, 50))
            else:
                self.set_led(Color(255, 255, 255))

    def cleanup(self):
        print("Cleaning up GPIO and shutting down...")
        try:
            # Move servo first while PWM is still active
            self._move_servo_safe(6)
        except Exception as e:
            print(f"Error moving servo: {e}")
        
        try:
            # Stop PWM and clear reference
            if hasattr(self, 'servo_pwm') and self.servo_pwm is not None:
                self.servo_pwm.stop()
                self.servo_pwm = None
        except Exception as e:
            print(f"Error stopping PWM: {e}")
        
        try:
            # Turn off LEDs
            self.set_led(Color(0, 0, 0))
        except Exception as e:
            print(f"Error setting LEDs off: {e}")
        
        try:
            # Clean up GPIO last
            GPIO.cleanup()
        except Exception as e:
            print(f"Error during GPIO cleanup: {e}")

def run_server():
    dino = DinoController()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
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
        print("\nShutting down gracefully...")
    finally:
        dino.cleanup()
        server.close()
        print("Server closed")

if __name__ == "__main__":
    run_server()
