import socket

class RaspiClient:
    def __init__(self, ip='192.168.168.167', port=5000):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((ip, port))

    def send(self, command):
        self.sock.sendall(command.encode())

    def close(self):
        self.sock.close()
