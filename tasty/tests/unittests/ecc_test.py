import unittest
from tasty.crypt.homomorph.ecc import getEC
from tasty.crypt.homomorph.ecc import decodePoint
from tasty.crypt.homomorph.ecc import ECPoint


class ECCTestCase(unittest.TestCase):

    def setUp(self):
        self.EC = getEC("secp256r1")
        

    def testPointCompression(self):
        cG = "036B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296".lower()
        self.assertEqual(self.EC.G.encode(True),cG)

    def testPointDecompression(self):
        G = decodePoint("036B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296", self.EC)
        self.assertEqual(G, self.EC.G)

    def testCompressInfinity(self):
        inf = ECPoint(0,0,self.EC,True)
        self.assertEqual(inf, decodePoint(inf.encode(True),self.EC))



def suite():
    suite = unittest.TestSuite()
    suite.addTest(ECCTestCase("testPointCompression"))
    suite.addTest(ECCTestCase("testPointDecompression"))
    suite.addTest(ECCTestCase("testCompressInfinity"))
    return suite

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(suite())