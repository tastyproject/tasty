# -*- coding: utf-8 -*

from tasty.types import *

def protocol(client, server, params):
    server.val = Unsigned(bitlen=32).input()
    server.gval = Garbled(bitlen=32, val=server.val)
    server.rval = Unsigned(bitlen=32, val=server.gval)
    if server.val == server.rval:
        server.output("server plain -> garbled -> plain: SUCCESS")
    else:
        server.output("server plain -> garbled -> plain: FAIL!")
    client.val = Unsigned(bitlen=32).input()
    client.gval = Garbled(bitlen=32, val=client.val)
    client.rval = Unsigned(bitlen=32, val=client.gval)
    if client.val == client.rval:
        client.output("client plain -> garbled -> plain: SUCCESS")
    else:
        client.output("client plain -> garbled -> plain: FAIL!")

    server.gval2 = Garbled(bitlen=32, val=server.val)
    client.gval2 <<= server.gval2
    client.rval2 = Unsigned(bitlen=32, val=client.gval2)
    client.sval = Unsigned(bitlen=32, val=42)
    if client.rval2 == client.sval:
        client.output("server plain -> garbled -> client plain: SUCCESS")
    else:
        client.output("server plain -> garbled -> client plain: SUCCESS")




