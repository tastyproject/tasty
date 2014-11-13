from tasty.types import conversions
from tasty.types import *
from tasty.types.driver import TestDriver
__params__ = {'la': 32, 'lb': 32, 'da': 10}
driver = TestDriver()

def protocol(client, server, params):
    conversions.Paillier_Paillier_receive(client.ha, server.ha, 51, [1], False)
    conversions.Paillier_Paillier_receive(client.hb, server.hb, 184, [1], False)
    server.hc = server.ha * server.hb
    conversions.Paillier_Paillier_send(server.hc, client.hc, 235, [1], False)
