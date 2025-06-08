from rpi5_ws2812.ws2812 import Color, WS2812SpiDriver
import time
from RPi import GPIO

servo_pin = 5

GPIO.setmode(GPIO.BCM)
GPIO.setup(servo_pin, GPIO.OUT)

servo_pwm = GPIO.PWM(servo_pin, 50)
servo_pwm.start(0)

# Initialize the WS2812 strip with 8 LEDs and SPI bus 1, CE0
strip = WS2812SpiDriver(spi_bus=1, spi_device=0, led_count=8).get_strip()

def set_led_color(color):
    if color == "white":
        strip.set_all_pixels(Color(255, 255, 255))
    elif color == "green":
        strip.set_all_pixels(Color(0, 255, 0))
    elif color == "red":
        strip.set_all_pixels(Color(255, 0, 0))
    strip.show()

def move_servo(position):
    if position == "open":
        servo_pwm.ChangeDutyCycle(8)
    elif position == "close":
        servo_pwm.ChangeDutyCycle(6)

def cleanup():
    servo_pwm.stop()
    GPIO.cleanup()

# Set default LED color to white on startup
set_led_color("white")
