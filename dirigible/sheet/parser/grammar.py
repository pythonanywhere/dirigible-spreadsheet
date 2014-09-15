# Copyright (c) 2005-2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

import sys

from sheet.utils.cell_name_utils import cell_name_to_coordinates, column_name_to_index
from sheet.utils.string_utils import get_lstripped_part, get_rstripped_part

from sheet.parser import FormulaError
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
    Percent,
    FLCellRange,
    FLCellReference,
    FLColumnReference,
    FLRowReference,
    FLDDECall,
    FLDeletedReference,
    FLInvalidReference,
    FLNakedWorksheetReference,
    FLNamedColumnReference,
    FLNamedRowReference,
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
    TestFromAtomChild,
    TestList,
    TestListGexp,
    Trailer,
    VarArgsList,
)

from sheet.parser.tokens import DOT_RE, FLCELLREFLIKENAME_RE, tokens


# Rule to allow us to have the rest of the grammar in
# the order in which it is defined in the Python 2.4.3
# codebase.
def p__root(p):
    """_root : EQUALS test"""
    p[0] = FLRoot([p[1], p[2]])


# The remainder of this file comprises the rules required to
# define a test plus a number of "virtual" rules to make the
# parser's job (and ours) easier.  NB these latter (like _root
# above) have underscores before their names to make them
# easily identifiable.

def p_varargslist(p):
    """varargslist : _partial_varargslist_starting_with_fpdef
                   | _partial_varargslist_starting_with_keyword
                   | _partial_varargslist_starting_with_star
                   | _partial_varargslist_starting_with_doublestar"""
    p[0] = VarArgsList(p[1])


def p__partial_varargslist_starting_with_doublestar(p):
    """_partial_varargslist_starting_with_doublestar : DOUBLESTAR _name"""
    p[0] = p[1:]


def p__partial_varargslist_starting_with_star(p):
    """_partial_varargslist_starting_with_star : STAR _name
                                               | STAR _name COMMA _partial_varargslist_starting_with_doublestar"""
    if len(p) == 3:
        p[0] = [p[1], p[2]]
    else:
        p[0] = [p[1], p[2], p[3]] + p[4]


def p__partial_varargslist_starting_with_keyword(p):
    """_partial_varargslist_starting_with_keyword : fpdef COLONEQUALS test
                                                  | fpdef COLONEQUALS test COMMA
                                                  | fpdef COLONEQUALS test COMMA _partial_varargslist_starting_with_doublestar
                                                  | fpdef COLONEQUALS test COMMA _partial_varargslist_starting_with_star"""
    if len(p) < 6:
        p[0] = p[1:]
    else:
        p[0] = [p[1], p[2], p[3], p[4]] + p[5]


def p__partial_varargslist_starting_with_fpdef(p):
    """_partial_varargslist_starting_with_fpdef : fpdef
                                                | fpdef COMMA
                                                | fpdef COMMA _partial_varargslist_starting_with_doublestar
                                                | fpdef COMMA _partial_varargslist_starting_with_star
                                                | fpdef COMMA _partial_varargslist_starting_with_keyword
                                                | fpdef COMMA _partial_varargslist_starting_with_fpdef"""
    if len(p) < 4:
        p[0] = p[1:]
    else:
        p[0] = [p[1], p[2]] + p[3]


def p_fpdef(p):
    """fpdef : _name
             | LEFTPAREN fplist RIGHTPAREN"""

    p[0] = FPDef(p[1:])


def p_fplist(p):
    """fplist : fpdef
              | fpdef COMMA
              | fpdef _comma_fpdefs
              | fpdef _comma_fpdefs COMMA"""
    if len(p) == 2:
        p[0] = FPList([p[1]])
    elif len(p) == 3:
        if str(p[2]).rstrip() == ",":
            p[0] = FPList([p[1], p[2]])
        else:
            p[0] = FPList([p[1]] + p[2])
    else:
        p[0] = FPList([[p[1]] + p[2] + [p[3]]])


def p__comma_fpdefs(p):
    """_comma_fpdefs : COMMA fpdef
                     | _comma_fpdefs COMMA fpdef"""
    if len(p) == 3:
        p[0] = [p[1], p[2]]
    else:
        p[0] = p[1] + [p[2], p[3]]


