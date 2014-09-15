# -*- coding: utf-8 -*-
# Copyright (c) 2005-2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#


try:
    import unittest2 as unittest
except ImportError:
    import unittest

from sheet.utils.string_utils import (
    correct_case, double_quote_repr_string, get_lstripped_part, get_rstripped_part
)


class StringUtilsTest(unittest.TestCase):

    def test_get_rstripped_part(self):
        self.assertEquals(get_rstripped_part("foo     "), "     ", "get_r_stripped_part broken")
        self.assertEquals(get_rstripped_part("   foo "), " ", "get_r_stripped_part broken")
        self.assertEquals(get_rstripped_part(""), "", "get_r_stripped_part broken")


    def test_get_lstripped_part(self):
        self.assertEquals(get_lstripped_part("     foo"), "     ", "get_l_stripped_part broken")
        self.assertEquals(get_lstripped_part("foo "), "", "get_l_stripped_part broken")
        self.assertEquals(get_lstripped_part(" foo   "), " ", "get_l_stripped_part broken")
        self.assertEquals(get_lstripped_part(""), "", "get_l_stripped_part broken")


    def test_double_quote_repr(self):
        "test double_quote_repr_string"
        self.assertEquals(double_quote_repr_string('what\'s "this"'), '"what\'s \\"this\\""', "didn't work")
        self.assertEquals(double_quote_repr_string(''), '""', "didn't work")


    def testCorrectCase(self):
        self.assertEquals(correct_case("a", ["A", "B"]), "A", "case not corrected")
        self.assertEquals(correct_case("a", ["C", "B"]), "a", "changed despite no matches")
        self.assertEquals(correct_case("flippertigibbet", ["A", "B", "FlipperTiGibbet"]), "FlipperTiGibbet", "case not corrected")

