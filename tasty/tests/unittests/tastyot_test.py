# -*- coding: utf-8 -*-
import unittest
from tasty.tastyot import TastyOT
from multiprocessing import Process
from tasty.osock import *
from time import sleep
from tasty.types import Party
from tasty import utils, config, state
from tasty.protocols.otprotocols import paillierot
from tasty.protocols.otprotocols import PaillierOT, ECNaorPinkasOT
import socket, atexit
from gmpy import mpz
from itertools import product
import time

#TODO: @Immo: please document how OT tests work

class TastyOTTestCase(unittest.TestCase):
    def setUp(self):
        state.config = config.create_configuration(security_level="short", asymmetric_security_parameter=1024, symmetric_security_parameter=80, ot_type = "EC", host="::1", port=8000, protocol_dir="docs/millionaires_problem/")
        state.config.ot_chain = [PaillierOT]

    def test_tastyot(self):
        """ testing the global TastyOT """

        # state.config.ot_chain = [paillierot.PaillierOT]

        n = 128 # must be even

        self.ot = t = OTTest(n)
        x = tuple(utils.get_random(0,1,n/2))
        y = tuple(utils.get_random(0,1,n/2))

        xc = [tuple(utils.get_random(0,2**80-1,2)) for i in xrange(n/2)]
        yc = [tuple(utils.get_random(0,2**80-1,2)) for i in xrange(n/2)]

        resultx = tuple(map(lambda x: mpz(x[0][x[1]]), zip(xc, x)))
        resulty = tuple(map(lambda x: mpz(x[0][x[1]]), zip(yc, y)))

        res = t.next_ots(x, xc)[1]
        self.assertEqual(res, resultx)
        res2 = t.next_ots(y, yc)[1]
        self.assertEqual(res2, resulty)
#        self.failUnlessRaises(OverflowError, t.next_ots, t, ((1,),(5,7)))

    def test_ot_protocol_performance(self):
        """ testing available OT protocols """
#        for security_level, ot_type in product(("short","medium","long"), ("Paillier","EC_c","EC")):
        for security_level, ot_type in product(("short","medium","long"), ("EC_c","EC")):
            print security_level, ot_type,
            start_time = time.clock()

            #protocols = [ECNaorPinkasOT.NP_EC_OT_secp192r1, ECNaorPinkasOT.NP_EC_OT_secp192r1_c, \
            #             ECNaorPinkasOT.NP_EC_OT_secp224r1, ECNaorPinkasOT.NP_EC_OT_secp224r1_c, \
            #             ECNaorPinkasOT.NP_EC_OT_secp256r1, ECNaorPinkasOT.NP_EC_OT_secp256r1_c]
            #protocols = state.config.ot_chain

            n = state.config.symmetric_security_parameter

#        for prot in protocols:
#            print prot.__name__
#            state.config.ot_chain = [prot]

            self.ot = t = OTTest(n)
            x = tuple(utils.get_random(0,1,n/2))
            y = tuple(utils.get_random(0,1,n/2))

            xc = [tuple(utils.get_random(0,2**n-1,2)) for i in xrange(n/2)] # n-bit messages
            yc = [tuple(utils.get_random(0,2**n-1,2)) for i in xrange(n/2)] # n-bit messages

            resultx = tuple(map(lambda x: mpz(x[0][x[1]]), zip(xc, x)))
            resulty = tuple(map(lambda x: mpz(x[0][x[1]]), zip(yc, y)))

            res = t.next_ots(x, xc)[1]
            self.assertEqual(res, resultx)
            res2 = t.next_ots(y, yc)[1]
            self.assertEqual(res2, resulty)

            print "%fs" % (time.clock()-start_time)

class OTTest(object):
    #TODO: @Immo: please document how OTTest works
    def __init__(self, num):
        self.num = num
        p = Process(target=OTTest.client,
                    args=(self, num))
        p.start()
        self.init_server()
        atexit.register(self.__del__)

    def next_ots(self, choices, transfer):
#        debug ("starting online phase")
        self.csock.sendobj("online")
        self.csock.sendobj(choices)
        sres = self.server_online(transfer)
        cres = self.csock.recvobj()
        return (sres, cres)

    def init_client(self):
        sleep(.1) #give the server time to set up
        sock = ClientObjectSocket(host="::1", port=8000)
        sleep(.1)
        self.csock = ClientObjectSocket(host="::1", port=8001)
        self.party = Party(role=Party.CLIENT, sock=sock)

    def client(self, num):
        self.init_client()
        self.ot = TastyOT(self.party, num)

        while True:
            next = self.csock.recvobj()
#            debug ("executing command %s"%next)
            if next == "online":
                self.client_online(self.csock.recvobj())
            elif next == "quit":
                exit(0)
            else:
                raise NotImplementedError(next)

    def init_server(self):
        sock = ServerObjectSocket(host="::1", port=8000).accept()[0]
        self.csock = ServerObjectSocket(host="::1", port=8001).accept()[0]
        self.party = party = Party(role=Party.SERVER, sock=sock)
        self.ot = TastyOT(self.party, self.num)

    def client_online(self, arg):
        self.csock.sendobj(self.ot.next_ots(arg))

    def server_online(self, arg):
        self.ot.next_ots(arg)

    def __del__(self):
        try:
            self.csock.sendobj("quit")
            self.csock.close()
        except socket.error: #server side has already exited
            pass

def suite():
    suite = unittest.TestSuite()
#    suite.addTest(TastyOTTestCase("test_tastyot"))
    suite.addTest(TastyOTTestCase("test_ot_protocol_performance"))
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
