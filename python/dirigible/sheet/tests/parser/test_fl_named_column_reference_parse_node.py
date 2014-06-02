# Copyright (c) 2005-2009 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from dirigible.sheet.parser.parse_node import ParseNode
from dirigible.sheet.parser.fl_named_column_reference_parse_node import FLNamedColumnReferenceParseNode


class FLNamedColumnReferenceParseNodeTest(unittest.TestCase):

    def testConstruct(self):
        pn = FLNamedColumnReferenceParseNode(["#foo#_"])
        self.assertEquals(pn.children, ["#foo#_"])
        self.assertEquals(pn.type, ParseNode.FL_NAMED_COLUMN_REFERENCE)


    def testColumnReference(self):
        pn1 = FLNamedColumnReferenceParseNode(["#foo###_   "])
        pn2 = FLNamedColumnReferenceParseNode(["blah", "!", "#foo###_  "])
        self.assertEquals(pn1.header, "foo#")
        self.assertEquals(pn2.header, "foo#")


    def testRegisteredWithParse(self):
        "test registered with ParseNode"
        self.assertEquals(type(ParseNode.construct_node(ParseNode.FL_NAMED_COLUMN_REFERENCE, ['dfytjdky'])),
                          FLNamedColumnReferenceParseNode,
                          "Class is not registered with ParseNode")
