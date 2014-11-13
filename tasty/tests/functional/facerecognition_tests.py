# -*- coding: utf-8 -*-

import unittest

from tasty.utils import tasty_path, rand, get_random, nogen, bitlength
from tasty import test_utils
from operator import mul
from tasty.types import Unsigned


class done(Exception):
    pass


def dot(a, b):
    return sum(map(mul, a, b))


class FaceRecognitionTestCase(test_utils.TastyRemoteCTRL):

    def protocol_dir(self):
        return tasty_path("tests/functional/protocols/face_recognition")


    def random(self, bitlen, signed, num = 1):
        if signed:
            start, end = -(2**(bitlen - 1)), 2**(bitlen - 1) - 1
        else:
            start, end = 0, 2**bitlen  - 1
        if num > 1:
            return list(get_random(start, end, num))
        else:
            return rand.randint(start, end)



    def next_data_in(self):

        def eigenface(params, gamma, omega, psi, u, tau):
            """ The Eigenface Algorithm """

            def project(gamma, u, psi):
                """ generate omegabar """
                return [dot(map(lambda x: -1 * x, ui), psi) + dot(gamma, ui) for ui in u]

            def distance(omegabar, omega):
                """ compute D """

                s3 = dot(omegabar, omegabar)
                return [dot(omegai, omegai) + s3 + dot(omegabar, map(lambda x: -2 * x, omegai)) for omegai in omega]

            def minimum(D, tau):
                """ find minimum index if smaller then trashhold tau, else None """

                mD = min(D)
                if mD > tau:
                    return None
                else:
                    return D.index(mD)

            omega = map(list, omega)
            gamma = list(gamma)
            psi = list(psi)
            u = map(nogen, u)
            tau = tau

            omegabar = project(gamma, u, psi)
            D = distance(omegabar, omega)
            return minimum(D, tau)



        while True:

            self.params = {"K": 12, "N": 10304, "M": 42}

            self.client_inputs = {"gamma": self.random(4, False, self.params["N"])}
            self.server_inputs = {"omega": [self.random(6, False, self.params["K"]) for i in xrange(self.params["M"])],
                              "psi": self.random(4, False, self.params["N"]),
                                  "u": [self.random(6, True, self.params["N"]) for i in xrange(self.params["K"])],
                                  "tau": self.random(40, False)}

            tmp = eigenface(self.params, self.client_inputs["gamma"],
                            self.server_inputs["omega"],
                            self.server_inputs["psi"],
                            self.server_inputs["u"],
                            self.server_inputs["tau"])
            if tmp is None:
                self.result = None
            else:
                self.result = Unsigned(val=tmp, bitlen=bitlength(self.params["M"] + 1))
            yield
            if tmp is not None :
                break


    def next_data_out(self):
        while True:
            self.assertEqual(self.client_outputs["out"], self.result)
#            print "*" * 50, "OK!", "*" * 50
#            time.sleep(60)
            yield
        #FIXME: calculate nums of costs
        #self.assertEqual(
            #self.client_costs[0]["abstract"]["online"]["accumulated"]["Enc"],
            #4)
        #self.assertEqual(
            #self.client_costs[1]["abstract"]["online"]["accumulated"]["Enc"],
            #5)
        #self.assertEqual(
            #self.client_costs[2]["abstract"]["online"]["accumulated"]["Enc"],
            #6)
        #self.assertEqual(
            #self.server_costs[0]["abstract"]["online"]["accumulated"]["Enc"],
            #3)
        #self.assertEqual(
            #self.server_costs[1]["abstract"]["online"]["accumulated"]["Enc"],
            #4)
        #self.assertEqual(
            #self.server_costs[2]["abstract"]["online"]["accumulated"]["Enc"],
            #5)

def suite():
    """narf"""
    tests = unittest.TestSuite()
    tests.addTest(FaceRecognitionTestCase())
    return tests


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=0).run(suite())
