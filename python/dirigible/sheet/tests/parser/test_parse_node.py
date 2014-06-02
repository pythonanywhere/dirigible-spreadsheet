# Copyright (c) 2005-2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from dirigible.sheet.parser.parse_node import ParseNode


def Expr(children):
    return ParseNode.construct_node(ParseNode.EXPR, children)

def Name(children):
    return ParseNode.construct_node(ParseNode.NAME, children)

def ShiftExpr(children):
    return ParseNode.construct_node(ParseNode.SHIFT_EXPR, children)


class ParseNodeTest(unittest.TestCase):

    def testStr(self):
        node = Expr([Name(["a"])])
        self.assertEquals(str(node), "<ParseNode type=\"EXPR\" children=[<ParseNode type=\"NAME\" children=['a']>]>", "Wrong string representation")


    def testEquals(self):
        node1 = Expr([Name(["a"])])
        node2 = Expr([Name(["a"])])
        self.assertTrue(node1 == node2, "Nodes expected to be equal were not")
        self.assertFalse(node1 != node2, "Nodes not expected to be unequal were")

        node3 = Expr([Name(["b"])])
        self.assertFalse(node2 == node3, "Nodes not expected to be equal were")
        self.assertTrue(node2 != node3, "Nodes expected to be unequal were not")

        node4 = Expr([Name(5)])
        self.assertFalse(node3 == None, "Nodes not expected to be equal were (None)")
        self.assertFalse(node3 == node4, "Nodes not expected to be equal were (unsized)")
        self.assertFalse(node4 == node3, "Nodes not expected to be equal were (unsized)")
        self.assertFalse(node4 == "hello", "Nodes not expected to be equal were (type)")

    def testFlatten(self):
        node = Expr([None])
        self.assertEquals(node.flatten(), "", "Unexpected flattening")

        node = Expr([Name(["a"])])
        self.assertEquals(node.flatten(), "a", "Unexpected flattening")

        node = Expr([Name(["a "]), "or ", ShiftExpr([Name(["b "]), "<< ", Name(["c"])])])
        self.assertEquals(node.flatten(), "a or b << c", "Unexpected flattening")


    def testFlattenWithUnicode(self):
        node = Expr([Name([u"\u20ac"])])
        self.assertEquals(node.flatten(), u"\u20ac", "unexpected flattening")


    def testFlattenHandlesSubclassed(self):
        "test flatten handles subclassed parse nodes"

        class ParseNodeSubclass(ParseNode):
            pass

        node = Expr([ParseNodeSubclass(ParseNode.NAME, ["Thing"])])

        self.assertEquals(node.flatten(), "Thing", "Thing should have been thing. Merry Christmas!")


    def testParseNodeShould(self):
        "test ParseNode should allow registering of node classes"
        class CustomParseNode(ParseNode):
            def __init__(self, children):
                ParseNode.__init__(self, "CUSTOM_NODE_TYPE", children)

        ParseNode.register_node_type("CUSTOM_NODE_TYPE", CustomParseNode)
        try:

            node = ParseNode.construct_node("CUSTOM_NODE_TYPE", [])
            self.assertEquals(type(node), CustomParseNode, "ParseNode.construct_node didn't dispatch to CustomParseNode")
            self.assertEquals(node.type, "CUSTOM_NODE_TYPE", "Wrong type attribute")
            self.assertEquals(node.children, [], "Wrong children")


            node = ParseNode.construct_node("FISH BOWL", ["gox blamp"])
            self.assertEquals(type(node), ParseNode, "ParseNode.construct_node didn't fall back to ParseNode")
            self.assertEquals(node.type, "FISH BOWL", "Wrong type attribute")
            self.assertEquals(node.children, ["gox blamp"], "Wrong children")


            self.assertIsNotNone(ParseNode.classRegistry, "ParseNode didn't have a class registry")
        finally:
            del ParseNode.classRegistry["CUSTOM_NODE_TYPE"]

