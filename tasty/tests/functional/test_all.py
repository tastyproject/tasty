# -*- coding: utf-8 -*-
import addition_tests
import multiplication_tests
import set_intersection_tests
import garbledfilecircuit_tests
import conversion_tests
import golden_example_tests
import unittest

def suite():
    s = unittest.TestSuite()
    s.addTests(conversion_tests.suite())
    s.addTests(addition_tests.suite())
    s.addTests(multiplication_tests.suite())
    s.addTests(set_intersection_tests.suite())
    s.addTests(garbledfilecircuit_tests.suite())
    s.addTests(golden_example_tests.suite())
    return s

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