def p_test(p):
    """test : and_test
            | and_test _or_and_tests
            | lambdef"""
    if len(p) == 2:
        p[0] = Test([p[1]])
    else:
        p[0] = Test([p[1]] + p[2])


def p__or_and_tests(p):
    """_or_and_tests : OR and_test
                     | _or_and_tests OR and_test"""
    if len(p) == 3:
        p[0] = [p[1], p[2]]
    else:
        p[0] = p[1] + [p[2], p[3]]


def p_and_test(p):
    """and_test : not_test
                | not_test _and_not_tests"""
    if len(p) == 2:
        p[0] = AndTest([p[1]])
    else:
        p[0] = AndTest([p[1]] + p[2])


def p__and_not_tests(p):
    """_and_not_tests : AND not_test
                      | _and_not_tests AND not_test"""
    if len(p) == 3:
        p[0] = [p[1], p[2]]
    else:
        p[0] = p[1] + [p[2], p[3]]


def p_not_test(p):
    """not_test : comparison
                | NOT not_test"""
    if len(p) == 2:
        p[0] = NotTest([p[1]])
    else:
        p[0] = NotTest([p[1], p[2]])


def p_comparison(p):
    """comparison : expr
                  | expr _comp_operator_exprs"""
    if len(p) == 2:
        p[0] = Comparison([p[1]])
    else:
        p[0] = Comparison([p[1]] + p[2])


def p__comp_operator_exprs(p):
    """_comp_operator_exprs : comp_operator expr
                            | _comp_operator_exprs comp_operator expr"""
    if len(p) == 3:
        p[0] = [p[1], p[2]]
    else:
        p[0] = p[1] + [p[2], p[3]]


def p_comp_operator(p):
    """comp_operator : LESSTHAN
                     | GREATERTHAN
                     | EQUALS
                     | EQUALTO
                     | GREATEREQUAL
                     | LESSEQUAL
                     | UNEQUAL
                     | OBSOLETEUNEQUAL
                     | IS
                     | IN
                     | IS NOT
                     | NOT IN"""
    if len(p) == 2:
        p[0] = CompOperator([p[1]])
    else:
        p[0] = CompOperator([p[1] + p[2]])


def p_expr(p):
    """expr : concat_expr
            | concat_expr _or_concat_exprs"""
    if len(p) == 2:
        p[0] = Expr([p[1]])
    else:
        p[0] = Expr([p[1]] + p[2])


def p__or_concat_exprs(p):
    """_or_concat_exprs : VERTICALBAR concat_expr
                     | _or_concat_exprs VERTICALBAR concat_expr"""
    if len(p) == 3:
        p[0] = [p[1], p[2]]
    else:
        p[0] = p[1] + [p[2], p[3]]


def p_concat_expr(p):
    """concat_expr : shift_expr
                | shift_expr _ampersand_shift_exprs"""
    if len(p) == 2:
        p[0] = ConcatExpr([p[1]])
    else:
        p[0] = ConcatExpr([p[1]] + p[2])


def p__ampersand_shift_exprs(p):
    """_ampersand_shift_exprs : AMPERSAND shift_expr
                              | _ampersand_shift_exprs AMPERSAND shift_expr"""
    if len(p) == 3:
        p[0] = [p[1], p[2]]
    else:
        p[0] = p[1] + [p[2], p[3]]


def p_shift_expr(p):
    """shift_expr : arith_expr
                  | arith_expr _shift_op_arith_exprs"""
    if len(p) == 2:
        p[0] = ShiftExpr([p[1]])
    else:
        p[0] = ShiftExpr([p[1]]+ p[2])


def p__shift_op_arith_exprs(p):
    """_shift_op_arith_exprs : LEFTSHIFT arith_expr
                             | RIGHTSHIFT arith_expr
                             | _shift_op_arith_exprs LEFTSHIFT arith_expr
                             | _shift_op_arith_exprs RIGHTSHIFT arith_expr"""
    if len(p) == 3:
        p[0] = [p[1], p[2]]
    else:
        p[0] = p[1] + [p[2], p[3]]


def p_arith_expr(p):
    """arith_expr : term
                  | term _a_op_terms"""
    if len(p) == 2:
        p[0] = ArithExpr([p[1]])
    else:
        p[0] = ArithExpr([p[1]] + p[2])


