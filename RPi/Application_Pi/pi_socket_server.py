import socket
import RPi.GPIO as GPIO
import time

# GPIO setup
LED_PIN = 18
SERVO_PIN = 17

GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.setup(SERVO_PIN, GPIO.OUT)

servo = GPIO.PWM(SERVO_PIN, 50)
servo.start(0)

def activate_servo():
    servo.ChangeDutyCycle(7.5)
    time.sleep(0.5)
    servo.ChangeDutyCycle(2.5)
    time.sleep(0.5)
    servo.ChangeDutyCycle(0)

def handle_command(command):
    print(f"Received: {command}")
    if "LED red" in command:
        GPIO.output(LED_PIN, GPIO.HIGH)  # Red mock (depends on actual setup)
    elif "LED green" in command:
        GPIO.output(LED_PIN, GPIO.LOW)
    elif "SERVO" in command:
        activate_servo()

# Socket server
HOST = "0.0.0.0"
PORT = 5000
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((HOST, PORT))
sock.listen(1)
print("Pi is listening for commands...")

conn, addr = sock.accept()
print(f"Connection from {addr}")

try:
    while True:
        data = conn.recv(1024).decode()
        if not data:
            break
        handle_command(data)
except KeyboardInterrupt:
    pass
finally:
    servo.stop()
    GPIO.cleanup()
    conn.close()
