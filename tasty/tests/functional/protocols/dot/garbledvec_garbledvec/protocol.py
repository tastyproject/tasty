# -*- coding: utf-8 -*-

from tasty.types import *
from tasty import state
from tasty.cost_results import *


def protocol(client, server):
    server.v = UnsignedVec(bitlen=16, dim=1000).input(random=True)
    server.w = UnsignedVec(bitlen=16, dim=1000).input(random=True)
    server.cr = server.v.dot(server.w)
    client.cr <<= server.cr
 
    server.hv = HomomorphicVec(val=server.v)
    server.hw = HomomorphicVec(val=server.w)
    server.hr = server.hv.dot(server.hw)
    client.hr <<= server.hr
    client.r = Unsigned(val=client.hr)

    if client.cr == client.r:
        client.output("SUCCESS")
    else:
        client.output("FAIL!")