def p__a_op_terms(p):
    """_a_op_terms : PLUS term
                   | MINUS term
                   | _a_op_terms PLUS term
                   | _a_op_terms MINUS term"""
    if len(p) == 3:
        p[0] = [p[1], p[2]]
    else:
        p[0] = p[1] + [p[2], p[3]]


def p_term(p):
    """term : percent
            | percent _m_op_factors"""
    if len(p) == 2:
        p[0] = Term([p[1]])
    else:
        p[0] = Term([p[1]] + p[2])


def p__m_op_factors(p):
    """_m_op_factors : STAR percent
                      | SLASH percent
                      | DOUBLESLASH percent
                      | MOD_ITERP percent
                      | _m_op_factors STAR percent
                      | _m_op_factors SLASH percent
                      | _m_op_factors DOUBLESLASH percent
                      | _m_op_factors MOD_ITERP percent"""
    if len(p) == 3:
        p[0] = [p[1], p[2]]
    else:
        p[0] = p[1] + [p[2], p[3]]

def p_percent(p):
    """percent : factor
               | percent PERCENT"""
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = Percent(p[1:])

def p_factor(p):
    """factor : power
              | MINUS factor
              | PLUS factor
              | TILDE factor"""
    p[0] = Factor(p[1:])


def p_power(p):
    """power : fl_reference
             | fl_reference DOUBLESTAR factor
             | fl_reference CIRCUMFLEX factor"""
    if len(p) == 2:
        p[0] = Power([p[1]])
    else:
        p[0] = Power([p[1], p[2], p[3]])


def p_atom(p):
    """atom : _number
            | stringliteral
            | _name
            | BACKWARDQUOTE testlist1 BACKWARDQUOTE
            | LEFTPAREN RIGHTPAREN
            | LEFTPAREN testlist_gexp RIGHTPAREN
            | LEFTBRACKET RIGHTBRACKET
            | LEFTBRACKET listmaker RIGHTBRACKET
            | LEFTBRACE RIGHTBRACE
            | LEFTBRACE dictmaker RIGHTBRACE"""
    p[0] = Atom(p[1:])


def p_listmaker(p):
    """listmaker : testlist
                 | test list_for"""
    if len(p) == 2:
        p[0] = ListMaker(p[1].children)
    else:
        p[0] = ListMaker([p[1], p[2]])


def p_testlist_gexp(p):
    """testlist_gexp : testlist
                     | test gen_for"""
    if len(p) == 2:
        p[0] = TestListGexp(p[1].children)
    else:
        p[0] = TestListGexp([p[1], p[2]])


def p_lambdef(p):
    """lambdef : LAMBDA LITTLEARROW test
               | LAMBDA varargslist LITTLEARROW test"""
    p[0] = LambDef(p[1:])


def p_trailer(p):
    """trailer : DOT _name
               | DOT FLCELLREFLIKENAME
               | LEFTPAREN RIGHTPAREN
               | LEFTPAREN arglist RIGHTPAREN
               | LEFTBRACKET subscriptlist RIGHTBRACKET"""

    def __ConvertCellRefLikeNameToNameNode(p):
        if len(p) == 3 and DOT_RE.match(p[1]) and isinstance(p[2], basestring) and FLCELLREFLIKENAME_RE.match(p[2]):
            return Name([p[2]])
        else:
            return p[2]

    p[2] = __ConvertCellRefLikeNameToNameNode(p)
    p[0] = Trailer(p[1:])


def p__trailers(p):
    """_trailers : trailer
                 | _trailers trailer"""
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]


def p_subscriptlist(p):
    """subscriptlist : subscript
                     | subscript COMMA
                     | subscript _comma_subscripts
                     | subscript _comma_subscripts COMMA"""
    if len(p) == 2:
        p[0] = SubscriptList([p[1]])
    elif len(p) == 3:
        if str(p[2]).rstrip() == ",":
            p[0] = SubscriptList([p[1], p[2]])
        else:
            p[0] = SubscriptList([p[1]] + p[2])
    else:
        p[0] = SubscriptList([p[1]] + p[2] + [p[3]])


def p__comma_subscripts(p):
    """_comma_subscripts : COMMA subscript
                         | _comma_subscripts COMMA subscript"""
    if len(p) == 3:
        p[0] = [p[1], p[2]]
    else:
        p[0] = p[1] + [p[2], p[3]]


