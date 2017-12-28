from mqtt import messages
from mqtt import messages_builders as builders
from mqtt import sock


class Client:
    def __init__(self, host, port):
        self.sock = sock.MsgSock(host, port)

    def wait4msg(self, msg):
        i = 4
        while i > 0:
            i -= 1
            ret = self.sock.read(255)
            if not ret:
                break

            if ret.fh.type == msg.fixedHeader.type:
                assert ret.raw == msg.toBytes(), 'unexpected msg body expected: ({}) vs {}'.format(msg.toBytes(), ret.raw)
                return
            else:
                self.on_message(ret)
        assert False, 'no message'

    def on_message(self, ret: sock.ControlPacketReader):
        # TODO: REACT
        print(ret.fh.type, ret.body)

    def connect(self, key, user, client_id):
        self.sock.open()

        msg = builders.ConnectMsgBuilder(clientID=client_id,
                                         user=user,
                                         password=key)
        self.sock.write(msg)
        self.wait4msg(builders.ConnectACKMsgBuilder(sessionPresentFlag=False))

    def disconnect(self):
        msg = builders.DisconnectMsgBuilder()
        self.sock.write(msg)
        self.sock.close()

    def publish(self, topic, value):
        msg = builders.PublishMsgBuilder(topic=topic, value=value)
        self.sock.write(msg)

    def subscribe(self, topic, qos=1):
        packetId = messages.PacketIdentifier()
        msg = builders.SubscribeBuilder(packetId=packetId,
                                        topics=[topic],
                                        qos=qos)
        self.sock.write(msg)
        self.wait4msg(builders.SubscribeAckBuilder(packetId, [qos]))

    def unsubscribe(self, topic):
        packetId = messages.PacketIdentifier()
        msg = builders.UnSubscribeBuilder(packetId=packetId,
                                          topics=[topic])
        self.sock.write(msg)
        self.wait4msg(builders.UnSubscribeAckBuilder(packetId))

    def ping(self):
        msg = builders.PingReqBuilder()
        self.sock.write(msg)
        self.wait4msg(builders.PingResBuilder())
