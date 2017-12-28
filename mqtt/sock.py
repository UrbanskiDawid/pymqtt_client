import socket


class Sock:
    def __init__(self, host: str, port: int):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_IP)
        self.sock.settimeout(2)
        self.adr = socket.getaddrinfo(host, port)[0][-1]
        self.printer = True

    def open(self):
        print('connecting')
        self.sock.connect(self.adr)
        print('connected')

    def write(self, msg):
        self.sock.send(msg)

    def read(self, num):
        try:
            return self.sock.recv(num)
        except socket.timeout:
            return None

    def close(self):
        self.sock.close()
        self.sock = None
