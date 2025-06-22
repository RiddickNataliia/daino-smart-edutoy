import socket
import protocol
from shape_learning_game import LearningShapesMode
from shape_testing_game import ShapeTestingMode
from color_learning_game import LearningColorsMode
from color_testing_game import ColorTestingMode
from bedtime_mode import BedtimeMode
import time
import sys

class GameManager:
    def __init__(self, pi_ip='192.168.168.167'):
        self.pi_ip = pi_ip
        self.pi_socket = None
        self._connect_to_pi()

    def _set_keepalive(self, sock):
        """Enable socket keep-alive to prevent idle disconnects"""
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        # Windows-specific keepalive parameters
        if hasattr(socket, 'SIO_KEEPALIVE_VALS'):
            sock.ioctl(socket.SIO_KEEPALIVE_VALS, (1, 60000, 30000))

    def _connect_to_pi(self):
        max_retries = 10  # Increased retry count
        for attempt in range(max_retries):
            try:
                self.pi_socket = socket.socket()
                self.pi_socket.settimeout(10.0)  # Longer timeout
                print(f"Attempting to connect to {self.pi_ip} (attempt {attempt+1}/{max_retries})")
                self.pi_socket.connect((self.pi_ip, 8888))
                self._set_keepalive(self.pi_socket)
                self.pi_socket.settimeout(None)
                print(f"Connected to Pi at {self.pi_ip}")
                return
            except (ConnectionRefusedError, socket.timeout) as e:
                print(f"Connection attempt failed: {e}")
                time.sleep(2)
            except OSError as e:
                print(f"Network error: {e}")
                time.sleep(2)
        print("Critical: Could not connect to Pi after multiple attempts")
        print("Please check:")
        print(f"1. Pi is powered on and has IP: {self.pi_ip}")
        print("2. Pi server is running (execute 'python dino_controller.py')")
        print("3. Network connection is stable")
        raise ConnectionError("Could not connect to Pi")

    def _reconnect(self):
        """Close existing connection and reconnect"""
        if self.pi_socket:
            try:
                self.pi_socket.close()
            except:
                pass
        self._connect_to_pi()

    def send_to_pi(self, shape, duration, correct=True, color=None):
        try:
            if color:
                cmd = protocol.create_command(protocol.SET_LED_COLOR, {"color": color})
            elif correct:
                cmd = protocol.create_command(protocol.LEARNING_SHAPE, {"shape": shape, "duration": duration})
            else:
                cmd = protocol.create_command(protocol.SET_LED_COLOR, {"color": "red"})
                
            # Check socket health before sending
            if not self.pi_socket or self.pi_socket.fileno() == -1:
                print("Socket invalid, reconnecting...")
                self._reconnect()
                
            self.pi_socket.sendall(cmd)
            
        except (ConnectionResetError, BrokenPipeError, socket.timeout, OSError) as e:
            print(f"Connection error: {e}. Reconnecting...")
            try:
                self._reconnect()
                self.pi_socket.sendall(cmd)  # Retry after reconnect
            except Exception as e2:
                print(f"Resend failed: {e2}")
        except Exception as e:
            print(f"Error sending to Pi: {e}")

    def run_mode(self, mode_name):
        if mode_name == "testing":
            tester = ShapeTestingMode()
        elif mode_name == "learning":
            tester = LearningShapesMode()
        elif mode_name == "color_learning":
            tester = LearningColorsMode()
        elif mode_name == "color_testing":
            tester = ColorTestingMode()
        elif mode_name == "bedtime":
            tester = BedtimeMode()
            # Prompt for duration
            while True:
                try:
                    minutes = int(input("Enter bedtime duration (10-120 minutes): "))
                    if 10 <= minutes <= 120:
                        tester.set_duration(minutes)
                        break
                    else:
                        print("Please enter a value between 10 and 120.")
                except ValueError:
                    print("Invalid input. Please enter a number.")
        else:
            print("Unknown mode.")
            return

        tester.send_to_pi = self.send_to_pi
        tester.pi_socket = self.pi_socket
        try:
            tester.run()
        except KeyboardInterrupt:
            print("\nGame mode interrupted. Returning to menu...")
            if hasattr(tester, 'cleanup'):
                tester.cleanup()
            raise

    def cleanup(self):
        """Close network connection to Pi"""
        if self.pi_socket:
            try:
                self.pi_socket.close()
                print("Closed connection to Pi")
            except Exception as e:
                print(f"Error closing socket: {e}")
            finally:
                self.pi_socket = None

if __name__ == "__main__":
    manager = GameManager()
    try:
        while True:
            print("\nEnter the number of the mode you choose:")
            print("1. Learn Shapes")
            print("2. Test Shapes")
            print("3. Learn Colors")
            print("4. Test Colors")
            print("5. Bedtime Mode")
            print("6. Exit")
            choice = input("Your choice: ").strip()

            if choice == "1":
                manager.run_mode("learning")
            elif choice == "2":
                manager.run_mode("testing")
            elif choice == "3":
                manager.run_mode("color_learning")
            elif choice == "4":
                manager.run_mode("color_testing")
            elif choice == "5":
                manager.run_mode("bedtime")
            elif choice == "6":
                print("Exiting program...")
                break
            else:
                print("Invalid choice. Please enter 1-6.")
    except KeyboardInterrupt:
        print("\n\nProgram interrupted by user. Exiting gracefully...")
    finally:
        manager.cleanup()
        sys.exit(0)
