from mqtt import messages


class Client:
    def __init__(self, sock):
        self.sock = sock

    def connect(self, key, user, client_id):
        self.sock.open()

        msg = messages.ConnectMsgBuilder(clientID=client_id,
                                         user=user,
                                         password=key)
        self.write(msg)
        ret = self.read(20)

        expected_resp = messages.ConnectACKMsgBuilder(sessionPresentFlag=False).toBytes()
        assert ret == expected_resp, "can't connect"

    def write(self, msg):
        if isinstance(msg, messages.ControlPacket):
            msg = msg.toBytes()
        return self.sock.write(msg)

    def read(self, num):
        return self.sock.read(num)

    def disconnect(self):
        msg = messages.DisconnectMsgBuilder()
        self.write(msg)
        self.sock.close()

    def publish(self, topic, value):
        msg = messages.PublishMsgBuilder(topic=topic, value=value)
        self.write(msg)
