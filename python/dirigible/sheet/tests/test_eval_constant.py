# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from dirigible.sheet.eval_constant import eval_constant


class TestEvalConstant(unittest.TestCase):

    def test_returns_input_unchanged_in_general(self):
        input = 'input'
        self.assertEquals(id(eval_constant(input)), id(input))


    def test_returns_float_for_floatlike_input(self):
        self.assertEquals(eval_constant('1'), 1)
        self.assertEquals(type(eval_constant('1')), type(1))
        self.assertEquals(eval_constant('1.5'), 1.5)
        self.assertEquals(eval_constant('1.5e10'), 1.5e10)
        self.assertEquals(type(eval_constant('1.5')), type(1.5))

