# Copyright (c) 2005-2009 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from dirigible.sheet.parser.fl_cell_range_parse_node import FLCellRangeParseNode
from dirigible.sheet.parser.parse_node import ParseNode
from dirigible.sheet.parser.fl_cell_reference_parse_node import FLCellReferenceParseNode

class FLCellRangeParseNodeTest(unittest.TestCase):

    def testConstructor(self):
        flCellRange = FLCellRangeParseNode(["A1", ":", "D2"])
        self.assertEquals(flCellRange.type, ParseNode.FL_CELL_RANGE,
            "Node was of the wrong type")
        self.assertEquals(flCellRange.children, ["A1", ":", "D2"],
            "Node had the wrong children")

    def testStr(self):
        node = FLCellRangeParseNode(["a1", ":", "g8"])
        self.assertEquals(str(node),
            "<FLCellRangeParseNode type=\"FL_CELL_RANGE\" children=['a1', ':', 'g8']>",
            "Wrong string representation")


    def testRegisteredWithParse(self):
        "test registered with ParseNode"
        self.assertEquals(
            type(ParseNode.construct_node(
                ParseNode.FL_CELL_RANGE, ['a1', ':', 'b4'])),
            FLCellRangeParseNode,
            "Class is not registered with ParseNode")


    def testCellReferences(self):
        first = FLCellReferenceParseNode(['a1'])
        second = FLCellReferenceParseNode(['g8'])
        node = FLCellRangeParseNode([first, ":", second])

        self.assertEquals(node.first_cell_reference, first)
        self.assertEquals(node.second_cell_reference, second)

        another = FLCellReferenceParseNode(['c2'])
        node.first_cell_reference = another
        self.assertEquals(node.first_cell_reference, another)

        node.second_cell_reference = another
        self.assertEquals(node.second_cell_reference, another)


    def testColon(self):
        first = FLCellReferenceParseNode(['a1'])
        second = FLCellReferenceParseNode(['g8'])
        node = FLCellRangeParseNode([first, ":", second])
        self.assertEquals(node.colon, ":")



