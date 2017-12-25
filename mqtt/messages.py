from enum import IntEnum
from struct import pack


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
        PINGREG = 12,
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
        byte1 = self.type.value << 4 | self.flag3 << 3 | self.flag2 << 2 | self.flag1 << 1 | self.flag0 << 0
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


class PacketIdentifier:
    def __init__(self, id):
        self.id = id

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
            payload += str_2_byte_lenprefix(i)
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
        QOS = int_2_byte(qos)
        fh = FixedHeader(FixedHeader.ControlPackettype.PUBLISH, dup_flag, QOS[0], QOS[1], retain)

        vh = str_2_byte_lenprefix(topic)

        if qos != 0:
            #TODO: PacketIdentifier
            raise Exception('not implemented')

        payload = str_2_bytes(value)

        return ControlPacket(fh, bytes(vh), bytes(payload))


def PublishAckBuilder(PacketIdentifier:int):
    fh = FixedHeader(FixedHeader.ControlPackettype.PUBACK, 0,0,0,0)

    vh = [int_2_byte(PacketIdentifier)]

    return ControlPacket(fh, bytes(vh))
