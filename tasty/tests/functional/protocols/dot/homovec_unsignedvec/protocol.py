# -*- coding: utf-8 -*-

from tasty.types import *
from tasty import state
from tasty.cost_results import *


def protocol(client, server):
    client.v = UnsignedVec(bitlen=16, dim=1000).input(random=True)
    client.w = UnsignedVec(bitlen=16, dim=1000).input(random=True)
    client.hv = HomomorphicVec(val=client.v)
    client.hr = client.hv.dot(client.w)
    client.r = Unsigned(val=client.hr)
    client.cr = client.v.dot(client.w)
    if client.cr == client.r:
        client.output("SUCCESS")
    else:
        client.output("FAIL!")
