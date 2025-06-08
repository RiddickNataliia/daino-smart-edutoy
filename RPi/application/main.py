import socket
import threading
import hardware_control  

def handle_client(conn, addr):
    print(f"[CONNECTED] {addr}")
    try:
        while True:
            data = conn.recv(1024).decode().strip()
            if not data:
                break
            print(f"[COMMAND] {data}")

            if data == "LED_GREEN":
                print("Turning LED green")
                hardware_control.set_led_color("green")
            elif data == "LED_RED":
                print("Turning LED red")
                hardware_control.set_led_color("red")
            elif data == "LED_WHITE":
                print("Turning LED white")
                hardware_control.set_led_color("white")
            elif data == "SERVO_OPEN":
                print("Opening jaw")
                hardware_control.move_servo("open")
            elif data == "SERVO_CLOSE":
                print("Closing jaw")
                hardware_control.move_servo("close")
            else:
                print("Unknown command")

    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        conn.close()
        print(f"[DISCONNECTED] {addr}")
        hardware_control.set_led_color("white") 
def start_server(ip='0.0.0.0', port=5000):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((ip, port))
    server.listen(1)
    print(f"[LISTENING] on {ip}:{port}")

    try:
        while True:
            conn, addr = server.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.start()
    finally:
        hardware_control.cleanup()

if __name__ == "__main__":
    start_server()
