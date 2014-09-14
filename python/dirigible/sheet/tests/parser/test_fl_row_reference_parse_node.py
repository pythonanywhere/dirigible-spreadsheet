# Copyright (c) 2005-2009 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from sheet.parser.parse_node import ParseNode
from sheet.parser.fl_row_reference_parse_node import FLRowReferenceParseNode
from sheet.parser.fl_reference_parse_node import FLReferenceParseNode


class FLRowReferenceParseNodeTest(unittest.TestCase):

    def testConstructor(self):
        flRowReference = FLRowReferenceParseNode(["_1"])
        self.assertTrue(isinstance(flRowReference, FLReferenceParseNode), 'should be a parse node')
        self.assertEquals(flRowReference.type, ParseNode.FL_ROW_REFERENCE, "Node was of the wrong type")
        self.assertEquals(flRowReference.children, ["_1"], "Node had the wrong children")


    def testStr(self):
        node = FLRowReferenceParseNode(["_1"])
        self.assertEquals(str(node), "<FLRowReferenceParseNode type=\"FL_ROW_REFERENCE\" children=['_1']>", "Wrong string representation")


    def testIsAbsolute(self):
        self.assertFalse(FLRowReferenceParseNode(["_1"]).isAbsolute, "Incorrect isAbsolute for _1")
        self.assertTrue(FLRowReferenceParseNode(["_$1"]).isAbsolute, "Incorrect isAbsolute for _$1")

        self.assertFalse(FLRowReferenceParseNode(["SheetSomething", "! ", "_1"]).isAbsolute,
                         "Incorrect isAbsolute for _1 with worksheet")
        self.assertTrue(FLRowReferenceParseNode(["SheetSomething", "! ", "_$1"]).isAbsolute,
                         "Incorrect isAbsolute for _$1 with worksheet")


    def testPlainRowName(self):
        self.assertEquals(FLRowReferenceParseNode(["_1"]).plainRowName, "1", "Incorrect plainRowName for _1")
        self.assertEquals(FLRowReferenceParseNode(["_$1"]).plainRowName, "1", "Incorrect plaiaRowName for _$1")

        self.assertEquals(FLRowReferenceParseNode(["SheetSomething", "! ", "_1"]).plainRowName, "1",
                          "Incorrect plainRowName for _1 with worksheet")
        self.assertEquals(FLRowReferenceParseNode(["SheetSomething", "! ", "_$1"]).plainRowName, "1",
                          "Incorrect plainRowName for _$1 with worksheet")


    def testRegisteredWithParse(self):
        "test registered with ParseNode"
        self.assertEquals(type(ParseNode.construct_node(ParseNode.FL_ROW_REFERENCE, [])), FLRowReferenceParseNode,
                          "Class is not registered with ParseNode")


    def testSettingPlainRowName(self):
        row = FLRowReferenceParseNode(["_1 "])
        row.plainRowName = "3"
        self.assertEquals(row.localReference, "_3 ")

        row = FLRowReferenceParseNode(["_$1 "])
        row.plainRowName = "3"
        self.assertEquals(row.localReference, "_$3 ")


    def testRowReferenceProperty(self):
        self.assertEquals(FLRowReferenceParseNode(["_1"]).localReference, "_1")
        self.assertEquals(FLRowReferenceParseNode(["ws1", "!", "_1"]).localReference, "_1")


    def testSettingRowProperty(self):
        row = FLRowReferenceParseNode(["_1 "])
        row.localReference = "12345"
        self.assertEquals(row.localReference, "12345")

        row = FLRowReferenceParseNode(["_$1 "])
        row.localReference = "#Deleted!"
        self.assertEquals(row.localReference, "#Deleted!")


    def testRowIndexProperty(self):
        self.assertEquals(FLRowReferenceParseNode(["_4"]).rowIndex, 4)
        self.assertEquals(FLRowReferenceParseNode(["_$2"]).rowIndex, 2)


    def testOffset(self):
        node = FLRowReferenceParseNode(['_2 '])
        node.offset(1000, 0)
        self.assertEquals(node.localReference, '_2 ')
        node.offset(-1000, 1)
        self.assertEquals(node.localReference, '_3 ')
        node.offset(0, -2)
        self.assertEquals(node.localReference, '_1 ')
        node.offset(1337, -1)
        self.assertEquals(node.localReference, '#Invalid! ')


    def testOffsetAbsoluteRefs(self):
        node = FLRowReferenceParseNode(['_$3 '])
        node.offset(0xDEADBEEF, 54)
        self.assertEquals(node.localReference, '_$3 ')

        node.offset(0xDEADBEEF, 4, moveAbsolute=True)
        self.assertEquals(node.localReference, '_$7 ')


    def testCoords(self):
        node = FLRowReferenceParseNode(['_$1 '])
        self.assertEquals(node.coords, (0, 1))

        node = FLRowReferenceParseNode(['_2 '])
        self.assertEquals(node.coords, (0, 2))

