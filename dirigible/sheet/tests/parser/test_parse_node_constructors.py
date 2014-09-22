# Copyright (c) 2005-2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from sheet.parser.fl_cell_reference_parse_node import FLCellReferenceParseNode
from sheet.parser.fl_cell_range_parse_node import FLCellRangeParseNode
from sheet.parser.fl_column_reference_parse_node import FLColumnReferenceParseNode
from sheet.parser.fl_row_reference_parse_node import FLRowReferenceParseNode
from sheet.parser.parse_node import ParseNode
from sheet.parser.parse_node_constructors import (
    AndTest,
    ArgList,
    Argument,
    ArithExpr,
    Atom,
    Comparison,
    CompOperator,
    ConcatExpr,
    DictMaker,
    Expr,
    ExprList,
    Factor,
    FLCellRange,
    FLCellReference,
    FLColumnReference,
    FLRowReference,
    FLDDECall,
    FLDeletedReference,
    FLInvalidReference,
    FLNakedWorksheetReference,
    FLReference,
    FLRoot,
    FPDef,
    FPList,
    GenFor,
    GenIf,
    GenIter,
    LambDef,
    ListFor,
    ListIf,
    ListIter,
    ListMaker,
    Name,
    NotTest,
    Number,
    Power,
    ShiftExpr,
    SliceOp,
    StringLiteral,
    Subscript,
    SubscriptList,
    Term,
    Test,
    TestList,
    TestListGexp,
    Trailer,
    VarArgsList,

    ArithExpr_Term,
    Expr_ConcatExpr_ShiftExpr,
    Factor_Power_FLReference_Atom,
    Test_AndTest_NotTest_Comparison,

    ExprFromNameChild,
    ExprFromAtomChild,
    TestFromAtomChild,
    TestFromPowerChild,
)


