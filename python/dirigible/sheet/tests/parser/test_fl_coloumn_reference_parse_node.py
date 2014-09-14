# Copyright (c) 2005-2009 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from sheet.parser.parse_node import ParseNode
from sheet.parser.fl_column_reference_parse_node import FLColumnReferenceParseNode
from sheet.parser.fl_reference_parse_node import FLReferenceParseNode

class FLColumnReferenceParseNodeTest(unittest.TestCase):

    def testConstructor(self):
        flColumnReference = FLColumnReferenceParseNode(["A_"])
        self.assertTrue(isinstance(flColumnReference, FLReferenceParseNode), 'should be a parse node')
        self.assertEquals(flColumnReference.type, ParseNode.FL_COLUMN_REFERENCE, "Node was of the wrong type")
        self.assertEquals(flColumnReference.children, ["A_"], "Node had the wrong children")


    def testStr(self):
        node = FLColumnReferenceParseNode(["a_"])
        self.assertEquals(str(node), "<FLColumnReferenceParseNode type=\"FL_COLUMN_REFERENCE\" children=['a_']>", "Wrong string representation")


    def testIsAbsolute(self):
        self.assertFalse(FLColumnReferenceParseNode(["A_"]).isAbsolute, "Incorrect isAbsolute for A_")
        self.assertTrue(FLColumnReferenceParseNode(["$A_"]).isAbsolute, "Incorrect isAbsolute for $A_")
        self.assertTrue(FLColumnReferenceParseNode([" $A_"]).isAbsolute, "Incorrect isAbsolute for  $A_")

        self.assertFalse(FLColumnReferenceParseNode(["SheetSomething", "! ", "A_"]).isAbsolute,
                         "Incorrect isAbsolute for A_ with worksheet")
        self.assertTrue(FLColumnReferenceParseNode(["SheetSomething", "! ", "$A_"]).isAbsolute,
                         "Incorrect isAbsolute for $A_ with worksheet")


    def testPlainColumnName(self):
        self.assertEquals(FLColumnReferenceParseNode(["A_"]).plainColumnName, "A", "Incorrect plainColumnName for A_")
        self.assertEquals(FLColumnReferenceParseNode(["$A_"]).plainColumnName, "A", "Incorrect plaiaColumName for $A_")

        self.assertEquals(FLColumnReferenceParseNode(["SheetSomething", "! ", "A_"]).plainColumnName, "A",
                          "Incorrect plainColumnName for A_ with worksheet")
        self.assertEquals(FLColumnReferenceParseNode(["SheetSomething", "! ", "$A_"]).plainColumnName, "A",
                          "Incorrect plainColumnName for $A_ with worksheet")


    def testRegisteredWithParse(self):
        "test registered with ParseNode"
        self.assertEquals(type(ParseNode.construct_node(ParseNode.FL_COLUMN_REFERENCE, ['A_'])), FLColumnReferenceParseNode,
                          "Class is not registered with ParseNode")


    def testSettingPlainColumnName(self):
        column = FLColumnReferenceParseNode(["A_ "])
        column.plainColumnName = "C"
        self.assertEquals(column.localReference, "C_ ")

        column = FLColumnReferenceParseNode(["$A_ "])
        column.plainColumnName = "C"
        self.assertEquals(column.localReference, "$C_ ")


    def testColumnReferenceProperty(self):
        self.assertEquals(FLColumnReferenceParseNode(["A_"]).localReference, "A_")
        self.assertEquals(FLColumnReferenceParseNode(["ws1", "!", "A_"]).localReference, "A_")


    def testSettingColumnProperty(self):
        column = FLColumnReferenceParseNode(["A_ "])
        column.localReference = "12345"
        self.assertEquals(column.localReference, "12345")

        column = FLColumnReferenceParseNode(["$A_ "])
        column.localReference = "#Deleted!"
        self.assertEquals(column.localReference, "#Deleted!")


    def testColIndexProperty(self):
        self.assertEquals(FLColumnReferenceParseNode(["D_"]).colIndex, 4)
        self.assertEquals(FLColumnReferenceParseNode(["$B_"]).colIndex, 2)


    def testCanonicalise(self):
        node = FLColumnReferenceParseNode(["sheet1  ", "!", "$d_"])
        node.canonicalise(['Sheet1'])
        self.assertEquals(node.localReference, '$D_')
        self.assertEquals(node.worksheetReference, 'Sheet1')


    def testOffset(self):
        node = FLColumnReferenceParseNode(['B_ '])
        node.offset(0, 1000)
        self.assertEquals(node.localReference, 'B_ ')
        node.offset(1, -1000)
        self.assertEquals(node.localReference, 'C_ ')
        node.offset(-2, 0)
        self.assertEquals(node.localReference, 'A_ ')
        node.offset(-1, 1337)
        self.assertEquals(node.localReference, '#Invalid! ')


    def testOffsetAbsoluteRefs(self):
        node = FLColumnReferenceParseNode(['$C_ '])
        node.offset(54, 0xDEADBEEF)
        self.assertEquals(node.localReference, '$C_ ')

        node.offset(4, 0xDEADBEEF, moveAbsolute=True)
        self.assertEquals(node.localReference, '$G_ ')


    def testCoords(self):
        node = FLColumnReferenceParseNode(['$A_ '])
        self.assertEquals(node.coords, (1, 0))

        node = FLColumnReferenceParseNode(['B_ '])
        self.assertEquals(node.coords, (2, 0))

