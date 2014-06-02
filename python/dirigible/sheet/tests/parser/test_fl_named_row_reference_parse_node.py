# Copyright (c) 2005-2009 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from dirigible.sheet.parser.parse_node import ParseNode
from dirigible.sheet.parser.fl_named_row_reference_parse_node import FLNamedRowReferenceParseNode


class FLNamedRowReferenceParseNodeTest(unittest.TestCase):

    def testConstruct(self):
        pn = FLNamedRowReferenceParseNode(["#foo#_"])
        self.assertEquals(pn.children, ["#foo#_"])
        self.assertEquals(pn.type, ParseNode.FL_NAMED_ROW_REFERENCE)


    def testRowReference(self):
        pn1 = FLNamedRowReferenceParseNode(["_#foo###   "])
        pn2 = FLNamedRowReferenceParseNode(["blah", "!", "_#foo###  "])
        self.assertEquals(pn1.header, "foo#")
        self.assertEquals(pn2.header, "foo#")


    def testRegisteredWithParse(self):
        "test registered with ParseNode"
        self.assertEquals(type(ParseNode.construct_node(ParseNode.FL_NAMED_ROW_REFERENCE, ['dfytjdky'])), FLNamedRowReferenceParseNode,
                          "Class is not registered with ParseNode")