def p_subscript(p):
    """subscript : _simple_subscript
                 | _complex_subscript"""
    p[0] = p[1]


def p__simple_subscript(p):
    """_simple_subscript : ELLIPSIS
                         | test"""
    p[0] = Subscript([p[1]])


def p__complex_subscript(p):
    """_complex_subscript : _short_slice
                          | _short_slice sliceop"""
    if len(p) == 2:
        p[0] = Subscript(p[1])
    else:
        p[0] = Subscript(p[1] + [p[2]])


def p__short_slice(p):
    """_short_slice : LITTLEARROW
                    | _lower_bound LITTLEARROW
                    | LITTLEARROW _upper_bound
                    | _lower_bound LITTLEARROW _upper_bound"""
    p[0] = p[1:]


def p__lower_bound(p):
    """_lower_bound : test"""
    p[0] = p[1]


def p__upper_bound(p):
    """_upper_bound : test"""
    p[0] = p[1]


def p_sliceop(p):
    """sliceop : LITTLEARROW
               | LITTLEARROW test"""
    p[0] = SliceOp(p[1:])


def p_exprlist(p):
    """exprlist : expr
                | expr COMMA
                | expr _comma_exprs
                | expr _comma_exprs COMMA"""
    if len(p) == 2:
        p[0] = ExprList([p[1]])
    elif len(p) == 3:
        if str(p[2]).rstrip() == ",":
            p[0] = ExprList([p[1], p[2]])
        else:
            p[0] = ExprList([p[1]] + p[2])
    else:
        p[0] = ExprList([p[1]] + p[2] + [p[3]])


def p__comma_exprs(p):
    """_comma_exprs : COMMA expr
                    | _comma_exprs COMMA expr"""
    if len(p) == 3:
        p[0] = [p[1], p[2]]
    else:
        p[0] = p[1] + [p[2], p[3]]


def p_testlist(p):
    """testlist : test
                | test COMMA
                | test _comma_tests
                | test _comma_tests COMMA"""
    if len(p) == 2:
        p[0] = TestList([p[1]])
    elif len(p) == 3:
        if str(p[2]).rstrip() == ",":
            p[0] = TestList([p[1], p[2]])
        else:
            p[0] = TestList([p[1]] + p[2])
    else:
        p[0] = TestList([p[1]] + p[2] + [p[3]])


def p__comma_tests(p):
    """_comma_tests : COMMA test
                    | _comma_tests COMMA test"""
    if len(p) == 3:
        p[0] = [p[1], p[2]]
    else:
        p[0] = p[1] + [p[2], p[3]]


def p_testlist_safe(p):
    """testlist_safe : test
                     | test _comma_tests"""

    if len(p) == 2:
        p[0] = TestList([p[1]])
    elif len(p) == 3:
        p[0] = TestList([p[1]] + p[2])
    else:
        p[0] = TestList([p[1]] + p[2] + [p[3]])


def p_dictmaker(p):
    """dictmaker : _key_value_pair
                 | _key_value_pair COMMA
                 | _key_value_pair _comma_key_value_pairs
                 | _key_value_pair _comma_key_value_pairs COMMA"""
    if len(p) == 2:
        p[0] = DictMaker(p[1])
    elif len(p) == 3:
        if str(p[2]).rstrip() == ",":
            p[0] = DictMaker(p[1] + [p[2]])
        else:
            p[0] = DictMaker(p[1] + p[2])
    else:
        p[0] = DictMaker(p[1] + p[2] + [p[3]])


def p__key_value_pair(p):
    """_key_value_pair : test LITTLEARROW test"""
    p[0] = [p[1], p[2], p[3]]


def p__comma_key_value_pairs(p):
    """_comma_key_value_pairs : COMMA _key_value_pair
                              | _comma_key_value_pairs COMMA _key_value_pair"""
    if len(p) == 3:
        p[0] = [p[1]] + p[2]
    else:
        p[0] = p[1] + [p[2]] + p[3]


def p_arglist(p):
    """arglist : _partial_arglist_starting_with_argument
               | _partial_arglist_starting_with_keyword
               | _partial_arglist_starting_with_star
               | _partial_arglist_starting_with_doublestar"""
    p[0] = ArgList(p[1])


def p__partial_arglist_starting_with_doublestar(p):
    """_partial_arglist_starting_with_doublestar : DOUBLESTAR test"""
    p[0] = [p[1], p[2]]


