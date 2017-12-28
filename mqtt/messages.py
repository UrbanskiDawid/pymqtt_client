from enum import IntEnum
from struct import pack
from random import randint

MQTTv311 = 4


def int_2_byte(value):
    ret = pack('>H', value)
    return [ret[0], ret[1]]


# TODO unicode support  [RFC3629]
def str_2_bytes(msg):
    return [ord(c) for c in msg]


def str_2_byte_lenprefix(msg: str):
    ret = []
    ret.extend(int_2_byte(len(msg)))
    ret.extend(str_2_bytes(msg))
    return ret


def msg2str(type_name,
            flag3,
            flag2,
            flag1,
            flag0,
            body):
    return "ControlPacket type:{} flags:[{} {} {} {}] body:{}".format(type_name,
                                                                      flag3,
                                                                      flag2,
                                                                      flag1,
                                                                      flag0,
                                                                      bytes(body))


class FixedHeader:
    class ControlPackettype(IntEnum):
        RESERVED = 0,
        CONNECT = 1,
        CONNACK = 2,
        PUBLISH = 3,
        PUBACK = 4,
        PUBREC = 5,
        PUBREL = 6,
        PUBCOMP = 7,
        SUBSCRIBE = 8,
        SUBACK = 9,
        UNSUBSCRIBE = 10,
        UNSUBACK = 11,
        PINGREQ = 12,
        PINGRES = 13,
        DISCONNECT = 14

    def __init__(self, type: ControlPackettype,
                 flag0, flag1, flag2, flag3,
                 remainingLength=[]):
        self.type = type
        self.flag0 = flag0
        self.flag1 = flag1
        self.flag2 = flag2
        self.flag3 = flag3
        self.remainingLength = remainingLength

    def toBytes(self)->bytes:
        byte1 = self.type.value << 4 |\
                self.flag3 << 3 |\
                self.flag2 << 2 | \
                self.flag1 << 1 | \
                self.flag0 << 0
        return pack('>B'+'B'*len(self.remainingLength), byte1, *self.remainingLength)

    def set_remainingLength(self, x):
        #The Remaining Length is the number of bytes remaining within the current packet,
        # including data in the variable header and the payload.
        #  The Remaining Length does not include the bytes used to encode the remaining Length
        self.remainingLength = []

        while True:
            encodedByte = x % 128
            x = x // 128
            if x > 0:
                encodedByte = encodedByte | 128
            self.remainingLength.append(encodedByte)
            if x <= 0:
                break


class ControlPacket:
    def __init__(self, fh: FixedHeader,
                       VariableHeader=bytes([]),
                       payload=bytes([])):
        self.fixedHeader = fh
        self.variableHeader = VariableHeader
        self.payload = payload

        length = len(VariableHeader)+len(payload)
        self.fixedHeader.set_remainingLength(length)

    def toBytes(self)->bytes:
        return self.fixedHeader.toBytes()+self.variableHeader+self.payload

    def __repr__(self):
        return msg2str(self.fixedHeader.type.name,
                       self.fixedHeader.flag3,
                       self.fixedHeader.flag2,
                       self.fixedHeader.flag1,
                       self.fixedHeader.flag0,
                       self.variableHeader+self.payload)


class PacketIdentifier:
    def __init__(self, identifier=None):
        if identifier is None:
            identifier = randint(0, 254)
        self.id = identifier

    def toBytes(self)->bytes:
        return pack('>H', self.id)
