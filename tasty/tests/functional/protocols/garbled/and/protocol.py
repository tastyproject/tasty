
__params__ = {'la': 32, 'lb': 32}

def protocol(client, server, params):
    L = params['la']
    L2 = params['lb']

             
    # input of client
    server.v = Unsigned(bitlen=L).input(src=driver, desc='a')
    server.w = Unsigned(bitlen=L).input(src=driver, desc='b')

    client.gv <<= Garbled(val=server.v)
    client.gw <<= Garbled(val=server.w)
    client.gz = client.gv & client.gw
    client.z = Unsigned(val=client.gz)
    client.z.output(dest=driver, desc="c")