def p__partial_arglist_starting_with_star(p):
    """_partial_arglist_starting_with_star : STAR test
                                           | STAR test COMMA _partial_arglist_starting_with_doublestar"""
    if len(p) == 3:
        p[0] = [p[1], p[2]]
    else:
        p[0] = [p[1], p[2], p[3]] + p[4]


def p__partial_arglist_starting_with_keyword(p):
    """_partial_arglist_starting_with_keyword : _keyword_argument
                                              | _keyword_argument COMMA _partial_arglist_starting_with_doublestar
                                              | _keyword_argument COMMA _partial_arglist_starting_with_star
                                              | _keyword_argument COMMA _partial_arglist_starting_with_keyword"""
    if len(p) < 4:
        p[0] = p[1:]
    else:
        p[0] = [p[1], p[2]] + p[3]


def p__partial_arglist_starting_with_argument(p):
    """_partial_arglist_starting_with_argument : COMMA
                                               | COMMA _partial_arglist_starting_with_doublestar
                                               | COMMA _partial_arglist_starting_with_star
                                               | COMMA _partial_arglist_starting_with_keyword
                                               | COMMA _partial_arglist_starting_with_argument
                                               | argument
                                               | argument COMMA
                                               | argument COMMA _partial_arglist_starting_with_doublestar
                                               | argument COMMA _partial_arglist_starting_with_star
                                               | argument COMMA _partial_arglist_starting_with_keyword
                                               | argument COMMA _partial_arglist_starting_with_argument"""
    if len(p) < 4:
        if not isinstance(p[1], ParseNode):
            p[0] = [Argument([TestFromAtomChild(Name(['']))]), p[1]]
            if len(p) > 2:
                p[0] += p[2]
        else:
            p[0] = p[1:]
    else:
        p[0] = [p[1], p[2]] + p[3]


def p_argument(p):
    """argument : test
                | test gen_for"""
    p[0] = Argument(p[1:])


def p__keyword_argument(p):
    """_keyword_argument : test COLONEQUALS test"""
    p[0] = Argument(p[1:])


def p_list_iter(p):
    """list_iter : list_for
                 | list_if"""
    p[0] = ListIter([p[1]])


def p_list_for(p):
    """list_for : FOR exprlist IN testlist_safe
                | FOR exprlist IN testlist_safe list_iter"""
    p[0] = ListFor(p[1:])


def p_list_if(p):
    """list_if : IF test
               | IF test list_iter"""
    p[0] = ListIf(p[1:])


def p_gen_iter(p):
    """gen_iter : gen_for
                | gen_if"""
    p[0] = GenIter([p[1]])


def p_gen_for(p):
    """gen_for : FOR exprlist IN test
               | FOR exprlist IN test gen_iter"""
    p[0] = GenFor(p[1:])


def p_gen_if(p):
    """gen_if : IF test
              | IF test gen_iter"""
    p[0] = GenIf(p[1:])


def p_testlist1(p):
    """testlist1 : test
                 | test _comma_tests"""
    if len(p) == 2:
        p[0] = TestList([p[1]])
    else:
        p[0] = TestList([p[1]] + p[2])


def p__name(p):
    """_name : NAME"""
    p[0] = Name([p[1]])


def p__number(p):
    """_number : _integer
               | _float
               | _imaginary"""
    p[0] = Number([p[1]])


def p__imaginary(p):
    """_imaginary  : IMAGINARY"""
    p[0] = p[1]


def p__float(p):
    """_float : FLOATNUMBER"""
    p[0] = p[1]


def p__integer(p):
    """_integer : OCTINTEGER
                | DECINTEGER
                | HEXINTEGER"""
    p[0] = p[1]


def p_stringliteral(p):
    """stringliteral : _shortstring
                     | _longstring
                     | stringliteral _shortstring
                     | stringliteral _longstring"""
    if len(p) == 2:
        p[0] = StringLiteral([p[1]])
    else:
        p[0] = StringLiteral(p[1].children + [p[2]])


def p__shortstring(p):
    """_shortstring : SSHORTSTRING
                    | DSHORTSTRING"""
    p[0] = p[1]


def p__longstring(p):
    """_longstring : DLONGSTRING
                   | SLONGSTRING"""
    p[0] = p[1]


# Extensions to Python:

