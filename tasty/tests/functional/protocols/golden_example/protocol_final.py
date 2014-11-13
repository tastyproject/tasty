from tasty.types.driver import TestDriver
__params__ = {'dim': 10, 'lenX': 32, 'lenY': 32}
driver = TestDriver()

def protocol(client, server, params):
    N = params['dim']
    Lx = params['lenX']
    Ly = params['lenY']
    client.v = UnsignedVec(bitlen=Lx, dim=N)
    client.v.input(src=driver, desc='X')
    server.w = UnsignedVec(bitlen=Ly, dim=N)
    server.w.input(src=driver, desc='Y')
    server.hv <<= HomomorphicVec(val=client.v)
    server.hx = server.hv * server.w
    client.gx <<= GarbledVec(val=server.hx)
    client.gmin = client.gx.min_value()
    client.min = Unsigned(val=client.gmin)
    client.min.output(desc='r', dest=driver)
