from mqtt.messages import *


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