def FixFunction(p):
    p[0] = [Atom([Name([str(p[1])])]), Trailer(p[2:])]

def p_iserror_function(p):
    """iserror_function : ISERROR LEFTPAREN argument RIGHTPAREN"""
    FixFunction(p)


def p_iserr_function(p):
    """iserr_function : ISERR LEFTPAREN argument RIGHTPAREN"""
    FixFunction(p)


def p_if_function(p):
    """if_function : IF LEFTPAREN argument COMMA argument COMMA argument RIGHTPAREN
                   | IF LEFTPAREN argument COMMA argument COMMA RIGHTPAREN
                   | IF LEFTPAREN argument COMMA argument RIGHTPAREN"""
    FixFunction(p)


def p_and_function(p):
    """and_function : AND LEFTPAREN arglist RIGHTPAREN"""
    FixFunction(p)


def p_or_function(p):
    """or_function : OR LEFTPAREN arglist RIGHTPAREN"""
    FixFunction(p)


def p_fl_reference(p):
    """fl_reference : atom
                    | atom _trailers
                    | and_function
                    | or_function
                    | if_function
                    | if_function _trailers
                    | iserr_function
                    | iserror_function
                    | fl_cell_range
                    | fl_cell_range _trailers
                    | fl_cell_reference
                    | fl_cell_reference _trailers
                    | fl_column_reference
                    | fl_column_reference _trailers
                    | fl_row_reference
                    | fl_row_reference _trailers
                    | fl_named_column_reference
                    | fl_named_column_reference _trailers
                    | fl_named_row_reference
                    | fl_named_row_reference _trailers
                    | fl_naked_worksheet_reference
                    | fl_naked_worksheet_reference _trailers
                    | fl_deleted_reference
                    | fl_invalid_reference
                    | fl_dde_call"""
    if isinstance(p[1], ParseNode):
        firstChildren = [p[1]]
    else:
        firstChildren = p[1]
    if len(p) == 2:
        p[0] = FLReference(firstChildren)
    elif len(p) == 3:
        p[0] = FLReference(firstChildren + p[2])


def p_fl_dde_call(p):
    """fl_dde_call : SSHORTSTRING EXCLAMATION SSHORTSTRING"""
    p[0] = FLDDECall(p[1:])


def p_fl_cell_range(p):
    """fl_cell_range : fl_cell_reference COLON fl_cell_reference
                     | fl_cell_reference COLON fl_deleted_reference
                     | fl_deleted_reference COLON fl_cell_reference
                     | fl_deleted_reference COLON fl_deleted_reference
                     | fl_cell_reference COLON fl_invalid_reference
                     | fl_invalid_reference COLON fl_cell_reference
                     | fl_invalid_reference COLON fl_invalid_reference"""
    types = [ParseNode.FL_CELL_REFERENCE, ParseNode.FL_DELETED_REFERENCE, ParseNode.FL_INVALID_REFERENCE]
    if p[1].type not in types:
        raise FormulaError("Error in formula at position %d: unexpected '%s'" % (p.lexer.lexpos - len(p[1].flatten()) - len(p[3].flatten()) - len(p[2]) - 1, p[1].flatten()))
    if p[3].type not in types:
        raise FormulaError("Error in formula at position %d: unexpected '%s'" % (p.lexer.lexpos - len(p[3].flatten()) - 1, p[3].flatten()))

    if p[1].type == ParseNode.FL_CELL_REFERENCE and p[3].type == ParseNode.FL_CELL_REFERENCE:
        if len(p[1].children) == 3 and len(p[3].children) == 1:
            p[3].children[:0] = p[1].children[:2]

    p[0] = FLCellRange([p[1], p[2], p[3]])


def GetWorksheetNameFromPotentialNakedWorksheetReference(nameOrNWRef):
    worksheetName = nameOrNWRef
    if isinstance(nameOrNWRef, ParseNode):
        worksheetName = nameOrNWRef.children[1]
        worksheetName += get_rstripped_part(nameOrNWRef.children[2])
    return worksheetName


