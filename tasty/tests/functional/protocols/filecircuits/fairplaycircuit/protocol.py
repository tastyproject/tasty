# -*- coding: utf-8 -*-

__params__ = {}
def protocol(client, server):
    gc = GarbledCircuit(
        FairplayCircuit(protocol_path("Add.sfdl.shdl")),
        ["alice.input", "bob.input"],
        ["alice.output"])

    # Plain inputs
    client.x = Signed(bitlen=4).input(src=driver, desc="a")
    server.y = Signed(bitlen=4).input(src=driver, desc="b")

    # Convert plain to garbled inputs
    client.gx = Garbled(val=client.x)
    server.gy = Garbled(val=server.y)
    client.gy <<= server.gy

    # Evaluate GC
    client.gz, = gc([client.gx, client.gy])

    # Convert garbled to plain outputs
    client.z = Signed(val=client.gz)

    ## Output results
    client.z.output(dest=driver, desc="zc")
