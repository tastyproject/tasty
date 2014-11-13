# -*- coding: utf-8 -*

from tasty.types import *

def protocol(client, server, params):
    # OK.
    #BITS = 8
    #NUM = 4
    #LENGTH = BITS * NUM

    # OK.
    LENGTH = 48
    SLEN = 48

    #EXP = 8
    #LENGTH = 2 ** EXP

    client.val = Unsigned(bitlen=LENGTH).input(desc="Client:")
    server.val = Unsigned(bitlen=SLEN).input(desc="Server:")

    client.gval = Garbled(bitlen=LENGTH, val=client.val)
    server.gval = Garbled(bitlen=SLEN, val=server.val)

    client.ogval <<= server.gval
    client.gresult = client.ogval * client.gval
    client.result = Unsigned(bitlen=SLEN+LENGTH, val=client.gresult)

    client.output(str(client.result))
