import socket
import time

class ConnectionError(Exception):
    """Custom exception for connection-related issues."""
    pass

class RaspiClient:
    def __init__(self, ip='192.168.168.167', port=5000, timeout=5):
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self.sock = None
        self.connect()

    def connect(self, retries=3, retry_delay=2):
        """Establish connection with retry logic."""
        for attempt in range(retries):
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.settimeout(self.timeout)
                self.sock.connect((self.ip, self.port))
                print(f"Connected to {self.ip}:{self.port}")
                return
            except (socket.error, socket.timeout) as e:
                if attempt < retries - 1:
                    print(f"Connection failed (attempt {attempt+1}/{retries}), retrying...")
                    time.sleep(retry_delay)
                else:
                    raise ConnectionError(f"Failed to connect after {retries} attempts: {e}")

    def send(self, command):
        """Send command with auto-reconnect on failure."""
        try:
            if not self.is_connected():
                print("Connection lost, reconnecting...")
                self.connect()
            
            self.sock.sendall(command.encode())
        except (socket.error, BrokenPipeError, socket.timeout) as e:
            print(f"Send failed: {e}")
            self.close()
            raise ConnectionError("Could not send command") from e

    def is_connected(self):
        """Check if socket is still connected."""
        try:
            # Simple check using socket options
            return self.sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR) == 0
        except (socket.error, AttributeError):
            return False

    def close(self):
        """Close connection gracefully."""
        if self.sock:
            try:
                self.sock.close()
            except socket.error:
                pass
            finally:
                self.sock = None
        print("Connection closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

# Usage Example:
if __name__ == "__main__":
    try:
        with RaspiClient() as client:
            # Keep connection open for multiple commands
            client.send("LED_WHITE")
            time.sleep(1)
            client.send("LED_GREEN")
            time.sleep(1)
            client.send("SERVO_OPEN")
            
    except ConnectionError as e:
        print(f"Critical error: {e}")

