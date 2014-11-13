def protocol(client, server):
    N = 4
    L = 32
    client.setup_output('client setup test')
    server.setup_output('server setup test')
    client.v = UnsignedVec(bitlen=L, dim=N)
    client.v.input(desc='enter values for v')
    server.w = UnsignedVec(bitlen=L, dim=N)
    server.w.input(desc='enter values for w')
    client.hv = HomomorphicVec(val=client.v)
    server.hv <<= client.hv
    server.hx = server.hv * server.w
    client.gx <<= GarbledVec(val=server.hx)
    client.gmin = client.gx.min_value()
    client.min = Unsigned(val=client.gmin)
    client.min.output(desc='minimum value')
    client.setup_output('client setup test 2')
    server.setup_output('server setup test 2')
    client.min.setup_output(desc='blah')
