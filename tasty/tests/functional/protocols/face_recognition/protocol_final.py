from tasty.types.driver import TestDriver
__params__ = {'K': 12, 'N': 10304, 'M': 42}
driver = TestDriver()

def protocol(c, s, p):
    K = p['K']
    N = p['N']
    M = p['M']
    s.homegabar = HomomorphicVec(dim=K)
    s.hgamma = HomomorphicVec(dim=N)
    s.hD = HomomorphicVec(dim=M)
    c.bot = Unsigned(val=M, bitlen=bitlength(M))
    c.gbot = Garbled(val=c.bot)
    c.gamma = UnsignedVec(bitlen=8, dim=N).input(src=driver, desc='gamma')
    s.omega = UnsignedVec(bitlen=32, dim=(M, K)).input(src=driver, desc='omega')
    s.psi = UnsignedVec(bitlen=8, dim=N).input(src=driver, desc='psi')
    s.u = SignedVec(bitlen=8, dim=(K, N)).input(src=driver, desc='u')
    s.tau = Unsigned(bitlen=50).input(src=driver, desc='tau')
    s.hgamma <<= HomomorphicVec(val=c.gamma)

    for i in xrange(K):
        s.homegabar[i] = Homomorphic(val=-s.u[i].dot(s.psi)) + s.hgamma.dot(s.u[i])

    s.hs3 = s.homegabar.dot(s.homegabar)

    for i in xrange(M):
        s.hD[i] = s.hs3 + s.omega[i].dot(s.omega[i])
        s.hD[i] += s.homegabar.dot(s.omega[i] * -2)

    c.gD <<= GarbledVec(val=s.hD, force_bitlen=50, force_signed=False)
    (c.gDmin_val, c.gDmin_ix) = c.gD.min_value_index()
    c.gtau <<= Garbled(val=s.tau)
    c.gcmp = c.gDmin_val < c.gtau
    c.gout = c.gcmp.mux(c.gbot, c.gDmin_ix)
    c.out = Unsigned(val=c.gout)

    if c.out == c.bot:
        c.output(None, dest=driver, desc='out')
    else:
        c.output(c.out, desc='out', dest=driver)
