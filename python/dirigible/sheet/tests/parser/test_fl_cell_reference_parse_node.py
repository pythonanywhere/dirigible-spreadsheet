# Copyright (c) 2005-2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from dirigible.sheet.parser.parse_node import ParseNode
from dirigible.sheet.parser.fl_cell_reference_parse_node import FLCellReferenceParseNode
from dirigible.sheet.parser.fl_reference_parse_node import FLReferenceParseNode

class FLCellReferenceParseNodeTest(unittest.TestCase):

    def testConstructor(self):
        flCellReference = FLCellReferenceParseNode(["A1"])
        self.assertTrue(isinstance(flCellReference, FLReferenceParseNode), 'should be a parse node')
        self.assertEquals(flCellReference.type, ParseNode.FL_CELL_REFERENCE, "Node was of the wrong type")
        self.assertEquals(flCellReference.children, ["A1"], "Node had the wrong children")


    def testStr(self):
        node = FLCellReferenceParseNode(["a1"])
        self.assertEquals(str(node), "<FLCellReferenceParseNode type=\"FL_CELL_REFERENCE\" children=['a1']>", "Wrong string representation")


    def testColAbsolute(self):
        self.assertFalse(FLCellReferenceParseNode(["A1"]).colAbsolute, "Incorrect colAbsolute for A1")
        self.assertFalse(FLCellReferenceParseNode(["A$1"]).colAbsolute, "Incorrect colAbsolute for A$1")
        self.assertTrue(FLCellReferenceParseNode(["$A1"]).colAbsolute, "Incorrect colAbsolute for $A1")
        self.assertTrue(FLCellReferenceParseNode(["$A$1"]).colAbsolute, "Incorrect colAbsolute for $A$1")

        self.assertFalse(FLCellReferenceParseNode(["SheetSomething", "! ", "A1"]).colAbsolute,
                         "Incorrect colAbsolute for A1 with worksheet")
        self.assertTrue(FLCellReferenceParseNode(["SheetSomething", "! ", "$A$1"]).colAbsolute,
                         "Incorrect colAbsolute for $A$1 with worksheet")

    def testRowAbsolute(self):
        self.assertFalse(FLCellReferenceParseNode(["A1"]).rowAbsolute, "Incorrect rowAbsolute for A1")
        self.assertTrue(FLCellReferenceParseNode(["A$1"]).rowAbsolute, "Incorrect rowAbsolute for A$1")
        self.assertFalse(FLCellReferenceParseNode(["$A1"]).rowAbsolute, "Incorrect rowAbsolute for $A1")
        self.assertTrue(FLCellReferenceParseNode(["$A$1"]).rowAbsolute, "Incorrect rowAbsolute for $A$1")

        self.assertFalse(FLCellReferenceParseNode(["SheetSomething", "! ", "A1"]).rowAbsolute,
                         "Incorrect colAbsolute for A1 with worksheet")
        self.assertTrue(FLCellReferenceParseNode(["SheetSomething", "! ", "$A$1"]).rowAbsolute,
                         "Incorrect colAbsolute for $A$1 with worksheet")


    def testPlainCellName(self):
        self.assertEquals(FLCellReferenceParseNode(["A1"]).plainCellName, "A1", "Incorrect plainCellName for A1")
        self.assertEquals(FLCellReferenceParseNode(["A$1"]).plainCellName, "A1", "Incorrect plainCellName for A$1")
        self.assertEquals(FLCellReferenceParseNode(["$A1"]).plainCellName, "A1", "Incorrect plainCellName for $A1")
        self.assertEquals(FLCellReferenceParseNode(["$A$1"]).plainCellName, "A1", "Incorrect plainCellName for $A$1")

        self.assertEquals(FLCellReferenceParseNode(["SheetSomething", "! ", "A1"]).plainCellName, "A1",
                          "Incorrect plainCellName for A1 with worksheet")
        self.assertEquals(FLCellReferenceParseNode(["SheetSomething", "! ", "$A$1"]).plainCellName, "A1",
                          "Incorrect plainCellName for $A$1 with worksheet")


    def testRegisteredWithParse(self):
        "test registered with ParseNode"
        self.assertEquals(type(ParseNode.construct_node(ParseNode.FL_CELL_REFERENCE, ['A1'])), FLCellReferenceParseNode,
                          "Class is not registered with ParseNode")


    def testCellProperty(self):
        node = FLCellReferenceParseNode(["G8  "])
        self.assertEquals(node.localReference, "G8  ", "cellref wrong")

        node = FLCellReferenceParseNode(["Sheet1", "!", "G8  "])
        self.assertEquals(node.localReference, "G8  ", "cellref wrong")

        node = FLCellReferenceParseNode(["G8   "])
        node.localReference = "F5"
        self.assertEquals(node.localReference, "F5", "should discard whitespace")

        node = FLCellReferenceParseNode(["G8  "])
        node.localReference = "F5  "
        self.assertEquals(node.localReference, "F5  ", "should not pile whitespace")


    def testCanonicalise(self):
        node = FLCellReferenceParseNode(["bertie ", "!", "a1  "])
        node.canonicalise(['Bertie'])
        self.assertEquals(node.localReference, 'A1  ')
        self.assertEquals(node.worksheetReference, 'Bertie')


    def testOffset(self):
        node = FLCellReferenceParseNode(["G8  "])
        node.offset(1, 4)
        self.assertEquals(node.localReference, "H12  ", "offset didnt work")

        node = FLCellReferenceParseNode(["G8  "])
        node.offset(-7, 1)
        self.assertEquals(node.localReference, "#Invalid!  ", "offset didnt work")

        node = FLCellReferenceParseNode(["G8  "])
        node.offset(1, -8)
        self.assertEquals(node.localReference, "#Invalid!  ", "offset didnt work")

        node = FLCellReferenceParseNode(["G8  "])
        node.offset(-6, -7)
        self.assertEquals(node.localReference, "A1  ", "offset didnt work")

        node = FLCellReferenceParseNode(["$G8  "])
        node.offset(-6, -7)
        self.assertEquals(node.localReference, "$G1  ", "offset didnt work")

        node = FLCellReferenceParseNode(["G$8  "])
        node.offset(-6, -7)
        self.assertEquals(node.localReference, "A$8  ", "offset didnt work")

        node = FLCellReferenceParseNode(["$G$8  "])
        node.offset(-6, -7)
        self.assertEquals(node.localReference, "$G$8  ", "offset didnt work")

        node = FLCellReferenceParseNode(["$G$8  "])
        node.offset(-6, -7, move_absolute=True)
        self.assertEquals(node.localReference, "$A$1  ", "offset didnt work")

        node = FLCellReferenceParseNode(["ZZZ9  "])
        node.offset(1, -1)
        self.assertEquals(node.localReference, "#Invalid!  ", "offset didnt work")


    def testCoords(self):
        node = FLCellReferenceParseNode(["A2"])
        self.assertEquals(node.coords, (1, 2))

        node = FLCellReferenceParseNode(["B1"])
        self.assertEquals(node.coords, (2, 1))

