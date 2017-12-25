import socket


def _print(msg, incommig):
    if incommig:
        print('<-')
    else:
        print('->')
    [print(format(i, '2d'),
           format(msg[i], '#010b'),
           format(msg[i], '#04x'),
           format(msg[i], '10d'),
           chr(msg[i])) for i in range(len(msg))]
    # short
    # print('<-', [format(c, '#010b') for c in ret], '|', [format(c, '#4x') for c in ret])


class Sock:
    def __init__(self, host: str, port: int):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_IP)
        self.sock.settimeout(30)
        self.adr = socket.getaddrinfo(host, port)[0][-1]

    def open(self):
        print('connecting')
        self.sock.connect(self.adr)
        print('connected')

    def write(self, msg):
        _print(msg, False)
        self.sock.send(msg)

    def read(self, num):
        ret = self.sock.recv(num)
        _print(ret, True)
        return ret

    def close(self):
        self.sock.close()
        self.sock = None