class ParseNodeConstructorsTest(unittest.TestCase):

    def testCombinedConvenienceConstructors(self):
        randomChild = "hello"

        self.assertEquals(ParseNode(ParseNode.ARITH_EXPR,
                            [ParseNode(ParseNode.TERM, [randomChild])]),
                          ArithExpr_Term(randomChild))

        self.assertEquals(ParseNode(ParseNode.EXPR,
                            [ParseNode(ParseNode.CONCAT_EXPR,
                                [ParseNode(ParseNode.SHIFT_EXPR,
                                    [randomChild])])]),
                          Expr_ConcatExpr_ShiftExpr(randomChild))

        self.assertEquals(ParseNode(ParseNode.FACTOR,
                            [ParseNode(ParseNode.POWER,
                                [ParseNode(ParseNode.FL_REFERENCE,
                                    [ParseNode(ParseNode.ATOM,
                                        [randomChild])])])]),
                          Factor_Power_FLReference_Atom(randomChild))

        self.assertEquals(ParseNode(ParseNode.TEST,
                            [ParseNode(ParseNode.AND_TEST,
                                [ParseNode(ParseNode.NOT_TEST,
                                    [ParseNode(ParseNode.COMPARISON,
                                        [randomChild])])])]),
                          Test_AndTest_NotTest_Comparison(randomChild))

        self.assertEquals(ParseNode(ParseNode.EXPR,
                            [ParseNode(ParseNode.CONCAT_EXPR,
                                [ParseNode(ParseNode.SHIFT_EXPR,
                                    [ParseNode(ParseNode.ARITH_EXPR,
                                        [ParseNode(ParseNode.TERM,
                                            [ParseNode(ParseNode.FACTOR,
                                                [ParseNode(ParseNode.POWER,
                                                    [ParseNode(ParseNode.FL_REFERENCE,
                                                        [ParseNode(ParseNode.ATOM,
                                                            [ParseNode(ParseNode.NAME,
                                                                [randomChild])])])])])])])])])]),
                          ExprFromNameChild(randomChild))

        self.assertEquals(ParseNode(ParseNode.EXPR,
                            [ParseNode(ParseNode.CONCAT_EXPR,
                                [ParseNode(ParseNode.SHIFT_EXPR,
                                    [ParseNode(ParseNode.ARITH_EXPR,
                                        [ParseNode(ParseNode.TERM,
                                            [ParseNode(ParseNode.FACTOR,
                                                [ParseNode(ParseNode.POWER,
                                                    [ParseNode(ParseNode.FL_REFERENCE,
                                                        [ParseNode(ParseNode.ATOM,
                                                            [randomChild])])])])])])])])]),
                          ExprFromAtomChild(randomChild))

        self.assertEquals(ParseNode(ParseNode.TEST,
                            [ParseNode(ParseNode.AND_TEST,
                                [ParseNode(ParseNode.NOT_TEST,
                                    [ParseNode(ParseNode.COMPARISON,
                                        [ParseNode(ParseNode.EXPR,
                                            [ParseNode(ParseNode.CONCAT_EXPR,
                                                [ParseNode(ParseNode.SHIFT_EXPR,
                                                    [ParseNode(ParseNode.ARITH_EXPR,
                                                        [ParseNode(ParseNode.TERM,
                                                            [ParseNode(ParseNode.FACTOR,
                                                                [ParseNode(ParseNode.POWER,
                                                                    [ParseNode(ParseNode.FL_REFERENCE,
                                                                        [ParseNode(ParseNode.ATOM,
                                                                            [randomChild])])])])])])])])])])])])]),
                          TestFromAtomChild(randomChild))

        self.assertEquals(ParseNode(ParseNode.TEST,
                            [ParseNode(ParseNode.AND_TEST,
                                [ParseNode(ParseNode.NOT_TEST,
                                    [ParseNode(ParseNode.COMPARISON,
                                        [ParseNode(ParseNode.EXPR,
                                            [ParseNode(ParseNode.CONCAT_EXPR,
                                                [ParseNode(ParseNode.SHIFT_EXPR,
                                                    [ParseNode(ParseNode.ARITH_EXPR,
                                                        [ParseNode(ParseNode.TERM,
                                                            [ParseNode(ParseNode.FACTOR,
                                                                [ParseNode(ParseNode.POWER,
                                                                            [randomChild])])])])])])])])])])]),
                          TestFromPowerChild(randomChild))



    def testSimpleConvenienceConstructors(self):
        randomList = ["foo", "bar", 27]

        self.assertEquals(ParseNode(ParseNode.AND_TEST, randomList),
                          AndTest(randomList))
        self.assertEquals(ParseNode(ParseNode.ARG_LIST, randomList),
                          ArgList(randomList))
        self.assertEquals(ParseNode(ParseNode.ARGUMENT, randomList),
                          Argument(randomList))
        self.assertEquals(ParseNode(ParseNode.ARITH_EXPR, randomList),
                          ArithExpr(randomList))
        self.assertEquals(ParseNode(ParseNode.ATOM, randomList),
                          Atom(randomList))
        self.assertEquals(ParseNode(ParseNode.COMPARISON, randomList),
                          Comparison(randomList))
        self.assertEquals(ParseNode(ParseNode.COMP_OPERATOR, randomList),
                          CompOperator(randomList))
        self.assertEquals(ParseNode(ParseNode.CONCAT_EXPR, randomList),
                          ConcatExpr(randomList))
        self.assertEquals(ParseNode(ParseNode.DICT_MAKER, randomList),
                          DictMaker(randomList))
        self.assertEquals(ParseNode(ParseNode.EXPR, randomList),
                          Expr(randomList))
        self.assertEquals(ParseNode(ParseNode.EXPR_LIST, randomList),
                          ExprList(randomList))
        self.assertEquals(ParseNode(ParseNode.FACTOR, randomList),
                          Factor(randomList))
        self.assertEquals(FLCellRangeParseNode(randomList),
                          FLCellRange(randomList))
        self.assertEquals(FLCellReferenceParseNode(randomList),
                          FLCellReference(randomList))
        self.assertEquals(FLColumnReferenceParseNode(randomList),
                          FLColumnReference(randomList))
        self.assertEquals(FLRowReferenceParseNode(randomList),
                          FLRowReference(randomList))
        self.assertEquals(ParseNode(ParseNode.FL_DDE_CALL, randomList),
                          FLDDECall(randomList))
        self.assertEquals(ParseNode(ParseNode.FL_DELETED_REFERENCE, randomList),
                          FLDeletedReference(randomList))
        self.assertEquals(ParseNode(ParseNode.FL_INVALID_REFERENCE, randomList),
                          FLInvalidReference(randomList))
        self.assertEquals(ParseNode(ParseNode.FL_NAKED_WORKSHEET_REFERENCE, randomList),
                          FLNakedWorksheetReference(randomList))
        self.assertEquals(ParseNode(ParseNode.FL_REFERENCE, randomList),
                          FLReference(randomList))
        self.assertEquals(ParseNode(ParseNode.FL_ROOT, randomList),
                          FLRoot(randomList))
        self.assertEquals(ParseNode(ParseNode.FP_DEF, randomList),
                          FPDef(randomList))
        self.assertEquals(ParseNode(ParseNode.FP_LIST, randomList),
                          FPList(randomList))
        self.assertEquals(ParseNode(ParseNode.GEN_FOR, randomList),
                          GenFor(randomList))
        self.assertEquals(ParseNode(ParseNode.GEN_IF, randomList),
                          GenIf(randomList))
        self.assertEquals(ParseNode(ParseNode.GEN_ITER, randomList),
                          GenIter(randomList))
        self.assertEquals(ParseNode(ParseNode.LAMBDEF, randomList),
                          LambDef(randomList))
        self.assertEquals(ParseNode(ParseNode.LIST_FOR, randomList),
                          ListFor(randomList))
        self.assertEquals(ParseNode(ParseNode.LIST_IF, randomList),
                          ListIf(randomList))
        self.assertEquals(ParseNode(ParseNode.LIST_ITER, randomList),
                          ListIter(randomList))
        self.assertEquals(ParseNode(ParseNode.LIST_MAKER, randomList),
                          ListMaker(randomList))
        self.assertEquals(ParseNode(ParseNode.NAME, randomList),
                          Name(randomList))
        self.assertEquals(ParseNode(ParseNode.NOT_TEST, randomList),
                          NotTest(randomList))
        self.assertEquals(ParseNode(ParseNode.NUMBER, randomList),
                          Number(randomList))
        self.assertEquals(ParseNode(ParseNode.POWER, randomList),
                          Power(randomList))
        self.assertEquals(ParseNode(ParseNode.SHIFT_EXPR, randomList),
                          ShiftExpr(randomList))
        self.assertEquals(ParseNode(ParseNode.SLICE_OP, randomList),
                          SliceOp(randomList))
        self.assertEquals(ParseNode(ParseNode.STRINGLITERAL, randomList),
                          StringLiteral(randomList))
        self.assertEquals(ParseNode(ParseNode.SUBSCRIPT, randomList),
                          Subscript(randomList))
        self.assertEquals(ParseNode(ParseNode.SUBSCRIPT_LIST, randomList),
                          SubscriptList(randomList))
        self.assertEquals(ParseNode(ParseNode.TERM, randomList),
                          Term(randomList))
        self.assertEquals(ParseNode(ParseNode.TEST, randomList),
                          Test(randomList))
        self.assertEquals(ParseNode(ParseNode.TEST_LIST, randomList),
                          TestList(randomList))
        self.assertEquals(ParseNode(ParseNode.TEST_LIST_GEXP, randomList),
                          TestListGexp(randomList))
        self.assertEquals(ParseNode(ParseNode.TRAILER, randomList),
                          Trailer(randomList))
        self.assertEquals(ParseNode(ParseNode.VAR_ARGS_LIST, randomList),
                          VarArgsList(randomList))


    def testSubclasses(self):
        self.assertNotEqual(type(FLCellReferenceParseNode(["A1"])),
                            ParseNode,
                            "Subclass of ParseNode had incorrect type")

        self.assertNotEqual(type(FLColumnReferenceParseNode(['A_'])),
                            ParseNode,
                            "Subclass of ParseNode had incorrect type")

        self.assertNotEqual(type(FLRowReferenceParseNode([])),
                            ParseNode,
                            "Subclass of ParseNode had incorrect type")


    def testFLCell(self):
        "test FLCellReferenceParseNode registered"
        self.assertIn(ParseNode.FL_COLUMN_REFERENCE, ParseNode.classRegistry,
                      "FL_COLUMN_REFERENCE not registered in ParseNode class registry")
        self.assertIn(ParseNode.FL_ROW_REFERENCE, ParseNode.classRegistry,
                      "FL_ROW_REFERENCE registered in ParseNode class registry")
        self.assertIn(ParseNode.FL_CELL_REFERENCE, ParseNode.classRegistry,
                      "FL_CELL_REFERENCE not registered in ParseNode class registry")