def _interpretHorribleFLReferenceMess(p, simpleInterpreter):
    # this is used to deal with the half-dozen ways that valid cell, col, or row references may have been tokenised
    p_1 = p[1]
    if len(p) == 2:
        if '!' not in p_1: #simple reference
            p[0] = simpleInterpreter(p_1, []) or Atom([Name([p_1])])
            return
        else:
            worksheetName, cellName = p_1.rsplit('!', 1)
            exclamationMark = '!' + get_lstripped_part(cellName)
            cellName = cellName.lstrip()
    else:
        worksheetName = GetWorksheetNameFromPotentialNakedWorksheetReference(p_1)
        exclamationMark = p[2]
        cellName = p[3]

    result = simpleInterpreter(cellName, [worksheetName, exclamationMark])
    if result is None:
        raise FormulaError("Error in formula at position %d: unexpected '%s'" % (p.lexer.lexpos - len(cellName) - 1, cellName))
    else:
        p[0] = result


def _asCellReference(cellName, worksheetInfo):
    if cell_name_to_coordinates(cellName):
        worksheetInfo.append(cellName)
        return FLCellReference(worksheetInfo)


def p_fl_cell_reference(p):
    """fl_cell_reference : FLCELLREFLIKENAME
                         | LONGCELLREFERENCE
                         | FLCELLREFLIKENAME EXCLAMATION FLCELLREFLIKENAME
                         | FLCOLUMNREFLIKENAME EXCLAMATION FLCELLREFLIKENAME
                         | FLROWREFLIKENAME  EXCLAMATION FLCELLREFLIKENAME
                         | NAME EXCLAMATION FLCELLREFLIKENAME
                         | fl_naked_worksheet_reference EXCLAMATION FLCELLREFLIKENAME"""
    _interpretHorribleFLReferenceMess(p, _asCellReference)


def _asColumnReference(columnName, worksheetInfo):
    worksheetInfo.append(columnName)
    columnReference = FLColumnReference(worksheetInfo)
    if column_name_to_index(columnReference.plainColumnName):
        return columnReference


def p_fl_column_reference(p):
    """fl_column_reference : FLCOLUMNREFLIKENAME
                           | LONGCOLUMNREFERENCE
                           | FLCELLREFLIKENAME EXCLAMATION FLCOLUMNREFLIKENAME
                           | FLCOLUMNREFLIKENAME EXCLAMATION FLCOLUMNREFLIKENAME
                           | FLROWREFLIKENAME EXCLAMATION FLCOLUMNREFLIKENAME
                           | NAME EXCLAMATION FLCOLUMNREFLIKENAME
                           | fl_naked_worksheet_reference EXCLAMATION FLCOLUMNREFLIKENAME"""
    _interpretHorribleFLReferenceMess(p, _asColumnReference)


def _asRowReference(rowName, worksheetInfo):
    worksheetInfo.append(rowName)
    rowReference = FLRowReference(worksheetInfo)
    rowIndex = int(rowReference.plainRowName)
    if rowIndex < sys.maxint:
        return rowReference


def p_fl_row_reference(p):
    """fl_row_reference : FLROWREFLIKENAME
                        | LONGROWREFERENCE
                        | FLCELLREFLIKENAME EXCLAMATION FLROWREFLIKENAME
                        | FLCOLUMNREFLIKENAME EXCLAMATION FLROWREFLIKENAME
                        | FLROWREFLIKENAME  EXCLAMATION FLROWREFLIKENAME
                        | NAME EXCLAMATION FLROWREFLIKENAME
                        | fl_naked_worksheet_reference EXCLAMATION FLROWREFLIKENAME"""
    _interpretHorribleFLReferenceMess(p, _asRowReference)


def _asNamedColumnReference(columnName, worksheetInfo):
    worksheetInfo.append(columnName)
    return FLNamedColumnReference(worksheetInfo)


def p_fl_named_column_reference(p):
    """fl_named_column_reference : FLNAMEDCOLUMNREFERENCE
                                 | LONGNAMEDCOLUMNREFERENCE
                                 | FLCELLREFLIKENAME EXCLAMATION FLNAMEDCOLUMNREFERENCE
                                 | FLCOLUMNREFLIKENAME EXCLAMATION FLNAMEDCOLUMNREFERENCE
                                 | FLROWREFLIKENAME EXCLAMATION FLNAMEDCOLUMNREFERENCE
                                 | NAME EXCLAMATION FLNAMEDCOLUMNREFERENCE
                                 | fl_naked_worksheet_reference EXCLAMATION FLNAMEDCOLUMNREFERENCE"""
    _interpretHorribleFLReferenceMess(p, _asNamedColumnReference)


