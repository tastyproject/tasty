# -*- coding: utf-8 -*-

__params__ = {}
def protocol(client, server, params):
    l = 24
    server.zero = Unsigned(bitlen=1, val=0)
    client.gzero <<= Garbled(val=server.zero)
    
    # input of client
    client.x = SignedVec(bitlen=l, dim=15).input(src=driver, desc="x")
    server.A = SignedVec(bitlen=l, dim=(6, 15)).input(src=driver, desc="A")

    server.hx <<= HomomorphicVec(val=client.x)

    server.hy = HomomorphicVec(dim=6)
    for i in xrange(6):
        server.hy[i] = server.A[i].dot(server.hx)
        
    client.y <<= SignedVec(val=server.hy)
    client.y.output()
    client.gy <<= GarbledVec(val=server.hy)
    client.y2 = SignedVec(val=client.gy)
    client.y2.output(desc='aaargh')

    client.gs = GarbledVec(dim=6)
    for i in xrange(6):
        client.gs[i] = client.gy[i] > client.gzero

    client.s = UnsignedVec(val=client.gs)
    client.s.output()

    client.VF = Unsigned(val=~client.gs[0] & ~client.gs[2])
    client.VT = Unsigned(val=~client.gs[0] & client.gs[2])
    client.SVT = Unsigned(val=client.gs[0] & ~client.gs[2])
    client.gt = client.gs[0] & client.gs[1]

    client.PVC = Unsigned(val=client.gt & ~client.gs[3] & ~client.gs[4])
    client.APC = Unsigned(val=client.gt & client.gs[3] & ~client.gs[5])

    if client.VF:
        client.output("VF", desc="out", dest=driver)
    elif client.VT:
        client.output("VT", desc="out", dest=driver)
    elif client.SVT:
        client.output("SVT", desc="out", dest=driver)
    elif client.PVC:
        client.output("PVC", desc="out", dest=driver)
    elif client.APC:
        client.output("APC", desc="out", dest=driver)
    else:
        client.output("NSR", desc="out", dest=driver)
