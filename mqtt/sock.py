import socket
from mqtt import messages
import logging


class Sock:
    def __init__(self, host: str, port: int):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_IP)
        self.sock.settimeout(2)
        self.adr = socket.getaddrinfo(host, port)[0][-1]
        self.printer = True

    def open(self):
        self.sock.connect(self.adr)

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


class ControlPacketReader:

    def __init__(self, input: bytearray):
        assert len(input)
        self.bytes_read = 0
        self.raw = bytearray()
        buffer = bytearray(input)
        buffer.reverse()
        self.fh = self._consumeFixedHeader(buffer)
        self.body = bytearray([self.pop(buffer) for i in range(self.fh.remainingLength)])

    def pop(self, buffer):
        byte = buffer.pop()
        self.bytes_read += 1
        self.raw.append(byte)
        return byte

    def _consumeFixedHeader(self, buffer):
        byte0 = self.pop(buffer)
        return messages.FixedHeader(type =self._get_type(byte0),
                                    flag0=self._get_flag(byte0, 0),
                                    flag1=self._get_flag(byte0, 1),
                                    flag2=self._get_flag(byte0, 2),
                                    flag3=self._get_flag(byte0, 3),
                                    remainingLength=self._consume_RemainingLength(buffer))

    @staticmethod
    def _get_type(byte0) -> messages.FixedHeader.ControlPackettype:
        msg_type = byte0 >> 4
        return messages.FixedHeader.ControlPackettype(msg_type)

    @staticmethod
    def _get_flag(byte0, flagID):
        mask = 1 << flagID
        return byte0 & mask >> flagID

    def _consume_RemainingLength(self, buffer):
        multiplier = 1
        value = 0

        while True:
            encodedByte = self.pop(buffer)

            value += (encodedByte & 127) * multiplier
            multiplier *= 128
            if multiplier > 128 * 128 * 128:
                raise Exception('Malformed Remaining Length')

            if (encodedByte & 128) == 0:
                break
        return value

    def __repr__(self):
        return messages.msg2str(self.fh.type.name,
                                self.fh.flag3,
                                self.fh.flag2,
                                self.fh.flag1,
                                self.fh.flag0,
                                bytes(self.body))


class MsgSock(Sock):

    @staticmethod
    def _print(msg): #, incommig):
        # if incommig:
        #     print('<-')
        # else:
        #     print('->')
        [print(format(i, '2d'),
               format(msg[i], '#010b'),
               format(msg[i], '#04x'),
               format(msg[i], '5d'),
               chr(msg[i])) for i in range(len(msg))]
        # short
        # print('<-', [format(c, '#010b') for c in ret], '|', [format(c, '#4x') for c in ret])

    def write(self, msg):
        assert isinstance(msg, messages.ControlPacket)
        print('->', msg)
        msg = msg.toBytes()
        self._print(msg)
        return super(MsgSock, self).write(msg)

    def read(self, num) -> ControlPacketReader:
        ret = super(MsgSock, self).read(num)
        if not ret:
            return None

        try:
            ret = bytearray(ret)
            msg = ControlPacketReader(ret)
            print('<-', msg)
            self._print(msg.raw)
            return msg
        except Exception as e:
            logging.exception(e)
            logging.error(ret)
            return None
