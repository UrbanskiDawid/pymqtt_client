from mqtt import messages
import logging
from mqtt import sock


class MsgSock(sock.Sock):

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

    def read(self, num) -> messages.ControlPacketReader:
        ret = super(MsgSock, self).read(num)
        if not ret:
            return None

        try:
            ret = bytearray(ret)
            msg = messages.ControlPacketReader(ret)
            print('<-', msg)
            self._print(msg.raw)
            return msg
        except Exception as e:
            logging.exception(e)
            logging.error(ret)
            return None


class Client:
    def __init__(self, host, port):
        self.sock = MsgSock(host, port)

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
                #TODO: REACT
                print(ret.fh.type)
        assert False, 'no message'

    def connect(self, key, user, client_id):
        self.sock.open()

        msg = messages.ConnectMsgBuilder(clientID=client_id,
                                         user=user,
                                         password=key)
        self.sock.write(msg)
        self.wait4msg(messages.ConnectACKMsgBuilder(sessionPresentFlag=False))

    def disconnect(self):
        msg = messages.DisconnectMsgBuilder()
        self.sock.write(msg)
        self.sock.close()

    def publish(self, topic, value):
        msg = messages.PublishMsgBuilder(topic=topic, value=value)
        self.sock.write(msg)

    def subscribe(self, topic, qos=0):
        packetId = messages.PacketIdentifier()
        msg = messages.SubscribeBuilder(packetId=packetId,
                                        topics=[topic],
                                        qos=qos)
        self.sock.write(msg)
        self.wait4msg(messages.SubscribeAckBuilder(packetId, [qos]))

    def unsubscribe(self, topic):
        packetId = messages.PacketIdentifier()
        msg = messages.UnSubscribeBuilder(packetId=packetId,
                                          topics=[topic])
        self.sock.write(msg)
        self.wait4msg(messages.UnSubscribeAckBuilder(packetId))

    def ping(self):
        msg = messages.PingReqBuilder()
        self.sock.write(msg)
        self.wait4msg(messages.PingResBuilder())
