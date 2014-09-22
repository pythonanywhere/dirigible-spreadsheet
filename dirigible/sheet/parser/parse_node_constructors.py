# Copyright (c) 2005-2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

from sheet.parser.fl_cell_reference_parse_node import FLCellReferenceParseNode as FLCellReference
from sheet.parser.fl_cell_range_parse_node import FLCellRangeParseNode as FLCellRange
from sheet.parser.fl_column_reference_parse_node import FLColumnReferenceParseNode as FLColumnReference
from sheet.parser.fl_named_column_reference_parse_node import FLNamedColumnReferenceParseNode as FLNamedColumnReference
from sheet.parser.fl_named_row_reference_parse_node import FLNamedRowReferenceParseNode as FLNamedRowReference
from sheet.parser.fl_row_reference_parse_node import FLRowReferenceParseNode as FLRowReference
from sheet.parser.parse_node import ParseNode


def ConcatExpr(children):
    return ParseNode.construct_node(ParseNode.CONCAT_EXPR, children)

def AndTest(children):
    return ParseNode.construct_node(ParseNode.AND_TEST, children)

def ArgList(children):
    return ParseNode.construct_node(ParseNode.ARG_LIST, children)

def Argument(children):
    return ParseNode.construct_node(ParseNode.ARGUMENT, children)

def ArithExpr(children):
    return ParseNode.construct_node(ParseNode.ARITH_EXPR, children)

def Atom(children):
    return ParseNode.construct_node(ParseNode.ATOM, children)

def FLDDECall(children):
    return ParseNode.construct_node(ParseNode.FL_DDE_CALL, children)

def FLDeletedReference(children):
    return ParseNode.construct_node(ParseNode.FL_DELETED_REFERENCE, children)

def FLInvalidReference(children):
    return ParseNode.construct_node(ParseNode.FL_INVALID_REFERENCE, children)

def FLNakedWorksheetReference(children):
    return ParseNode.construct_node(ParseNode.FL_NAKED_WORKSHEET_REFERENCE, children)

def FLReference(children):
    return ParseNode.construct_node(ParseNode.FL_REFERENCE, children)

def FLRoot(children):
    return ParseNode.construct_node(ParseNode.FL_ROOT, children)

def Comparison(children):
    return ParseNode.construct_node(ParseNode.COMPARISON, children)

def CompOperator(children):
    return ParseNode.construct_node(ParseNode.COMP_OPERATOR, children)

def DictMaker(children):
    return ParseNode.construct_node(ParseNode.DICT_MAKER, children)

def Expr(children):
    return ParseNode.construct_node(ParseNode.EXPR, children)

def ExprList(children):
    return ParseNode.construct_node(ParseNode.EXPR_LIST, children)

def Factor(children):
    return ParseNode.construct_node(ParseNode.FACTOR, children)

def FPDef(children):
    return ParseNode.construct_node(ParseNode.FP_DEF, children)

def FPList(children):
    return ParseNode.construct_node(ParseNode.FP_LIST, children)

def GenFor(children):
    return ParseNode.construct_node(ParseNode.GEN_FOR, children)

def GenIf(children):
    return ParseNode.construct_node(ParseNode.GEN_IF, children)

def GenIter(children):
    return ParseNode.construct_node(ParseNode.GEN_ITER, children)

def LambDef(children):
    return ParseNode.construct_node(ParseNode.LAMBDEF, children)

def ListFor(children):
    return ParseNode.construct_node(ParseNode.LIST_FOR, children)

def ListIf(children):
    return ParseNode.construct_node(ParseNode.LIST_IF, children)

def ListIter(children):
    return ParseNode.construct_node(ParseNode.LIST_ITER, children)

def ListMaker(children):
    return ParseNode.construct_node(ParseNode.LIST_MAKER, children)

def Name(children):
    return ParseNode.construct_node(ParseNode.NAME, children)

def NotTest(children):
    return ParseNode.construct_node(ParseNode.NOT_TEST, children)

def Number(children):
    return ParseNode.construct_node(ParseNode.NUMBER, children)

def Percent(children):
    return ParseNode.construct_node(ParseNode.PERCENT, children)

def Power(children):
    return ParseNode.construct_node(ParseNode.POWER, children)

def ShiftExpr(children):
    return ParseNode.construct_node(ParseNode.SHIFT_EXPR, children)

def SliceOp(children):
    return ParseNode.construct_node(ParseNode.SLICE_OP, children)

def StringLiteral(children):
    return ParseNode.construct_node(ParseNode.STRINGLITERAL, children)

def Subscript(children):
    return ParseNode.construct_node(ParseNode.SUBSCRIPT, children)

def SubscriptList(children):
    return ParseNode.construct_node(ParseNode.SUBSCRIPT_LIST, children)

def Term(children):
    return ParseNode.construct_node(ParseNode.TERM, children)

def Test(children):
    return ParseNode.construct_node(ParseNode.TEST, children)

def TestList(children):
    return ParseNode.construct_node(ParseNode.TEST_LIST, children)

def TestListGexp(children):
    return ParseNode.construct_node(ParseNode.TEST_LIST_GEXP, children)

def Trailer(children):
    return ParseNode.construct_node(ParseNode.TRAILER, children)

def VarArgsList(children):
    return ParseNode.construct_node(ParseNode.VAR_ARGS_LIST, children)

# combinations

def ArithExpr_Term(mExprChild):
    return ArithExpr([Term([mExprChild])])

def Expr_ConcatExpr_ShiftExpr(shiftExprChild):
    return Expr([ConcatExpr([ShiftExpr([shiftExprChild])])])

def Factor_Power_FLReference_Atom(*atomChildren):
    return Factor([Power([FLReference([Atom(list(atomChildren))])])])

def Test_AndTest_NotTest_Comparison(comparisonChild):
    return Test([AndTest([NotTest([Comparison([comparisonChild])])])])

# very big combinations

def ExprFromAtomChild(atomChild):
    return Expr_ConcatExpr_ShiftExpr(
        ArithExpr_Term(Factor_Power_FLReference_Atom(atomChild)))

def ExprFromAtomChildren(atomChildren):
    return Expr_ConcatExpr_ShiftExpr(
        ArithExpr_Term(Factor_Power_FLReference_Atom(*atomChildren)))

def ExprFromNameChild(nameChild):
    return ExprFromAtomChild(Name([nameChild]))

def TestFromAtomChild(atomChild):
    return Test_AndTest_NotTest_Comparison(
        ExprFromAtomChild(atomChild))

def TestFromPowerChild(powerChild):
    return Test_AndTest_NotTest_Comparison(
        Expr_ConcatExpr_ShiftExpr(
            ArithExpr_Term(
                Factor([Power([powerChild])]))))
