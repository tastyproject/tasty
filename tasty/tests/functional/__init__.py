# -*- coding: utf-8 -*-

import os, os.path, sys, time
import unittest
from multiprocessing import Process, Pipe


from tasty.scripts import main
from tasty import state
from tasty import config

path = os.path.join(state.tasty_root, "tests/functional/protocols")
#test_protocols = [os.path.join(path, i) for i in filter(lambda x: x != ".svn", os.listdir(path))]
test_protocols = [os.path.join(path, "millionaires_problem")]

class TastyProtocolTestBase(unittest.TestCase):

    def test_protocols(self):
        self.p = test_protocols.pop(0)
        oldsys = sys.argv
        sys.argv = ["tasty", "-sv", self.p]
        self.server_tasty = Process(target=main.start, name="Process_tasty_server")
        self.server_tasty.start()
        sys.argv = ["tasty", "-cv", self.p]
        self.client_tasty = Process(target=main.start, name="Process_tasty_client")
        self.client_tasty.start()

        sys.argv = oldsys

def suite():
    suite = unittest.TestSuite()
    for i in test_protocols:
        suite.addTest(TastyProtocolTestBase("test_protocols"))
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
