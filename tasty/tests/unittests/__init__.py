# -*- coding: utf-8 -*-

"""framework test suite

Testing Tasty
=============
Run the complete test suite, call in the root directory of tasty::
    python setup.py test

or simply call a test module::
    python tasty/tests/test_mymodule.py

Tips & tricks:
    If you encounter strange errors when running test cases from the global test
    framework, but the same tests are passing when called directory, try to
    set state.key to None before calling generate_keys

how to write test cases
=======================

    1. create a new file "tests/test_%s.py" % module_name
    2. name every testcase "%sTestCase" % class_name
    3. If the order of test methods matters, add tests with 'addTest()',
    otherwise use a unittest.TestLoader
    4. provide a module level test suite
    5. add in tasty/tests/__init__.py the new test suite

example::
    import unittest

    class MyModuleTestCase(unittest.TestCase):
        def setUp(self):
            '''prepare the test fixture and init needed data'''

            pass

        def tearDown(self):
            '''use this method when data deinitialization is required'''

            pass

        def test_foo(self):
            '''tests method foo of MyModule'''

            pass

        def test_bar(self):
            '''tests method bar of MyModule'''

            pass

    def suite():
        #if order of tests is important
        suite = unittest.TestSuite()
        suite.addTest(MyModuleTestCase("test_foo"))
        suite.addTest(MyModuleTestCase("test_bar"))
        return suite
        # otherwise simply use this
        #return unittest.TestLoader().loadTestsFromTestCase(MyModuleTestCase)

    if __name__ == '__main__':
        unittest.TextTestRunner(verbosity=2).run(suite())
"""

import unittest

from tasty.tests import types_tests
#from tasty.tests import circuit_dynamic_tests
#from tasty.tests import circuit_file_tests
#from tasty.tests import circuit_transformations_tests
#from tasty.tests import garbledcircuit_test
#from tasty.tests import garbled_circuit_cost_test
from tasty.tests import internalprotocol_test
from tasty.tests import tastyot_test
#from tasty.tests import garbledtype_test
from tasty.tests import set_intersection_tests

all_tests = unittest.TestSuite([
    types_tests.suite(),
    #circuit_dynamic_tests.suite(),
    #circuit_file_tests.suite(),
    #circuit_transformations_tests.suite(),
    #garbled_circuit_cost_test.suite(),
    #garbledcircuit_test.suite(),
    #internalprotocol_test.suite(),
    #tastyot_test.suite(),
    #garbledtype_test.suite(),
    #set_intersection_tests.suite()
])

from tasty import state, config
from tasty.protocols.otprotocols import PaillierOT
from tasty.crypt.garbled_circuit import generate_R

import logging
state.log.setLevel(logging.ERROR)

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(all_tests)
