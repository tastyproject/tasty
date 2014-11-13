# -*- coding: utf-8 -*-
import unittest
from itertools import product #cartesian product
from time import sleep
from multiprocessing import Process, Queue
import atexit
import socket

#from tasty.protocols import protocol
from tasty.types import Party
from tasty.protocols.transport import Transport
from tasty.protocols.otprotocols import *
from tasty.protocols.gc_protocols import *
from tasty.osock import *
from tasty import config, state
from tasty.crypt.garbled_circuit import *
from tasty.circuit import *
from tasty.circuit.dynamic import *

class InternalProtocolTestCase(unittest.TestCase):
    """ internal protocol test class """


    def test_transport(self):
        test = ProtocolTest(Transport)
        sval = ("have you mooed today?",)
        cval = ("how are you?",)
        test.run_online(sval, cval)
        sres, cres = test.get_result()
        self.assertEqual((sres, cres), (cval, sval))
        del test

    def test_dummyot(self):
        test = ProtocolTest(DummyOT)
        sval = ((5, 7),(9,10))
        cval = (0,1)
        test.run_online(sval,cval)
        sres, cres = test.get_result()
        self.assertEqual(cres[0],5)
        self.assertEqual(cres[1],10)
        del test

    def test_paillierot(self):
        test = ProtocolTest(PaillierOT)
        sval = ((5, 7),(9,10))
        cval = (0,1)
        test.run_online(sval,cval)
        sres, cres = test.get_result()
        self.assertEqual(cres[0],5)
        self.assertEqual(cres[1],10)
        del test

    def test_gcproto(self):
        if not state.R:
            state.R = generate_R()
        c = AddCircuit(5, 5, UNSIGNED, UNSIGNED)
        null_inputs = tuple(tuple(generate_garbled_value(l)) for l in (5, 5))
        bval = (value2bits(mpz(12), 5), value2bits(mpz(12), 5))
        inputs = [tuple(plain2garbled(y, x, state.R)) for x, y in zip(null_inputs, bval)]

        test = ProtocolTest(GCProtocol, sargs=(c, state.R) + null_inputs)
        test.run_precomputation()
        sgcr, tmp = test.get_precomputation_result()
        test.run_online((None,), (c,) + tuple(inputs))
        sres, cres = test.get_result()
        cres = tuple(cres)
        sgcr = tuple(sgcr)
#        print "sgcr = %s\ncres = %s"%(str(sgcr),str(cres))
        sgcres = map(lambda x: x & 1, sgcr[0])
        out = bits2value(tuple(perm2plain(cres[0], sgcres)))
        self.assertEqual(out, 12+4)






class ProtocolTest(object):
    def __init__(self, protocolclass = None, cargs=None, sargs=None):
        self.protocolclass = protocolclass
        self.cargs = cargs
        self.sargs = sargs
        p = Process(target=ProtocolTest.client,
                    args=(self, protocolclass))
        p.start()
        self.init_server()
        atexit.register(self.__del__)

    def run_online(self, sparam=None, cparam=None):
#        debug ("starting online phase")
        self.csock.sendobj("online")
        self.csock.sendobj(cparam)
        self.server_online(sparam)

    def run_precomputation(self):
        self.csock.sendobj("precompute")
        self.server_precompute()

    def queueget_block(self):
        ret = self.csock.recvobj()
        return ret

    def init_client(self):
        sleep(.1) #give the server time to set up
        sock = ClientObjectSocket(host="::1", port=8000)
        sleep(.1)
        self.csock = ClientObjectSocket(host="::1", port=8001)
        self.party = Party(role=Party.CLIENT, sock=sock)

    def client(self, protocol):
        self.init_client()
        if self.cargs:
            self.protocol = self.protocolclass(self.party, self.cargs)
        else:
            self.protocol = self.protocolclass(self.party)

        while True:
            next = self.queueget_block()
#            debug ("executing command %s"%next)
            if (next == "precompute"):
                self.client_precompute()
            elif next == "online":
                self.client_online(self.queueget_block())
            elif next == "quit":
                exit(0)
            elif next == "precomp_results":
                self.csock.sendobj(tuple(self.protocol.get_precomputation_results()))
            elif next == "results":
#                print "getting client results"
                result = tuple(self.protocol.get_results())
#                print "result = %s"%str(result)
                self.csock.sendobj(result)
            elif next is None or "":
                sleep (.1)
            else:
                raise NotImplementedError(next)

    def get_result(self):
        self.csock.sendobj("results")
        sres = tuple(self.protocol.get_results())
        cres = self.queueget_block()
        return sres, cres

    def get_precomputation_result(self):
        self.csock.sendobj("precomp_results")
        sres = tuple(self.protocol.get_precomputation_results())
        cres = self.queueget_block()
        return sres, cres

    def init_server(self):
        sock = ServerObjectSocket(host="::1", port=8000).accept()[0]
        self.csock = ServerObjectSocket(host="::1", port=8001).accept()[0]
        self.party = party = Party(role=Party.SERVER, sock=sock)
        if self.sargs is not None :
            self.protocol = self.protocolclass(self.party, self.sargs)
        else:
            self.protocol = self.protocolclass(self.party)

    def client_online(self, arg):
#        debug ("client online phase, arg = %s"%str(arg))
        self.protocol(arg)

    def client_precompute(self):
#        debug ("starting client precomputation")
        protocol.Protocol.precompute()

    def server_online(self, arg):
#        debug ("starting online")
        self.protocol(arg)

    def server_precompute(self):
        protocol.Protocol.precompute()

    def __del__(self):
        try:
            self.csock.sendobj("quit")
            self.csock.close()
        except socket.error: #server side has already exited
            pass


def suite():
    config.create_configuration(host="::1", port=8000, symmetric_security_parameter=80, asymmetric_security_parameter=1024, protocol_dir="/tmp", ot_chain=[PaillierOT,])
    state.R = generate_R()
    suite = unittest.TestSuite()
    suite.addTest(InternalProtocolTestCase("test_transport"))
    suite.addTest(InternalProtocolTestCase("test_dummyot"))
    suite.addTest(InternalProtocolTestCase("test_paillierot"))
    suite.addTest(InternalProtocolTestCase("test_gcproto"))
    return suite


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
