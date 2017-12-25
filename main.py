from mqtt import sock
from mqtt.client import Client

IO_KEY='?????',
IO_USER='ranma1988'

class AdafruitMQTT(Client):
    def __init__(self):
        s = sock.Sock('io.adafruit.com', 1883)
        super(AdafruitMQTT, self).__init__(s)

        self.connect(client_id="cupz",
                     key=IO_KEY,
                     user=IO_USER)

    def __enter__(self):
        return self

    def __exit__(self ,type, value, traceback):
        self.disconnect()


if __name__ == "__main__":
    # http://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.pdf
    with AdafruitMQTT() as mqtt:
        mqtt.publish('ranma1988/feeds/test', 'ON') # https://io.adafruit.com/ranma1988/feeds/test

    print('done')
