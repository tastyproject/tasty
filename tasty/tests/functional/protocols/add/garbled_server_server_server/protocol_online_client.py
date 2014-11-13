from tasty.types import conversions
from tasty.types import *
from tasty.types.driver import TestDriver
__params__ = {'la': 32, 'lb': 32}
driver = TestDriver()

def protocol(client, server, params):
    conversions.Garbled_Garbled_receive(server.ga, client.ga, 59, [1], False)
    conversions.Garbled_Garbled_receive(server.gb, client.gb, 86, [1], False)
    client.gc = client.ga + client.gb
    conversions.Garbled_Garbled_send(client.gc, server.gc, 87, [1], False)
