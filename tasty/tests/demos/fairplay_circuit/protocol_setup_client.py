from tasty.types import conversions
from tasty.types import *
from tasty.types.driver import IODriver
driver = IODriver()

def protocol(client, server, params):
    gc = GarbledCircuit(FairplayCircuit(protocol_path('Add.sfdl.shdl')), ['alice.input', 'bob.input'], ['alice.output'])
    client.gx = Garbled(val=Signed(bitlen=4, dim=[1], signed=True, passive=True, empty=True), signed=True, bitlen=4, dim=[1])
    conversions.Garbled_Garbled_receive(server.gy, client.gy, 4, [1], True)
    (client.gz,) = gc([client.gx, client.gy])
    client.z = Signed(val=client.gz, signed=True, bitlen=5, dim=[1])
