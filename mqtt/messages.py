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


def ConnectMsgBuilder(clientID:str,
                      protocoll_level=MQTTv311,
                      user="",
                      password="",
                      willRetain= False,
                      qos=0,
                      cleanSession=True,
                      keepAlive=10,
                      ):
    fh = FixedHeader(FixedHeader.ControlPackettype.CONNECT, 0, 0, 0, 0)


    ## VARIABLE HEADER ##
    protocol_name = str_2_byte_lenprefix("MQTT")

    connect_flag = 0
    if user:
        connect_flag |= 1 << 7  # userName
    if password:
        connect_flag |= 1 << 6  # password
    if willRetain:
        connect_flag |= 1 << 5  # will Retain
    assert qos <= 3 or qos >= 0
    connect_flag |= qos << 3
    connect_flag |= 0 << 2  # will flag
    if cleanSession:
        connect_flag |= 1 << 1  # clean session
    connect_flag |= 0 << 0  # reserved

    keep_alive = int_2_byte(keepAlive)

    vh = protocol_name + \
        [protocoll_level] + \
        [connect_flag] + \
         keep_alive
    assert len(vh) == 10  # 10bytes
    ##--##

    ## PAYLOAD ##
    # Client Identifier
    # Will Topic,
    # Will Message,
    # User Name,
    # Password
    payload = []
    for i in [clientID, user, password]:
        if i:
            payload.extend(str_2_byte_lenprefix(i))
    ## -- ##

    return ControlPacket(fh, bytes(vh), bytes(payload))


def DisconnectMsgBuilder():
    fh = FixedHeader(FixedHeader.ControlPackettype.DISCONNECT, 0, 0, 0, 0)
    return ControlPacket(fh)


def ConnectACKMsgBuilder(sessionPresentFlag=True,
                         connectReturnCode=0):
        fh = FixedHeader(FixedHeader.ControlPackettype.CONNACK, 0, 0, 0, 0,
                         remainingLength=[2])

        connectAcknowledgeFlags = 0
        connectAcknowledgeFlags |= sessionPresentFlag << 0

        vh=[connectAcknowledgeFlags,
            connectReturnCode]

        return ControlPacket(fh, bytes(vh))


def PublishMsgBuilder(topic,
                      value: str,
                      dup_flag=False,
                      qos=0,
                      retain=True):
        QOSbit1 = qos & 0b10 >> 1
        QOSbit0 = qos & 0b01
        fh = FixedHeader(FixedHeader.ControlPackettype.PUBLISH, dup_flag, QOSbit0, QOSbit1, retain)
        vh = str_2_byte_lenprefix(topic)

        if qos != 0:
            #TODO: PacketIdentifier
            raise Exception('not implemented')

        payload = str_2_bytes(value)

        return ControlPacket(fh, bytes(vh), bytes(payload))


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
        return FixedHeader(type =self._get_type(byte0),
                           flag0=self._get_flag(byte0, 0),
                           flag1=self._get_flag(byte0, 1),
                           flag2=self._get_flag(byte0, 2),
                           flag3=self._get_flag(byte0, 3),
                           remainingLength=self._consume_RemainingLength(buffer))

    @staticmethod
    def _get_type(byte0) -> FixedHeader.ControlPackettype:
        msg_type = byte0 >> 4
        return FixedHeader.ControlPackettype(msg_type)

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
        return msg2str(self.fh.type.name,
                       self.fh.flag3,
                       self.fh.flag2,
                       self.fh.flag1,
                       self.fh.flag0,
                       bytes(self.body))


def PublishAckBuilder(PacketIdentifier:int):
    fh = FixedHeader(FixedHeader.ControlPackettype.PUBACK, 0,0,0,0)

    vh = [int_2_byte(PacketIdentifier)]

    return ControlPacket(fh, bytes(vh))


def SubscribeBuilder(packetId: PacketIdentifier,
                     topics: list(),
                     qos=1):
    assert isinstance(packetId, PacketIdentifier)
    fh = FixedHeader(FixedHeader.ControlPackettype.SUBSCRIBE, 0,1,0,0)
    vh = packetId.toBytes()
    payload = []
    assert isinstance(topics, list)
    for topic in topics:
        payload.extend(str_2_byte_lenprefix(topic))
        payload.extend(qos.to_bytes(length=1, byteorder='big'))

    return ControlPacket(fh, bytes(vh), bytes(payload))


#0x00 - Success - Maximum QoS 0
#0x01 - Success - Maximum QoS 1
#0x02 - Success - Maximum QoS 2
#0x80 - Failure
def SubscribeAckBuilder(packetId: PacketIdentifier, ret_codes:list()):

    fh = FixedHeader(FixedHeader.ControlPackettype.SUBACK, 0,0,0,0)
    vh = packetId.toBytes()
    payload = []
    for code in ret_codes:
        payload.extend(code.to_bytes(length=1, byteorder='big'))
    return ControlPacket(fh, bytes(vh), bytes(payload))


def UnSubscribeBuilder(packetId: PacketIdentifier,
                       topics: list()):

    fh = FixedHeader(FixedHeader.ControlPackettype.UNSUBSCRIBE, 0,1,0,0)
    vh = packetId.toBytes()
    payload = []
    for topic in topics:
        payload.extend(str_2_byte_lenprefix(topic))
    return ControlPacket(fh, bytes(vh), bytes(payload))


def UnSubscribeAckBuilder(packetId: PacketIdentifier):
    fh = FixedHeader(FixedHeader.ControlPackettype.UNSUBACK, 0,0,0,0)
    vh = packetId.toBytes()
    return ControlPacket(fh, bytes(vh))


def PingReqBuilder():
    fh = FixedHeader(FixedHeader.ControlPackettype.PINGREQ, 0, 0, 0, 0)
    return ControlPacket(fh)


def PingResBuilder():
    fh = FixedHeader(FixedHeader.ControlPackettype.PINGRES, 0, 0, 0, 0)
    return ControlPacket(fh)
