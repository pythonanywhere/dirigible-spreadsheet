# Copyright (c) 2005-2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from mock import sentinel

from sheet.parser.fl_reference_parse_node import FLReferenceParseNode, quote_fl_worksheet_name, unquote_fl_worksheet_name

class FLReferenceParseNodeTest(unittest.TestCase):

    def testWorksheetReferenceProperty(self):
        ref = FLReferenceParseNode(None, [sentinel.onlyChild])
        self.assertEquals(ref.worksheetReference, None)

        ref = FLReferenceParseNode(None, ["'Thin Lizzy'    ", sentinel.second, sentinel.third])
        self.assertEquals(ref.children[0], "'Thin Lizzy'    ")
        self.assertEquals(ref.worksheetReference, 'Thin Lizzy')

        # loses the whitespace information
        ref.worksheetReference = None
        self.assertEquals(ref.children, [sentinel.third])

        # therefore no whitespace information here
        ref.worksheetReference = "Ben Folds' Five    "
        self.assertEquals(ref.children, ["'Ben Folds'' Five    '", '!', sentinel.third])
        self.assertEquals(ref.worksheetReference, "Ben Folds' Five    ")

        ref.children[0] = "'with trailing whitespace'   "
        ref.worksheetReference = "Shihad"
        self.assertEquals(ref.children, ["Shihad   ", '!', sentinel.third])


    def testInit(self):
        self.assertRaises(AssertionError, FLReferenceParseNode, sentinel.type, [sentinel.firstChild, sentinel.secondChild])
        self.assertRaises(AssertionError, FLReferenceParseNode, sentinel.type, [sentinel.child] * 4)

        ref = FLReferenceParseNode(sentinel.type, [sentinel.firstChild])
        self.assertEquals(ref.type, sentinel.type)
        self.assertEquals(ref.children, [sentinel.firstChild])

        ref = FLReferenceParseNode(sentinel.type, [sentinel.firstChild, sentinel.secondChild, sentinel.thirdChild])
        self.assertEquals(ref.type, sentinel.type)
        self.assertEquals(ref.children, [sentinel.firstChild, sentinel.secondChild, sentinel.thirdChild])


    def testCanonicalise(self):
        def assertCanon(reference, worksheetNames, expected):
            ref = FLReferenceParseNode(None, [reference, '!', sentinel.onlyChild])
            ref.canonicalise(worksheetNames)
            self.assertEquals(ref.children[0], expected)

        assertCanon('foo', ['foO'], 'foO')
        assertCanon('foo', [], 'foo')
        assertCanon("'''s'", ["'S"], "'''S'")
        assertCanon("foo  ", [], 'foo  ')

        ref = FLReferenceParseNode(None, ['A1'])
        ref.canonicalise([])
        self.assertEquals(ref.worksheetReference, None)


    def testQuoteFLWorksheetName(self):
        self.assertEquals(quote_fl_worksheet_name("Wyborowa"), "Wyborowa", "Incorrectly quoted")
        self.assertEquals(quote_fl_worksheet_name("#3"), "'#3'", "Incorrectly quoted special character")
        self.assertEquals(quote_fl_worksheet_name("Let's do it."), "'Let''s do it.'", "Incorrectly quoted single quote")
        self.assertEquals(quote_fl_worksheet_name("31337"), "'31337'", "Incorrectly quoted numbers only")
        self.assertEquals(quote_fl_worksheet_name("D31337"), "D31337", "Incorrectly quoted cell-ref-like-name")
        self.assertEquals(quote_fl_worksheet_name("Testing 123"), "'Testing 123'", "Incorrectly quoted name")
        self.assertEquals(quote_fl_worksheet_name("  raz dwa trzy  "), "'  raz dwa trzy  '", "Incorrectly quoted name with spaces")


    def testUnquoteFLWorksheetName(self):
        self.assertEquals(unquote_fl_worksheet_name("Wyborowa"), "Wyborowa", "Incorrectly unquoted")
        self.assertEquals(unquote_fl_worksheet_name("'#3'"), "#3", "Incorrectly unquoted special character")
        self.assertEquals(unquote_fl_worksheet_name("'Let''s do it.'"), "Let's do it.", "Incorrectly unquoted single quote")
        self.assertEquals(unquote_fl_worksheet_name("'31337'"), "31337", "Incorrectly unquoted numbers only")
        self.assertEquals(unquote_fl_worksheet_name("D31337"), "D31337", "Incorrectly unquoted cell-ref-like-name")
        self.assertEquals(unquote_fl_worksheet_name("'Testing 123'"), "Testing 123", "Incorrectly unquoted name")
        self.assertEquals(unquote_fl_worksheet_name("'  raz dwa trzy  '"), "  raz dwa trzy  ", "Incorrectly unquoted name with spaces")