def _asNamedRowReference(rowName, worksheetInfo):
    worksheetInfo.append(rowName)
    return FLNamedRowReference(worksheetInfo)


def p_fl_named_row_reference(p):
    """fl_named_row_reference : FLNAMEDROWREFERENCE
                              | LONGNAMEDROWREFERENCE
                              | FLCELLREFLIKENAME EXCLAMATION FLNAMEDROWREFERENCE
                              | FLCOLUMNREFLIKENAME EXCLAMATION FLNAMEDROWREFERENCE
                              | FLROWREFLIKENAME EXCLAMATION FLNAMEDROWREFERENCE
                              | NAME EXCLAMATION FLNAMEDROWREFERENCE
                              | fl_naked_worksheet_reference EXCLAMATION FLNAMEDROWREFERENCE"""
    _interpretHorribleFLReferenceMess(p, _asNamedRowReference)


def p_fl_deleted_reference(p):
    """fl_deleted_reference : FLDELETEDREFERENCE
                            | LONGDELETEDREFERENCE
                            | FLCELLREFLIKENAME EXCLAMATION FLDELETEDREFERENCE
                            | FLCOLUMNREFLIKENAME EXCLAMATION FLDELETEDREFERENCE
                            | FLROWREFLIKENAME EXCLAMATION FLDELETEDREFERENCE
                            | NAME EXCLAMATION FLDELETEDREFERENCE
                            | fl_naked_worksheet_reference EXCLAMATION FLDELETEDREFERENCE"""
    if len(p) == 2:
        if p[1].count('!') == 1:
            p[0] = FLDeletedReference([p[1]])
        else:
            worksheetReference, deletedReference = p[1].rsplit('#', 1)
            worksheetName, exclamationWhitespace = worksheetReference.rsplit('!', 1)
            p[0] = FLDeletedReference([worksheetName, '!' + exclamationWhitespace, '#' + deletedReference])
    else:
        worksheetName = GetWorksheetNameFromPotentialNakedWorksheetReference(p[1])
        p[0] = FLDeletedReference([worksheetName, p[2], p[3]])


def p_fl_invalid_reference(p):
    """fl_invalid_reference : FLINVALIDREFERENCE
                            | LONGINVALIDREFERENCE
                            | FLCELLREFLIKENAME EXCLAMATION FLINVALIDREFERENCE
                            | FLCOLUMNREFLIKENAME EXCLAMATION FLINVALIDREFERENCE
                            | FLROWREFLIKENAME EXCLAMATION FLINVALIDREFERENCE
                            | NAME EXCLAMATION FLINVALIDREFERENCE
                            | fl_naked_worksheet_reference EXCLAMATION FLINVALIDREFERENCE"""
    if len(p) == 2:
        if p[1].count('!') == 1:
            p[0] = FLInvalidReference([p[1]])
        else:
            worksheetReference, invalidReference = p[1].rsplit('#', 1)
            worksheetName, exclamationWhitespace = worksheetReference.rsplit('!', 1)
            p[0] = FLInvalidReference([worksheetName, '!' + exclamationWhitespace, '#' + invalidReference])
    else:
        worksheetName = GetWorksheetNameFromPotentialNakedWorksheetReference(p[1])
        p[0] = FLInvalidReference([worksheetName, p[2], p[3]])


def p_fl_naked_worksheet_reference(p):
    """fl_naked_worksheet_reference : LESSTHAN NAME GREATERTHAN
                                    | LESSTHAN FLCELLREFLIKENAME GREATERTHAN
                                    | FLNAKEDWORKSHEETREFERENCE"""
    if len(p) == 2:
        name, greaterThanWhitespace = p[1].rsplit(">", 1)
        greaterThan = ">" + greaterThanWhitespace
        lessThanWhitespace = get_lstripped_part(name[1:])
        lessThan = "<" + lessThanWhitespace
        name = name[1:].lstrip()
        p[0] = FLNakedWorksheetReference([lessThan, name, greaterThan])
    else:
        p[0] = FLNakedWorksheetReference([p[1], p[2], p[3]])


def p_error(p):
    if not p:
        # EOF reached
        raise FormulaError("Possibly incomplete formula")

    raise FormulaError("Error in formula at position %d: unexpected '%s'" % (p.lexpos + 1, p.value))
