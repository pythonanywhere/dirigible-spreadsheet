# Copyright (c) 2005-2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from itertools import takewhile
import os
from threading import Lock, Thread
import time

from sheet.parser import FormulaError
from sheet.parser.parser import parse
from sheet.parser.parse_node import ParseNode
from sheet.parser.parse_node_constructors import (
    AndTest,
    ArgList,
    Argument,
    ArithExpr,
    Atom,
    ConcatExpr,
    FLCellRange,
    FLCellReference,
    FLDDECall,
    FLDeletedReference,
    FLInvalidReference,
    FLNakedWorksheetReference,
    FLReference,
    FLRoot,
    Comparison,
    CompOperator,
    DictMaker,
    Expr,
    ExprList,
    Factor,
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
    Percent,
    Power,
    ShiftExpr,
    StringLiteral,
    Subscript,
    SubscriptList,
    Term,
    Test,
    TestList,
    TestListGexp,
    Trailer,
    VarArgsList,

    Factor_Power_FLReference_Atom,
    ArithExpr_Term,
    Expr_ConcatExpr_ShiftExpr,
    Test_AndTest_NotTest_Comparison,
    ExprFromAtomChild,
    ExprFromNameChild,
    TestFromAtomChild,
)

def ArgListElement(element):
    if isinstance(element, str) or element.type is ParseNode.ARGUMENT:
        return element
    if element.type in (ParseNode.FL_CELL_REFERENCE, ParseNode.FL_NAKED_WORKSHEET_REFERENCE):
        return Argument([Test_AndTest_NotTest_Comparison(
                Expr_ConcatExpr_ShiftExpr(
                    ArithExpr_Term(Factor([Power([FLReference([element])])]))))])
    return Argument([element])


def TestFromFlReferenceChildren(children):
    return Test_AndTest_NotTest_Comparison(
                            Expr_ConcatExpr_ShiftExpr(
                                ArithExpr_Term(
                                    Factor([Power([FLReference(children)])])
                   )))


def CreateTest(name, lBracket, argList, rBracket):
    return TestFromFlReferenceChildren(
        [
        Atom([Name([name])]),
        Trailer(
            [
            lBracket,
            ArgList([ArgListElement(arg) for arg in argList]),
            rBracket
            ])
        ]
)


def ArgumentFromFLReferenceChild(child):
    return Argument([Test_AndTest_NotTest_Comparison(
                        Expr_ConcatExpr_ShiftExpr(
                            ArithExpr_Term(Factor([Power([FLReference([child])])]))))])

def CreateAndTest(operand1, operator, operand2):
    return Test(
        [AndTest(
                    [
                    NotTest(
                        [Comparison(
                            [Expr_ConcatExpr_ShiftExpr(
                                ArithExpr_Term(
                                    Factor_Power_FLReference_Atom(operand1)))])]),
                    operator,
                    NotTest(
                        [Comparison(
                            [Expr_ConcatExpr_ShiftExpr(
                                ArithExpr_Term(
                                    Factor_Power_FLReference_Atom(operand2)))])])
                    ])])

def CreateComparison(operand1, operator, operand2):
    return Test(
            [AndTest(
                [NotTest(
                    [Comparison(
                        [
                        Expr_ConcatExpr_ShiftExpr(
                            ArithExpr_Term(
                                Factor_Power_FLReference_Atom(operand1)))
                        ,
                        CompOperator([operator]),
                        Expr_ConcatExpr_ShiftExpr(
                            ArithExpr_Term(
                                Factor_Power_FLReference_Atom(operand2)))
                        ])])])])

def CreateParseTree(lBracket, test, forStr, exprList, inStr, testListSafe, rBracket):
    return FLRoot(["=", Test_AndTest_NotTest_Comparison(
            Expr_ConcatExpr_ShiftExpr(
                ArithExpr_Term(
                    Factor([Power([FLReference([Atom(
                        [
                        lBracket,
                        ListMaker(
                            [
                            test,
                            ListFor(
                                [
                                forStr,
                                exprList,
                                inStr,
                                testListSafe
                                ])
                            ]),
                        rBracket
                        ])])])]))))])


class ParseTreeTest(unittest.TestCase):

    def assertParsesToTree(self, text, expectedTree):
        self.assertEquals(parse(text), expectedTree, "\nParsed >>>%s<<< incorrectly" % (text))


    def assertParsesToFLReferenceChildren(self, text, children):
        prefix = ''.join(takewhile(lambda x: x in ' =', text))

        self.assertParsesToTree(text, FLRoot([prefix, TestFromFlReferenceChildren(children)]))


    def assertParsesToFLReferenceChild(self, text, child):
        self.assertParsesToFLReferenceChildren(text, [child])


    def assertParsesCorrectly(self, text, constructExpectedTree):
        self.assertParsesToTree(text, constructExpectedTree(text), )


    def assertCannotParse(self, text, errorPosition, errorToken=""):
        try:
            parse(text)
            self.fail("No error for invalid text >>>%s<<<" % (text))
        except FormulaError, e:
            if errorPosition == -1:
                self.assertEquals(str(e),
                                  "Possibly incomplete formula",
                                  "Unexpected error message")
            else:
                self.assertEquals(str(e),
                                  "Error in formula at position %d: unexpected '%s'" % (errorPosition, errorToken),
                                  "Unexpected error message")


    def testOne(self):
        def CreateParseTree(equals, number):
            return FLRoot([equals, Test_AndTest_NotTest_Comparison(
                ExprFromAtomChild(Number([number])))])

        self.assertParsesToTree("=1", CreateParseTree("=", "1"))
        self.assertParsesToTree("=  1", CreateParseTree("=  ", "1"))
        self.assertCannotParse(" = 1", 1, " = 1")


    def testFLD(self):
        "test f l d d e call"
        self.assertParsesToFLReferenceChild(
            "='hello'!'goodbye'", FLDDECall(["'hello'", "!", "'goodbye'"]))
        self.assertParsesToFLReferenceChild(
            "='BLP|M'!'GBPEUR Curncy,[PX_MID]'", FLDDECall(["'BLP|M'", "!", "'GBPEUR Curncy,[PX_MID]'"]))


    def testFLNaked(self):
        "test f l naked worksheet reference"
        self.assertParsesToFLReferenceChild(
            "=<Sheet1>", FLNakedWorksheetReference(["<", "Sheet1", ">"]))
        self.assertParsesToFLReferenceChild(
            "=< Sheet1 > ", FLNakedWorksheetReference(["< ", "Sheet1 ", "> "]))
        self.assertParsesToFLReferenceChild(
            "=<'Sheet1'>", FLNakedWorksheetReference(["<", "'Sheet1'", ">"]))
        self.assertParsesToFLReferenceChild(
            "=<'didn''t'>", FLNakedWorksheetReference(["<", "'didn''t'", ">"]))


    def testFLNaked2(self):
        "test f l naked worksheet reference with trailers"
        self.assertParsesToFLReferenceChildren(
            "=<Sheet1>.Bounds", [FLNakedWorksheetReference(["<", "Sheet1", ">"]), Trailer([".", Name(["Bounds"])])])



    def testFLNaked3(self):
        "test f l naked worksheet reference becomes normal cell reference where appropriate"
        self.assertParsesToFLReferenceChild(
            "=<Worksheet>!A1", FLCellReference(["Worksheet", "!", "A1"]))

        self.assertParsesToFLReferenceChild(
            "=<'Worksheet'>!A1", FLCellReference(["'Worksheet'", "!", "A1"]))

        self.assertParsesToFLReferenceChild(
            "=<'I didn''t do it!'>  !A1", FLCellReference(["'I didn''t do it!'  ", "!", "A1"]))

        self.assertParsesToFLReferenceChild(
            "=<Sheet1>!#Invalid!", FLInvalidReference(["Sheet1", "!", "#Invalid!"]))

        self.assertParsesToFLReferenceChild(
            "=<Sheet1>!#Deleted!", FLDeletedReference(["Sheet1", "!", "#Deleted!"]))

        self.assertCannotParse("=< 'boo!'>", 4, "'boo!'")
        self.assertCannotParse("=<'boo!' >", 3, "'boo!' ")


    def testWorksheetExpressions(self):
        def CreateParseTree(children):
            return FLRoot(["=", Test_AndTest_NotTest_Comparison(
                Expr_ConcatExpr_ShiftExpr(children))])

        self.assertParsesToTree("=<Sheet1>+<Sheet2>", CreateParseTree(
            ArithExpr(
                [Term(
                    [Factor(
                        [Power(
                            [FLReference([FLNakedWorksheetReference(["<", "Sheet1", ">"])])])])]),
                "+",
                Term(
                    [Factor(
                        [Power(
                            [FLReference([FLNakedWorksheetReference(["<", "Sheet2", ">"])])])])])]
                )))


    def testFLInvalid(self):
        "test f l invalid reference"
        self.assertParsesToFLReferenceChild(
            "=#Invalid!", FLInvalidReference(["#Invalid!"]))

        self.assertParsesToFLReferenceChild(
            "=Sheet1!#Invalid!", FLInvalidReference(["Sheet1", "!", "#Invalid!"]))

        self.assertParsesToFLReferenceChild(
            "=A_!#Invalid!", FLInvalidReference(["A_", "!", "#Invalid!"]))

        self.assertParsesToFLReferenceChild(
            "=_1!#Invalid!", FLInvalidReference(["_1", "!", "#Invalid!"]))

        self.assertParsesToFLReferenceChild(
            "=A1!#Invalid!", FLInvalidReference(["A1", "!", "#Invalid!"]))


    def testFLDeleted(self):
        "test f l deleted reference"
        self.assertParsesToFLReferenceChild(
            "=#Deleted!", FLDeletedReference(["#Deleted!"]))

        self.assertParsesToFLReferenceChild(
            "=Sheet1!#Deleted!", FLDeletedReference(["Sheet1", "!", "#Deleted!"]))

        self.assertParsesToFLReferenceChild(
            "='Sheet1!'!#Deleted!", FLDeletedReference(["'Sheet1!'", "!", "#Deleted!"]))

        self.assertParsesToFLReferenceChild(
            "=A_!#Deleted!", FLDeletedReference(["A_", "!", "#Deleted!"]))

        self.assertParsesToFLReferenceChild(
            "=_1!#Deleted!", FLDeletedReference(["_1", "!", "#Deleted!"]))

        self.assertParsesToFLReferenceChild(
            "=A1!#Deleted!", FLDeletedReference(["A1", "!", "#Deleted!"]))


    def testFLReference(self):
        "test f l reference nasty cases"
        self.assertParsesToTree("=#Deleted!+B26",
            FLRoot(["=", Test_AndTest_NotTest_Comparison(
                Expr_ConcatExpr_ShiftExpr(
                    ArithExpr([
                        Term([Factor([Power([FLReference([
                            FLDeletedReference(["#Deleted!"])])])])]),
                        "+",
                        Term([Factor([Power([FLReference([
                            FLCellReference(["B26"])])])])])
                        ])))]))

        self.assertParsesToTree("='x'!='y'",
            FLRoot(["=", Test([AndTest([NotTest([Comparison(
                [
                Expr_ConcatExpr_ShiftExpr(
                    ArithExpr_Term(Factor_Power_FLReference_Atom(StringLiteral(["'x'"])))),
                CompOperator(["!="]),
                Expr_ConcatExpr_ShiftExpr(
                    ArithExpr_Term(Factor_Power_FLReference_Atom(StringLiteral(["'y'"]))))
                ])])])])]))



    def testFLSum(self):
        def CreateParseTree(name, lBracket, argList, rBracket):
            return FLRoot(["=", CreateTest(name, lBracket, argList, rBracket)])

        self.assertParsesToTree("=SUM(A1:B2)", CreateParseTree(
            "SUM",
            "(",
            [
                ArgumentFromFLReferenceChild(FLCellRange(
                    [
                    FLCellReference(["A1"]),
                    ":",
                    FLCellReference(["B2"])
                    ]))
            ],
            ")"
            ))
        self.assertParsesToTree("=sum(A1:B2)", CreateParseTree(
            "sum",
            "(",
            [ArgumentFromFLReferenceChild(FLCellRange(
                [
                FLCellReference(["A1"]),
                ":",
                FLCellReference(["B2"])
                ]))
            ],
            ")"
            ))
        self.assertParsesToTree("=suM(A1:B2)", CreateParseTree(
            "suM",
            "(",
             [
                ArgumentFromFLReferenceChild(FLCellRange(
                    [
                    FLCellReference(["A1"]),
                    ":",
                    FLCellReference(["B2"])
                ]))
             ],
            ")"
            ))

        self.assertParsesToTree("=SUM ( A1 : B2 ) ", CreateParseTree(
            "SUM ",
            "( ",
            [
                ArgumentFromFLReferenceChild(FLCellRange(
                    [
                    FLCellReference(["A1 "]),
                    ": ",
                    FLCellReference(["B2 "])
                    ]))
            ],
            ") "
            ))

        self.assertParsesToTree("=SUM(A1:#Deleted!)", CreateParseTree(
            "SUM",
            "(",
            [
                ArgumentFromFLReferenceChild(FLCellRange(
                    [
                    FLCellReference(["A1"]),
                    ":",
                    FLDeletedReference(["#Deleted!"]),
                    ]))
            ],
            ")"
            ))

        self.assertParsesToTree("=SUM(#Deleted!:B2)", CreateParseTree(
            "SUM",
            "(",
            [
                ArgumentFromFLReferenceChild(FLCellRange(
                    [
                    FLDeletedReference(["#Deleted!"]),
                    ":",
                    FLCellReference(["B2"]),
                    ]))
            ],
            ")"
            ))

        self.assertParsesToTree("=SUM(#Deleted!:#Deleted!)", CreateParseTree(
            "SUM",
            "(",
            [
                ArgumentFromFLReferenceChild(FLCellRange(
                    [
                    FLDeletedReference(["#Deleted!"]),
                    ":",
                    FLDeletedReference(["#Deleted!"]),
                    ]))
            ],
            ")"
            ))

        self.assertParsesToTree("=SUM(A1:#Invalid!)", CreateParseTree(
            "SUM",
            "(",
            [
                ArgumentFromFLReferenceChild(FLCellRange(
                    [
                    FLCellReference(["A1"]),
                    ":",
                    FLInvalidReference(["#Invalid!"]),
                    ]))
            ],
            ")"
            ))

        self.assertParsesToTree("=SUM(#Invalid!:B2)", CreateParseTree(
            "SUM",
            "(",
            [
                ArgumentFromFLReferenceChild(FLCellRange(
                    [
                    FLInvalidReference(["#Invalid!"]),
                    ":",
                    FLCellReference(["B2"]),
                    ]))
            ],
            ")"
            ))

        self.assertParsesToTree("=SUM(#Invalid!:#Invalid!)", CreateParseTree(
            "SUM",
            "(",
            [
                ArgumentFromFLReferenceChild(FLCellRange(
                    [
                    FLInvalidReference(["#Invalid!"]),
                    ":",
                    FLInvalidReference(["#Invalid!"]),
                    ]))
            ],
            ")"
            ))

        self.assertCannotParse("=SUM(A1:AAAA1)", 8, "AAAA1")
        self.assertCannotParse("=SUM(AAAA1:A1)", 5, "AAAA1")

        self.assertCannotParse("=SUM(A1:FXSHRXX1)", 8, "FXSHRXX1")
        self.assertCannotParse("=SUM(FXSHRXX1:A1)", 5, "FXSHRXX1")

        self.assertParsesToTree("=SUM(A1:B2,A2:B1)", CreateParseTree(
            "SUM",
            "(",
                [
                    ArgumentFromFLReferenceChild(FLCellRange(
                        [
                        FLCellReference(["A1"]),
                        ":",
                        FLCellReference(["B2"])
                    ])),
                    ",",
                    ArgumentFromFLReferenceChild(FLCellRange(
                        [
                        FLCellReference(["A2"]),
                        ":",
                        FLCellReference(["B1"])
                    ]))
                ],
            ")"
            ))


        self.assertParsesToTree("=SUM(A1:B2,B1)", CreateParseTree(
            "SUM",
            "(",
             [
                    ArgumentFromFLReferenceChild(FLCellRange(
                        [
                        FLCellReference(["A1"]),
                        ":",
                        FLCellReference(["B2"])
                    ])),
                    ",",
                    ArgumentFromFLReferenceChild(FLCellReference(["B1"]))
             ],
            ")"
            ))

        self.assertParsesToTree("=SUM(A1:B2,SUM(A1))", CreateParseTree(
            "SUM",
            "(",
             [
                    ArgumentFromFLReferenceChild(FLCellRange(
                        [
                        FLCellReference(["A1"]),
                        ":",
                        FLCellReference(["B2"])
                    ])),
                    ",",
                    CreateTest('SUM', '(', [ArgumentFromFLReferenceChild(FLCellReference(["A1"]))], ')')
             ],
            ")"
            ))


        self.assertParsesToTree("=SUM(A1,A2,A3)", CreateParseTree(
            "SUM",
            "(",
            [
                ArgumentFromFLReferenceChild(FLCellReference(["A1"])),
                ",",
                ArgumentFromFLReferenceChild(FLCellReference(["A2"])),
                ",",
                ArgumentFromFLReferenceChild(FLCellReference(["A3"]))
            ],
            ")"))

        self.assertParsesToTree("=SUM(<Sheet1>)", CreateParseTree(
            "SUM",
            "(",
            [
                FLNakedWorksheetReference(["<", "Sheet1", ">"])
            ],
            ")"
            ))

        self.assertParsesToTree("=SUM(<Sheet1>,<Sheet2>)", CreateParseTree(
            "SUM",
            "(",
            [
                FLNakedWorksheetReference(["<", "Sheet1", ">"]),
                ",",
                FLNakedWorksheetReference(["<", "Sheet2", ">"])
            ],
            ")"
            ))
        self.assertParsesToTree("=SUM(Sheet1!A1:Sheet1!B1)", CreateParseTree(
            "SUM",
            "(",
            [
                 ArgumentFromFLReferenceChild(FLCellRange([
                        FLCellReference(["Sheet1", "!", "A1"]),
                        ":",
                        FLCellReference(["Sheet1", "!", "B1"])
                ]))
            ],
            ")"
            ))

        self.assertParsesToTree("=SUM(A1,1/7)", CreateParseTree(
             "SUM",
             "(",
             [
                FLCellReference(["A1"]),
                ',',
                Test_AndTest_NotTest_Comparison(
                                Expr_ConcatExpr_ShiftExpr(
                    ArithExpr(
                            [Term(
                                [
                                Factor_Power_FLReference_Atom(Number(["1"])),
                                "/",
                                Factor_Power_FLReference_Atom(Number(["7"]))
                                ])])))
             ],
             ")"
             ))


    def testFLCell(self):
        "test f l cell range"
        def CreateParseTree(name, lBracket, argList, rBracket):
            return FLRoot(["=", CreateTest(name, lBracket, argList, rBracket)])
        self.assertParsesToTree("=SUM(Sheet1!A1:B2)", CreateParseTree(
            "SUM",
            "(",
                [ArgumentFromFLReferenceChild(
                    FLCellRange(
                        [
                        FLCellReference(["Sheet1", "!", "A1"]),
                        ":",
                        FLCellReference(["Sheet1", "!", "B2"])
                    ]),
                )],
            ")"
            ))

        self.assertParsesToTree("=SUM(Sheet1!A1:Sheet2!B2)", CreateParseTree(
            "SUM",
            "(",
                [ArgumentFromFLReferenceChild(
                    FLCellRange(
                        [
                        FLCellReference(["Sheet1", "!", "A1"]),
                        ":",
                        FLCellReference(["Sheet2", "!", "B2"])
                    ]),
                )],
            ")"
            ))

        self.assertParsesToFLReferenceChild("= A1:Sheet1!B1", FLCellRange([
            FLCellReference(["A1"]), ":", FLCellReference(["Sheet1", "!", "B1"])]))

        self.assertParsesToFLReferenceChild("= Sheet1!A1:B1", FLCellRange([
            FLCellReference(["Sheet1", "!", "A1"]), ":", FLCellReference(["Sheet1", "!", "B1"])]))

        self.assertParsesToFLReferenceChild("= Sheet1!A1:Sheet1!B1", FLCellRange([
            FLCellReference(["Sheet1", "!", "A1"]), ":", FLCellReference(["Sheet1", "!", "B1"])]))

        self.assertParsesToFLReferenceChild("= A1:B1", FLCellRange([
            FLCellReference(["A1"]), ":", FLCellReference(["B1"])]))


    def testCellRangeWith(self):
        "test cell range with dictionaries"
        def CreateParseTree(lBrace, key, littleArrow, value, rBrace):
            return FLRoot(["=", Test_AndTest_NotTest_Comparison(
                    Expr_ConcatExpr_ShiftExpr(
                        ArithExpr_Term(
                            Factor([Power([FLReference([Atom(
                                [
                                lBrace,
                                DictMaker(
                                    [
                                    key,
                                    littleArrow,
                                    value
                                    ]),
                                rBrace
                                ])])])]))))])

        self.assertParsesToTree("={A1-> A1:B2}",
                                CreateParseTree('{',
                                                TestFromFlReferenceChildren([FLCellReference(['A1'])]),
                                                '-> ',
                                                TestFromFlReferenceChildren([
                                                    FLCellRange([
                                                        FLCellReference(["A1"]),
                                                        ":",
                                                        FLCellReference(["B2"])
                                                    ])
                                                ]),
                                                '}'))

        self.assertParsesToTree("={A11:A1->B2}",
                                CreateParseTree('{',
                                                TestFromFlReferenceChildren([
                                                    FLCellRange([
                                                        FLCellReference(["A11"]),
                                                        ":",
                                                        FLCellReference(["A1"])
                                                    ])
                                                ]),
                                                '->',
                                                TestFromFlReferenceChildren([FLCellReference(['B2'])]),
                                                '}'))

        self.assertParsesToTree("={B2:C3 -> A1:B2}",
                                CreateParseTree('{',
                                                TestFromFlReferenceChildren([
                                                    FLCellRange([
                                                        FLCellReference(["B2"]),
                                                        ":",
                                                        FLCellReference(["C3 "])
                                                    ])
                                                ]),
                                                '-> ',
                                                TestFromFlReferenceChildren([
                                                    FLCellRange([
                                                        FLCellReference(["A1"]),
                                                        ":",
                                                        FLCellReference(["B2"])
                                                    ])
                                                ]),
                                                '}'))

        self.assertParsesToTree("={A-> A1:B2}",
                                CreateParseTree('{',
                                                Test_AndTest_NotTest_Comparison(
                                                    ExprFromNameChild("A")),
                                                '-> ',
                                                TestFromFlReferenceChildren([
                                                    FLCellRange([
                                                        FLCellReference(["A1"]),
                                                        ":",
                                                        FLCellReference(["B2"])
                                                    ])
                                                ]),
                                                '}'))


    def testCellRangeWith2(self):
        "test cell range with lambdas"
        def CreateFLRoot(test):
            return FLRoot(["=", test])
        def CreateLambda(lambdastr, params, littleArrow, bodyTerm):
            return Test([LambDef(
                             [
                             lambdastr,
                             params,
                             littleArrow,
                             bodyTerm
                        ])
                    ])
        def CreateDictionary(lBrace, key, littleArrow, value, rBrace):
            return Test_AndTest_NotTest_Comparison(
                    Expr_ConcatExpr_ShiftExpr(
                        ArithExpr_Term(
                            Factor([Power([FLReference([Atom(
                                [
                                lBrace,
                                DictMaker(
                                    [
                                    key,
                                    littleArrow,
                                    value
                                    ]),
                                rBrace
                                ])])])]))))

        self.assertCannotParse("= {lambda A1->B2:C3}", 11, 'A1')
        self.assertCannotParse("= {lambda A1:B2->C3}", 11, 'A1')
        self.assertCannotParse("= {lambda A1:B2->C3:D4}", 11, 'A1')

        self.assertParsesToTree("=lambda A-> A1:B2",
                                CreateFLRoot(
                                    CreateLambda("lambda ",
                                        VarArgsList([FPDef([Name(["A"])])]),
                                        "-> ",
                                        TestFromFlReferenceChildren([
                                                    FLCellRange([
                                                        FLCellReference(["A1"]),
                                                        ":",
                                                        FLCellReference(["B2"])
                                                    ])
                                        ])
                                    )
                                )
                               )

        self.assertParsesToTree("=lambda x:=A1->B2: C3",
                                CreateFLRoot(
                                    CreateLambda("lambda ",
                                        VarArgsList(
                                            [
                                            FPDef([Name(["x"])]),
                                            ":=",
                                            TestFromFlReferenceChildren([FLCellReference(['A1'])])
                                        ]),
                                        "->",
                                        TestFromFlReferenceChildren([
                                                    FLCellRange([
                                                        FLCellReference(["B2"]),
                                                        ": ",
                                                        FLCellReference(["C3"])
                                                    ])
                                        ])
                                    )
                                )
                               )

        self.assertParsesToTree("={lambda A->B2->C3:D4}",
                                CreateFLRoot(
                                    CreateDictionary(
                                        "{",
                                        CreateLambda("lambda ",
                                            VarArgsList([FPDef([Name(["A"])])]),
                                            "->",
                                            TestFromFlReferenceChildren([FLCellReference(["B2"])])
                                        ),
                                        '->',
                                        TestFromFlReferenceChildren([
                                            FLCellRange([
                                                FLCellReference(["C3"]),
                                                ":",
                                                FLCellReference(["D4"])
                                            ])
                                        ]),
                                        "}"
                                    )
                                )
                               )

        self.assertParsesToTree("={lambda A->B2:C3->D4}",
                                CreateFLRoot(
                                    CreateDictionary(
                                        "{",
                                        CreateLambda("lambda ",
                                            VarArgsList([FPDef([Name(["A"])])]),
                                            "->",
                                            TestFromFlReferenceChildren([
                                                FLCellRange([
                                                    FLCellReference(["B2"]),
                                                    ":",
                                                    FLCellReference(["C3"])
                                                ])
                                            ])
                                        ),
                                        '->',
                                        TestFromFlReferenceChildren([FLCellReference(["D4"])]),
                                        "}"
                                    )
                                )
                               )


    def testCellRangeWith3(self):
        "test cell range with subscription"
        def CreateParseTree(obj, lBracket, subscripts, rBracket):
            return FLRoot(["=", Test_AndTest_NotTest_Comparison(
                Expr_ConcatExpr_ShiftExpr(
                        ArithExpr_Term(
                            Factor(
                                [Power(
                                    [FLReference(
                                        [
                                        Atom([obj]),
                                        Trailer(
                                            [
                                            lBracket,
                                            SubscriptList(subscripts),
                                            rBracket
                                            ])
                                        ])])]))))])

        self.assertParsesToTree("=a [A1:B2]",
            CreateParseTree(
                Name(["a "]),
                "[",
                [Subscript([
                    TestFromFlReferenceChildren([
                        FLCellRange([
                            FLCellReference(["A1"]),
                            ":",
                            FLCellReference(["B2"])
                        ])
                    ])
                ])],
                "]"))

        self.assertCannotParse("= a[A1:B2:C3]", 10, ':')
        self.assertCannotParse("= a[A1:B2:C3:D4]", 10, ':')

    def testCallWithGen(self):
        "test call with gen expr"
        def CreateParseTree(atom, lBracket, argument, rBracket):
            return FLRoot(["=", Test_AndTest_NotTest_Comparison(
                    Expr_ConcatExpr_ShiftExpr(
                        ArithExpr_Term(
                            Factor(
                                [Power(
                                    [FLReference(
                                        [
                                        atom,
                                        Trailer(
                                            [
                                            lBracket,
                                            ArgList([argument]),
                                            rBracket
                                            ])
                                        ])])]))))])

        self.assertParsesToTree(
            "=a(x for x in L)",
            CreateParseTree(
                Atom([Name(["a"])]),
                "(",
                Argument(
                    [
                    TestFromAtomChild(Name(["x "])),
                    GenFor(
                        [
                        "for ",
                        ExprList(
                            [ExprFromAtomChild(Name(["x "]))]),
                        "in ",
                        TestFromAtomChild(Name(["L"]))
                        ])
                    ]),
                ")"
                ))

        # Although the 2.4.3 grammar allows the following form, it shouldn't.
        # See http://mail.python.org/pipermail/python-dev/2006-February/061544.html
        self.assertCannotParse("=a(x = 5 (for x in L))", 11, "for ")


    def testPower(self):
        def CreateParseTree(flReferenceChildren, operator, exponent):
            return FLRoot(["=", Test_AndTest_NotTest_Comparison(
                Expr_ConcatExpr_ShiftExpr(
                        ArithExpr_Term(
                            Factor(
                                [Power(
                                    [
                                    FLReference(flReferenceChildren),
                                    operator,
                                    exponent
                                    ])]))))])

        self.assertParsesToTree("=a**b", CreateParseTree([Atom([Name(["a"])])], "**", Factor_Power_FLReference_Atom(Name(["b"]))))
        self.assertParsesToTree("=a^b", CreateParseTree([Atom([Name(["a"])])], "^", Factor_Power_FLReference_Atom(Name(["b"]))))
        self.assertParsesToTree("=a0**b2", CreateParseTree([Atom([Name(["a0"])])], "**", Factor([Power([FLReference([FLCellReference(["b2"])])])])))
        self.assertParsesToTree("=a0^b2", CreateParseTree([Atom([Name(["a0"])])], "^", Factor([Power([FLReference([FLCellReference(["b2"])])])])))
        self.assertParsesToTree("=e2**e0", CreateParseTree([FLCellReference(["e2"])], "**", Factor_Power_FLReference_Atom(Name(["e0"]))))
        self.assertParsesToTree("=e2^e0", CreateParseTree([FLCellReference(["e2"])], "^", Factor_Power_FLReference_Atom(Name(["e0"]))))
        self.assertParsesToTree("=j0**j", CreateParseTree([Atom([Name(["j0"])])], "**", Factor_Power_FLReference_Atom(Name(["j"]))))
        self.assertParsesToTree("=j0^j", CreateParseTree([Atom([Name(["j0"])])], "^", Factor_Power_FLReference_Atom(Name(["j"]))))

        self.assertParsesToTree("=j0.x**j",
            CreateParseTree(
                [
                Atom([Name(["j0"])]),
                Trailer([".", Name(["x"])])
                ],
                "**",
                Factor_Power_FLReference_Atom(Name(["j"]))))

        self.assertParsesToTree("=j0.x^j",
            CreateParseTree(
                [
                Atom([Name(["j0"])]),
                Trailer([".", Name(["x"])])
                ],
                "^",
                Factor_Power_FLReference_Atom(Name(["j"]))))

        self.assertParsesToTree("=j0.x(15)[p->q]**j",
            CreateParseTree(
                [
                Atom([Name(["j0"])]),
                Trailer([".", Name(["x"])]),
                Trailer(
                    [
                    "(",
                    ArgList([Argument([TestFromAtomChild(Number(["15"]))])]),
                    ")"
                    ]),
                Trailer(
                    [
                    "[",
                    SubscriptList([Subscript(
                        [
                        TestFromAtomChild(Name(["p"])),
                        "->",
                        TestFromAtomChild(Name(["q"]))
                        ])]),
                    "]"
                    ]),
                ],
                "**",
                Factor_Power_FLReference_Atom(Name(["j"]))))

        self.assertParsesToTree("=j0.x(15)[p->q]^j",
            CreateParseTree(
                [
                Atom([Name(["j0"])]),
                Trailer([".", Name(["x"])]),
                Trailer(
                    [
                    "(",
                    ArgList([Argument([TestFromAtomChild(Number(["15"]))])]),
                    ")"
                    ]),
                Trailer(
                    [
                    "[",
                    SubscriptList([Subscript(
                        [
                        TestFromAtomChild(Name(["p"])),
                        "->",
                        TestFromAtomChild(Name(["q"]))
                        ])]),
                    "]"
                    ]),
                ],
                "^",
                Factor_Power_FLReference_Atom(Name(["j"]))))


    def testNestedFactor(self):
        def CreateParseTree(unaryOperation, operand):
            return FLRoot(["=", Test_AndTest_NotTest_Comparison(
                Expr_ConcatExpr_ShiftExpr(
                        ArithExpr_Term(
                            Factor(
                                [
                                unaryOperation,
                                Factor_Power_FLReference_Atom(Number([operand]))
                                ]))))])

        self.assertParsesToTree("=+1", CreateParseTree("+", "1"))
        self.assertParsesToTree("=-1", CreateParseTree("-", "1"))
        self.assertParsesToTree("=~1", CreateParseTree("~", "1"))


    def testPercent(self):
        def CreateParseTree(operand, percentOperator):
            return FLRoot(["=", Test_AndTest_NotTest_Comparison(
                Expr_ConcatExpr_ShiftExpr(
                        ArithExpr_Term(
                            Percent(
                                [
                                Factor_Power_FLReference_Atom(operand),
                                percentOperator
                                ]))))])

        self.assertParsesToTree("=10%", CreateParseTree(Number(["10"]), "%"))
        self.assertParsesToTree("=10 %", CreateParseTree(Number(["10 "]), "%"))
        self.assertParsesToTree("=10% ", CreateParseTree(Number(["10"]), "% "))
        self.assertParsesToTree("=a % ", CreateParseTree(Name(["a "]), "% "))


    def testFactorFactorTerm(self):
        def CreateParseTree(moperator, uoperator1, operand1, uoperator2, operand2):
            return FLRoot(["=", Test_AndTest_NotTest_Comparison(
                Expr_ConcatExpr_ShiftExpr(
                        ArithExpr(
                            [Term(
                                [
                                Factor(
                                    [uoperator1, Factor_Power_FLReference_Atom(operand1)]),
                                moperator,
                                Factor(
                                    [uoperator2, Factor_Power_FLReference_Atom(operand2)])
                                ])])))])

        self.assertParsesToTree("=-6/-4", CreateParseTree("/",
                                                         "-", Number(["6"]),
                                                         "-", Number(["4"])))
        self.assertParsesToTree("=- 6 / - 4", CreateParseTree("/ ",
                                                             "- ", Number(["6 "]),
                                                             "- ", Number(["4"])))
        self.assertParsesToTree("=-6/~.4", CreateParseTree("/",
                                                         "-", Number(["6"]),
                                                         "~", Number([".4"])))
        self.assertParsesToTree("=- 6 / ~ .4", CreateParseTree("/ ",
                                                              "- ", Number(["6 "]),
                                                              "~ ", Number([".4"])))
        self.assertParsesToTree("=-4.5j/+2.4e6", CreateParseTree("/",
                                                                "-", Number(["4.5j"]),
                                                                "+", Number(["2.4e6"])))
        self.assertParsesToTree("=- 4.5j / + 2.4e6", CreateParseTree("/ ",
                                                                    "- ", Number(["4.5j "]),
                                                                    "+ ", Number(["2.4e6"])))


    def testAtomTerm(self):
        def CreateParseTree(operator, operand1, operand2):
            return FLRoot(["=", Test_AndTest_NotTest_Comparison(
                Expr_ConcatExpr_ShiftExpr(
                        ArithExpr(
                            [Term(
                                [
                                Factor_Power_FLReference_Atom(operand1),
                                operator,
                                Factor_Power_FLReference_Atom(operand2)
                                ])])))])

        self.assertParsesToTree("=1*2", CreateParseTree("*", Number(["1"]), Number(["2"])))
        self.assertParsesToTree("=1 * 2", CreateParseTree("* ", Number(["1 "]), Number(["2"])))
        self.assertParsesToTree("=1/2", CreateParseTree("/", Number(["1"]), Number(["2"])))
        self.assertParsesToTree("=1 / 2", CreateParseTree("/ ", Number(["1 "]), Number(["2"])))
        self.assertParsesToTree("=1//2", CreateParseTree("//", Number(["1"]), Number(["2"])))
        self.assertParsesToTree("=1 // 2", CreateParseTree("// ", Number(["1 "]), Number(["2"])))
        self.assertParsesToTree("=1%%2", CreateParseTree("%%", Number(["1"]), Number(["2"])))
        self.assertParsesToTree("=1 %% 2", CreateParseTree("%% ", Number(["1 "]), Number(["2"])))
        self.assertParsesToTree("=1.6e38*2", CreateParseTree("*", Number(["1.6e38"]), Number(["2"])))
        self.assertParsesToTree("=1.6e38 * 2", CreateParseTree("* ", Number(["1.6e38 "]), Number(["2"])))
        self.assertParsesToTree("=1./2j", CreateParseTree("/", Number(["1."]), Number(["2j"])))
        self.assertParsesToTree("=1. / 2j", CreateParseTree("/ ", Number(["1. "]), Number(["2j"])))


    def testMultiAtomTerm(self):
        def CreateParseTree(operand1, operator1, operand2, operator2,  operand3):
            return FLRoot(["=", Test_AndTest_NotTest_Comparison(
                Expr_ConcatExpr_ShiftExpr(
                        ArithExpr(
                            [Term(
                                [
                                Factor_Power_FLReference_Atom(operand1),
                                operator1,
                                Factor_Power_FLReference_Atom(operand2),
                                operator2,
                                Factor_Power_FLReference_Atom(operand3)
                                ])])))])

        self.assertParsesToTree("=1* 2e3/4j", CreateParseTree(
            Number(["1"]),
            "* ",
            Number(["2e3"]),
            "/",
            Number(["4j"])))


    def testAtomArithExpr(self):
        def CreateParseTree(operator, operand1, operand2):
            return FLRoot(["=", Test_AndTest_NotTest_Comparison(
                Expr_ConcatExpr_ShiftExpr(
                        ArithExpr(
                            [
                            Term(
                                [Factor_Power_FLReference_Atom(operand1)]),
                            operator,
                            Term(
                                [Factor_Power_FLReference_Atom(operand2)])
                            ])))])

        self.assertParsesToTree("=1+2", CreateParseTree("+", Number(["1"]), Number(["2"])))
        self.assertParsesToTree("=1 + 2", CreateParseTree("+ ", Number(["1 "]), Number(["2"])))
        self.assertParsesToTree("=5e3-2.2", CreateParseTree("-", Number(["5e3"]), Number(["2.2"])))
        self.assertParsesToTree("=5e3 - 2.2", CreateParseTree("- ", Number(["5e3 "]), Number(["2.2"])))
        self.assertParsesToTree("=1j+2e6", CreateParseTree("+", Number(["1j"]), Number(["2e6"])))
        self.assertParsesToTree("=1j + 2e6", CreateParseTree("+ ", Number(["1j "]), Number(["2e6"])))


    def testMultiAtomArith(self):
        "test multi atom arith expr"
        def CreateParseTree(operand1, operator1, operand2, operator2, operand3):
            return FLRoot(["=", Test_AndTest_NotTest_Comparison(
                Expr_ConcatExpr_ShiftExpr(
                        ArithExpr(
                            [
                            Term(
                                [Factor_Power_FLReference_Atom(operand1)]),
                            operator1,
                            Term(
                                [Factor_Power_FLReference_Atom(operand2)]),
                            operator2,
                            Term(
                                [Factor_Power_FLReference_Atom(operand3)])
                            ])))])

        self.assertParsesToTree("=1.5+2j  - 5", CreateParseTree(
            Number(["1.5"]),
            "+",
            Number(["2j  "]),
            "- ",
            Number(["5"])))


    def testAtomShiftExpr(self):
        def CreateParseTree(operator, operand1, operand2):
            return FLRoot(["=", Test_AndTest_NotTest_Comparison(
                    Expr(
                        [ConcatExpr(
                            [ShiftExpr(
                                [
                                ArithExpr_Term(
                                    Factor_Power_FLReference_Atom(operand1)),
                                operator,
                                ArithExpr_Term(
                                    Factor_Power_FLReference_Atom(operand2))
                                ])])]))])

        self.assertParsesToTree("=2<<3", CreateParseTree("<<", Number(["2"]), Number(["3"])))
        self.assertParsesToTree("=2 << 3", CreateParseTree("<< ", Number(["2 "]), Number(["3"])))
        self.assertParsesToTree("=2e3>>3J", CreateParseTree(">>", Number(["2e3"]), Number(["3J"])))
        self.assertParsesToTree("=2e3 >> 3J", CreateParseTree(">> ", Number(["2e3 "]), Number(["3J"])))


    def testMultiAtomShift(self):
        "test multi atom shift expr"
        def CreateParseTree(operand1, operator1, operand2, operator2, operand3):
            return FLRoot(["=", Test_AndTest_NotTest_Comparison(
                    Expr(
                        [ConcatExpr(
                            [ShiftExpr(
                                [
                                ArithExpr_Term(
                                    Factor_Power_FLReference_Atom(operand1)),
                                operator1,
                                ArithExpr_Term(
                                    Factor_Power_FLReference_Atom(operand2)),
                                operator2,
                                ArithExpr_Term(
                                    Factor_Power_FLReference_Atom(operand3))
                                ])])]))])

        self.assertParsesToTree("=2<<3>>7", CreateParseTree(
            Number(["2"]),
            "<<",
            Number(["3"]),
            ">>",
            Number(["7"])))


    def testAtomConcatExpr(self):
        def CreateParseTree(operator, operand1, operand2):
            return FLRoot(["=", Test_AndTest_NotTest_Comparison(
                Expr(
                    [ConcatExpr(
                        [
                        ShiftExpr(
                            [ArithExpr_Term(
                                Factor_Power_FLReference_Atom(operand1))]),
                        operator,
                        ShiftExpr(
                            [ArithExpr_Term(
                                Factor_Power_FLReference_Atom(operand2))])
                        ])]))])

        self.assertParsesToTree("=a&b", CreateParseTree("&", Name(["a"]), Name(["b"])))
        self.assertParsesToTree("=a & b", CreateParseTree("& ", Name(["a "]), Name(["b"])))


    def testMultiAtomConcat(self):
        "test multi atom concat expr"
        def CreateParseTree(operand1, operator1, operand2, operator2, operand3):
            return FLRoot(["=", Test_AndTest_NotTest_Comparison(
                Expr(
                    [ConcatExpr(
                        [
                        ShiftExpr(
                            [ArithExpr_Term(
                                Factor_Power_FLReference_Atom(operand1))]),
                        operator1,
                        ShiftExpr(
                            [ArithExpr_Term(
                                Factor_Power_FLReference_Atom(operand2))]),
                        operator2,
                        ShiftExpr(
                            [ArithExpr_Term(
                                Factor_Power_FLReference_Atom(operand3))])
                        ])]))])

        self.assertParsesToTree("=a&b& c", CreateParseTree(
            Name(["a"]),
            "&",
            Name(["b"]),
            "& ",
            Name(["c"])))


    def testExpr(self):
        def CreateParseTree(operator, operand1, operand2):
            return FLRoot(["=", Test_AndTest_NotTest_Comparison(
                    Expr(
                        [
                        ConcatExpr(
                            [ShiftExpr(
                                [ArithExpr_Term(
                                    Factor_Power_FLReference_Atom(
                                        Name([operand1])))])]),
                        operator,
                        ConcatExpr(
                            [ShiftExpr(
                                [ArithExpr_Term(
                                    Factor_Power_FLReference_Atom(
                                        Name([operand2])))])])
                        ]))])

        self.assertParsesToTree("=a|b", CreateParseTree("|", "a", "b"))
        self.assertParsesToTree("=a | b", CreateParseTree("| ", "a ", "b"))


    def testSimpleComparison(self):
        def CreateParseTree(operand1, operator, operand2):
            return FLRoot(["=", Test(
                    [AndTest(
                        [NotTest(
                            [Comparison(
                                [
                                Expr_ConcatExpr_ShiftExpr(
                                    ArithExpr_Term(
                                        Factor_Power_FLReference_Atom(operand1)))
                                ,
                                CompOperator([operator]),
                                Expr_ConcatExpr_ShiftExpr(
                                    ArithExpr_Term(
                                        Factor_Power_FLReference_Atom(operand2)))
                                ])])])])])

        self.assertParsesToTree("=a<b", CreateParseTree(Name(["a"]), "<", Name(["b"])))
        self.assertParsesToTree("=a < b", CreateParseTree(Name(["a "]), "< ", Name(["b"])))
        self.assertParsesToTree("=a>b", CreateParseTree(Name(["a"]), ">", Name(["b"])))
        self.assertParsesToTree("=a > b", CreateParseTree(Name(["a "]), "> ", Name(["b"])))
        self.assertParsesToTree("=a==b", CreateParseTree(Name(["a"]), "==", Name(["b"])))
        self.assertParsesToTree("=a=b", CreateParseTree(Name(["a"]), "=", Name(["b"])))
        self.assertParsesToTree("=a == b", CreateParseTree(Name(["a "]), "== ", Name(["b"])))
        self.assertParsesToTree("=a = b", CreateParseTree(Name(["a "]), "= ", Name(["b"])))
        self.assertParsesToTree("=a>=b", CreateParseTree(Name(["a"]), ">=", Name(["b"])))
        self.assertParsesToTree("=a >= b", CreateParseTree(Name(["a "]), ">= ", Name(["b"])))
        self.assertParsesToTree("=a<=b", CreateParseTree(Name(["a"]), "<=", Name(["b"])))
        self.assertParsesToTree("=a <= b", CreateParseTree(Name(["a "]), "<= ", Name(["b"])))
        self.assertParsesToTree("=a<>b", CreateParseTree(Name(["a"]), "<>", Name(["b"])))
        self.assertParsesToTree("=a <> b", CreateParseTree(Name(["a "]), "<> ", Name(["b"])))
        self.assertParsesToTree("=a!=b", CreateParseTree(Name(["a"]), "!=", Name(["b"])))
        self.assertParsesToTree("=a != b", CreateParseTree(Name(["a "]), "!= ", Name(["b"])))

        self.assertParsesToTree('="a"is"b"', CreateParseTree(StringLiteral(['"a"']),
                                                            "is",
                                                            StringLiteral(['"b"'])))
        self.assertParsesToTree('="a" is "b"', CreateParseTree(StringLiteral(['"a" ']),
                                                            "is ",
                                                            StringLiteral(['"b"'])))
        self.assertParsesToTree('="a"in"b"', CreateParseTree(StringLiteral(['"a"']),
                                                            "in",
                                                            StringLiteral(['"b"'])))
        self.assertParsesToTree('="a" in "b"', CreateParseTree(StringLiteral(['"a" ']),
                                                            "in ",
                                                            StringLiteral(['"b"'])))
        self.assertParsesToTree('=1is 2', CreateParseTree(Number(["1"]),
                                                         "is ",
                                                         Number(["2"])))
        self.assertParsesToTree('=1 is 2', CreateParseTree(Number(["1 "]),
                                                          "is ",
                                                          Number(["2"])))
        self.assertParsesToTree('="a"is not"b"', CreateParseTree(StringLiteral(['"a"']),
                                                                "is not",
                                                                StringLiteral(['"b"'])))
        self.assertParsesToTree('="a"  is   not  "b"', CreateParseTree(StringLiteral(['"a"  ']),
                                                                "is   not  ",
                                                                StringLiteral(['"b"'])))
        self.assertParsesToTree('="a"not in"b"', CreateParseTree(StringLiteral(['"a"']),
                                                                "not in",
                                                                StringLiteral(['"b"'])))
        self.assertParsesToTree('="a" not   in "b"', CreateParseTree(StringLiteral(['"a" ']),
                                                                "not   in ",
                                                                StringLiteral(['"b"'])))

        self.assertCannotParse("=1is2", 3, "is2")
        self.assertCannotParse("=1 is2", 4, "is2")
        self.assertCannotParse("=1 isnot 2", 4, "isnot ")
        self.assertCannotParse("=x := 2", 4, ":= ")


    def testComplexComparison(self):
        def CreateParseTree(operand1, operator1, operand2, operator2, operand3):
            return FLRoot(["=", Test(
                    [AndTest(
                        [NotTest(
                            [Comparison(
                                [
                                Expr_ConcatExpr_ShiftExpr(
                                    ArithExpr_Term(
                                        Factor_Power_FLReference_Atom(operand1)))
                                ,
                                CompOperator([operator1])
                                ,
                                Expr_ConcatExpr_ShiftExpr(
                                    ArithExpr_Term(
                                        Factor_Power_FLReference_Atom(operand2)))
                                ,
                                CompOperator([operator2])
                                ,
                                Expr_ConcatExpr_ShiftExpr(
                                    ArithExpr_Term(
                                        Factor_Power_FLReference_Atom(operand3)))
                                ])])])])])


        self.assertParsesToTree("=a is not b is c", CreateParseTree(Name(["a "]),
                                                                   "is not ",
                                                                   Name(["b "]),
                                                                   "is ",
                                                                   Name(["c"])))
        self.assertParsesToTree("=1 < x <= 4", CreateParseTree(Number(["1 "]),
                                                              "< ",
                                                              Name(["x "]),
                                                              "<= ",
                                                              Number(["4"])))


    def testNotTest(self):
        def CreateParseTree(operator, operand):
            return FLRoot(["=", Test(
                    [AndTest(
                        [NotTest(
                            [
                            operator,
                            NotTest(
                                [Comparison(
                                    [Expr_ConcatExpr_ShiftExpr(
                                        ArithExpr_Term(
                                            Factor_Power_FLReference_Atom(operand)))])])
                            ])])])])

        # no need to test trivial case -- is amply tested by almost every other test ;-)
        self.assertParsesToTree("=not 33", CreateParseTree("not ", Number(["33"])))


    def testNotNotTest(self):
        def CreateParseTree(operator1, operator2, operand):
            return FLRoot(["=", Test(
                    [AndTest(
                        [NotTest(
                            [
                            operator1,
                            NotTest(
                                [
                                operator2,
                                NotTest(
                                    [Comparison(
                                        [Expr_ConcatExpr_ShiftExpr(
                                            ArithExpr_Term(
                                                Factor_Power_FLReference_Atom(operand)))])])
                                ])
                            ]
                        )])])])

        self.assertParsesToTree("=not   not foobar", CreateParseTree("not   ", "not ", Name(["foobar"])))


    def testAndTest(self):
        def CreateParseTree(operand1, operator, operand2):
            return FLRoot(["=", CreateAndTest(operand1, operator, operand2)])


        self.assertParsesToTree("=22 and 33", CreateParseTree(Number(["22 "]), "and ", Number(["33"])))
        self.assertParsesToTree("=22   and 33", CreateParseTree(Number(["22   "]), "and ", Number(["33"])))
        self.assertParsesToTree("=2and'a'", CreateParseTree(Number(["2"]), "and", StringLiteral(["'a'"])))


    def testMultiAndTest(self):
        def CreateParseTree(operand1, operator1, operand2, operator2, operand3):
            return FLRoot(["=", Test(
                    [AndTest(
                        [
                        NotTest(
                            [Comparison(
                                [Expr_ConcatExpr_ShiftExpr(
                                    ArithExpr_Term(
                                        Factor_Power_FLReference_Atom(operand1)))])]),
                        operator1,
                        NotTest(
                            [Comparison(
                                [Expr_ConcatExpr_ShiftExpr(
                                    ArithExpr_Term(
                                        Factor_Power_FLReference_Atom(operand2)))])]),
                        operator2,
                        NotTest(
                            [Comparison(
                                [Expr_ConcatExpr_ShiftExpr(
                                    ArithExpr_Term(
                                        Factor_Power_FLReference_Atom(operand3)))])])
                        ])])])


        self.assertParsesToTree("=22 and 33e3 and pi", CreateParseTree(
            Number(["22 "]),
            "and ",
            Number(["33e3 "]),
            "and ",
            Name(["pi"])))


    def testTest(self):
        def CreateParseTree(operand1, operator, operand2):
            return FLRoot(["=", Test(
                    [
                    AndTest(
                        [NotTest(
                            [Comparison(
                                [Expr_ConcatExpr_ShiftExpr(
                                    ArithExpr_Term(
                                        Factor_Power_FLReference_Atom(operand1)))])])]),
                    operator,
                    AndTest(
                        [NotTest(
                            [Comparison(
                                [Expr_ConcatExpr_ShiftExpr(
                                    ArithExpr_Term(
                                        Factor_Power_FLReference_Atom(operand2)))])])])
                    ])])

        self.assertParsesToTree("=22 or 33", CreateParseTree(Number(["22 "]), "or ", Number(["33"])))
        self.assertParsesToTree("=22   or 33", CreateParseTree(Number(["22   "]), "or ", Number(["33"])))
        self.assertParsesToTree("=2or'a'", CreateParseTree(Number(["2"]), "or", StringLiteral(["'a'"])))


    def testMultiTest(self):
        def CreateParseTree(operand1, operator1, operand2, operator2, operand3):
            return FLRoot(["=", Test(
                    [
                    AndTest(
                        [NotTest(
                            [Comparison(
                                [Expr_ConcatExpr_ShiftExpr(
                                    ArithExpr_Term(
                                        Factor_Power_FLReference_Atom(operand1)))])])]),
                    operator1,
                    AndTest(
                        [NotTest(
                            [Comparison(
                                [Expr_ConcatExpr_ShiftExpr(
                                    ArithExpr_Term(
                                        Factor_Power_FLReference_Atom(operand2)))])])]),
                    operator2,
                    AndTest(
                        [NotTest(
                            [Comparison(
                                [Expr_ConcatExpr_ShiftExpr(
                                    ArithExpr_Term(
                                        Factor_Power_FLReference_Atom(operand3)))])])])
                    ])])

        self.assertParsesToTree("=22j or 33 or '''CHEESE!'''", CreateParseTree(
            Number(["22j "]),
            "or ",
            Number(["33 "]),
            "or ",
            StringLiteral(["'''CHEESE!'''"])))


    def testTrivialLambDef(self):
        def CreateParseTree(lambdastr, littleArrow, atom):
            return FLRoot(["=", Test(
                [LambDef(
                    [
                    lambdastr,
                    littleArrow,
                    Test_AndTest_NotTest_Comparison(
                        Expr_ConcatExpr_ShiftExpr(
                            ArithExpr_Term(
                                Factor_Power_FLReference_Atom(atom))))])])])

        self.assertParsesToTree("=lambda->1", CreateParseTree("lambda", "->", Number(["1"])))
        self.assertParsesToTree("=lambda  ->  x", CreateParseTree("lambda  ", "->  ", Name(["x"])))

        self.assertCannotParse("=lambda 3 -> 3", 9, "3 ")


    def testSimpleLambDef(self):
        def CreateParseTree(lambdastr, params, littleArrow, bodyTerm):
            return FLRoot(["=", Test(
                [LambDef(
                    [
                    lambdastr,
                    params,
                    littleArrow,
                    Test_AndTest_NotTest_Comparison(
                            Expr_ConcatExpr_ShiftExpr(
                                ArithExpr(
                                    [bodyTerm])))
                    ])])])

        self.assertParsesToTree("=lambda  x -> y",
            CreateParseTree(
                "lambda  ",
                 VarArgsList([FPDef([Name(["x "])])]),
                 "-> ",
                 Term([Factor_Power_FLReference_Atom(Name(["y"]))])))

        self.assertParsesToTree("=lambda  x, -> y",
            CreateParseTree(
                "lambda  ",
                 VarArgsList([FPDef([Name(["x"])]), ", "]),
                 "-> ",
                 Term([Factor_Power_FLReference_Atom(Name(["y"]))])))

        self.assertParsesToTree("=lambda  x,y   -> y",
            CreateParseTree(
                "lambda  ",
                 VarArgsList(
                    [
                    FPDef([Name(["x"])]),
                    ",",
                    FPDef([Name(["y   "])]),
                    ]),
                 "-> ",
                 Term([Factor_Power_FLReference_Atom(Name(["y"]))])))

        self.assertParsesToTree("=lambda  x,y  ,z, -> y",
            CreateParseTree(
                "lambda  ",
                 VarArgsList(
                    [
                    FPDef([Name(["x"])]),
                    ",",
                    FPDef([Name(["y  "])]),
                    ",",
                    FPDef([Name(["z"])]),
                    ", ",
                    ]),
                 "-> ",
                 Term([Factor_Power_FLReference_Atom(Name(["y"]))])))

        self.assertParsesToTree("=lambda  *x -> y",
            CreateParseTree(
                "lambda  ",
                 VarArgsList(
                    [
                    "*",
                    Name(["x "])
                    ]),
                 "-> ",
                 Term([Factor_Power_FLReference_Atom(Name(["y"]))])))

        self.assertParsesToTree("=lambda  **x -> y",
            CreateParseTree(
                "lambda  ",
                 VarArgsList(
                    [
                    "**",
                    Name(["x "])
                    ]),
                 "-> ",
                 Term([Factor_Power_FLReference_Atom(Name(["y"]))])))

        self.assertParsesToTree("=lambda  *x, **y -> y",
            CreateParseTree(
                "lambda  ",
                 VarArgsList(
                    [
                    "*",
                    Name(["x"]),
                    ", ",
                    "**",
                    Name(["y "]),
                    ]),
                 "-> ",
                 Term([Factor_Power_FLReference_Atom(Name(["y"]))])))

        self.assertParsesToTree("=lambda  x, *y -> y",
            CreateParseTree(
                "lambda  ",
                 VarArgsList(
                    [
                    FPDef([Name(["x"])]),
                    ", ",
                    "*",
                    Name(["y "]),
                    ]),
                 "-> ",
                 Term([Factor_Power_FLReference_Atom(Name(["y"]))])))

        self.assertParsesToTree("=lambda  x, **y -> y",
            CreateParseTree(
                "lambda  ",
                 VarArgsList(
                    [
                    FPDef([Name(["x"])]),
                    ", ",
                    "**",
                    Name(["y "]),
                    ]),
                 "-> ",
                 Term([Factor_Power_FLReference_Atom(Name(["y"]))])))

        self.assertParsesToTree("=lambda  x, *y, **z -> y",
            CreateParseTree(
                "lambda  ",
                 VarArgsList(
                    [
                    FPDef([Name(["x"])]),
                    ", ",
                    "*",
                    Name(["y"]),
                    ", ",
                    "**",
                    Name(["z "]),
                    ]),
                 "-> ",
                 Term([Factor_Power_FLReference_Atom(Name(["y"]))])))

        self.assertParsesToTree("=lambda  x := None -> y",
            CreateParseTree(
                "lambda  ",
                VarArgsList(
                    [
                    FPDef([Name(["x "])]),
                    ":= ",
                    TestFromAtomChild(Name(["None "]))
                    ]),
                "-> ",
                Term([Factor_Power_FLReference_Atom(Name(["y"]))])))

        self.assertParsesToTree("=lambda  ( x ) -> y",
            CreateParseTree(
                "lambda  ",
                VarArgsList(
                    [
                    FPDef(["( ", FPList([FPDef([Name(["x "])])]), ") "])
                    ]),
                 "-> ",
                 Term([Factor_Power_FLReference_Atom(Name(["y"]))])))

        self.assertParsesToTree("=lambda  ( x  ,  y, z ) -> w",
            CreateParseTree(
                "lambda  ",
                VarArgsList(
                    [
                    FPDef(
                        [
                        "( ",
                        FPList(
                            [
                            FPDef([Name(["x  "])]),
                            ",  ",
                            FPDef([Name(["y"])]),
                            ", ",
                            FPDef([Name(["z "])]),
                            ]),
                        ") "
                        ])
                    ]),
                "-> ",
                Term([Factor_Power_FLReference_Atom(Name(["w"]))])))

        self.assertParsesToTree("=lambda  ( x  ,  y, z ), (q,  ) := 1 ,-> w",
            CreateParseTree(
                "lambda  ",
                VarArgsList(
                    [
                    FPDef(
                        [
                        "( ",
                        FPList(
                            [
                            FPDef([Name(["x  "])]),
                            ",  ",
                            FPDef([Name(["y"])]),
                            ", ",
                            FPDef([Name(["z "])]),
                            ]),
                        ")"
                        ]),
                    ", ",
                    FPDef(
                        [
                        "(",
                        FPList(
                            [
                            FPDef([Name(["q"])]),
                            ",  ",
                            ]),
                        ") "
                        ]),
                    ":= ",
                    TestFromAtomChild(Number(["1 "])),
                    ","
                    ]),
                "-> ",
                Term([Factor_Power_FLReference_Atom(Name(["w"]))])))

        self.assertParsesToTree("=lambda  x -> y * z",
            CreateParseTree(
                "lambda  ",
                 VarArgsList([FPDef([Name(["x "])])]),
                 "-> ",
                 Term(
                    [
                    Factor_Power_FLReference_Atom(Name(["y "])),
                    "* ",
                    Factor_Power_FLReference_Atom(Name(["z"]))
                    ])))

        self.assertCannotParse("=lambda , : 3", 9, ", ")
        self.assertCannotParse("=lambda x, y, , : 3", 15, ", ")
        self.assertCannotParse("=lambda p, x:=1, y, , : 3", 18, "y")
        self.assertCannotParse("=lambda *x, y, : 3", 13, "y")
        self.assertCannotParse("=lambda **x, y : 3", 12, ", ")
        self.assertCannotParse("=lambda *x, y:=1, : 3", 13, "y")
        self.assertCannotParse("=lambda **x, y:=1 : 3", 12, ", ")
        self.assertCannotParse("=lambda *x, *y : 3", 13, "*")
        self.assertCannotParse("=lambda **x, **y : 3", 12, ", ")
        self.assertCannotParse("=lambda **x, *y : 3", 12, ", ")
        self.assertCannotParse("=lambda z, **x, *y : 3", 15, ", ")
        self.assertCannotParse("=lambda z, *x, y : 3", 16, "y ")
        self.assertCannotParse("=lambda *x, : 3", 13, ": ")
        self.assertCannotParse("=lambda *x, **y, : 3", 16, ", ")
        self.assertCannotParse("=lambda **y, : 3", 12, ", ")
        self.assertCannotParse("=lambda x:=1,y, : 3", 14, "y")
        self.assertCannotParse("=lambda (x:=1) : 3", 11, ":=")
        self.assertCannotParse("=lambda (x:=1,y), : 3", 11, ":=")
        self.assertCannotParse("=lambda (x:=1),y, : 3", 11 ,":=")


    def testTrivialStringConversion(self):
        def CreateParseTree(firstQuote, atomChild, secondQuote):
            return FLRoot(["=", Test_AndTest_NotTest_Comparison(
                Expr_ConcatExpr_ShiftExpr(
                    ArithExpr_Term(
                        Factor([Power([FLReference([Atom(
                            [
                            firstQuote,
                            TestList(
                                [
                                TestFromAtomChild(atomChild)
                                ]),
                            secondQuote
                            ])])])]))))])


        self.assertParsesToTree("=`1`", CreateParseTree("`", Number(["1"]), "`"))
        self.assertParsesToTree("=` 1 ` ", CreateParseTree("` ", Number(["1 "]), "` "))
        self.assertParsesToTree("=` fred`  ", CreateParseTree("` ", Name(["fred"]), "`  "))

        self.assertCannotParse("=``", -1)
        self.assertCannotParse("=` `", -1)
        self.assertCannotParse("=`5", -1)
        self.assertCannotParse("=`5, `", -1)


    def testComplexStringConversion(self):
        def CreateParseTree(firstQuote, tests, secondQuote):
            return FLRoot(["=", Test_AndTest_NotTest_Comparison(
                    Expr_ConcatExpr_ShiftExpr(
                        ArithExpr_Term(
                            Factor([Power([FLReference([Atom(
                                [
                                firstQuote,
                                TestList(tests),
                                secondQuote
                                ])])])]))))])


        self.assertParsesToTree(
            "=`1, 2, 3`",
            CreateParseTree(
                "`",
                [
                    TestFromAtomChild(Number(["1"])),
                    ", ",
                    TestFromAtomChild(Number(["2"])),
                    ", ",
                    TestFromAtomChild(Number(["3"])),
                ],
                "`"))

        self.assertParsesToTree(
            "=`1, 2, 3 `",
            CreateParseTree(
                "`",
                [
                    TestFromAtomChild(Number(["1"])),
                    ", ",
                    TestFromAtomChild(Number(["2"])),
                    ", ",
                    TestFromAtomChild(Number(["3 "])),
                ],
                "`"))

        self.assertParsesToTree(
            "=` cheese, 'cheese', c + heese` ",
            CreateParseTree(
                "` ",
                [
                    TestFromAtomChild(Name(["cheese"])),
                    ", ",
                    TestFromAtomChild(StringLiteral(["'cheese'"])),
                    ", ",
                    Test_AndTest_NotTest_Comparison(
                        Expr_ConcatExpr_ShiftExpr(
                            ArithExpr(
                                [
                                Term(
                                    [Factor_Power_FLReference_Atom(Name(["c "]))]),
                                "+ ",
                                Term(
                                    [Factor_Power_FLReference_Atom(Name(["heese"]))])
                                ])))

                ],
                "` "))

        self.assertCannotParse("=`5, 1", -1)
        self.assertCannotParse("=`5, 1,`", -1)


    def testEmptyParentheses(self):
        def CreateParseTree(lParen, rParen):
            return FLRoot(["=", Test_AndTest_NotTest_Comparison(
                    Expr_ConcatExpr_ShiftExpr(
                        ArithExpr_Term(
                            Factor([Power([FLReference([Atom(
                                [
                                lParen,
                                rParen
                                ])])])]))))])


        self.assertParsesToTree("=()", CreateParseTree("(", ")"))
        self.assertParsesToTree("=( )", CreateParseTree("( ", ")"))
        self.assertParsesToTree("=() ", CreateParseTree("(", ") "))
        self.assertParsesToTree("=( ) ", CreateParseTree("( ", ") "))

        self.assertCannotParse("=(", -1)
        self.assertCannotParse("=)", 2, ")")


    def testParenthesesWithSingle(self):
        def CreateParseTree(lParen, atomChild, rParen):
            return FLRoot(["=", Test_AndTest_NotTest_Comparison(
                    Expr_ConcatExpr_ShiftExpr(
                        ArithExpr_Term(
                            Factor([Power([FLReference([Atom(
                                [
                                lParen,
                                TestListGexp(
                                    [TestFromAtomChild(atomChild)]),
                                rParen
                                ])])])]))))])


        self.assertParsesToTree("=(1)", CreateParseTree("(", Number(["1"]), ")"))
        self.assertParsesToTree("=( 1 ) ", CreateParseTree("( ", Number(["1 "]), ") "))
        self.assertParsesToTree("=( fred)  ", CreateParseTree("( ", Name(["fred"]), ")  "))

        self.assertCannotParse("=(5", -1)
        self.assertCannotParse("=5)", 3, ")")


    def testComplexParentheses(self):
        def CreateParseTree(lParen, testListGexp, rParen):
            return FLRoot(["=", Test_AndTest_NotTest_Comparison(
                    Expr_ConcatExpr_ShiftExpr(
                        ArithExpr_Term(
                            Factor([Power([FLReference([Atom(
                                [
                                lParen,
                                testListGexp,
                                rParen
                                ])])])]))))])


        self.assertParsesToTree(
            "=(1, 2, 3)",
            CreateParseTree(
                "(",
                TestListGexp(
                    [
                    TestFromAtomChild(Number(["1"])),
                    ", ",
                    TestFromAtomChild(Number(["2"])),
                    ", ",
                    TestFromAtomChild(Number(["3"])),
                    ]),
                ")"))

        self.assertParsesToTree(
            "=(1, 2, 3, )",
            CreateParseTree(
                "(",
                TestListGexp(
                    [
                    TestFromAtomChild(Number(["1"])),
                    ", ",
                    TestFromAtomChild(Number(["2"])),
                    ", ",
                    TestFromAtomChild(Number(["3"])),
                    ", ",
                    ]),
                ")"))

        self.assertParsesToTree(
            "=( cheese, 'cheese', c + heese) ",
            CreateParseTree(
                "( ",
                TestListGexp(
                    [
                    TestFromAtomChild(Name(["cheese"])),
                    ", ",
                    TestFromAtomChild(StringLiteral(["'cheese'"])),
                    ", ",
                    Test_AndTest_NotTest_Comparison(
                        Expr_ConcatExpr_ShiftExpr(
                            ArithExpr(
                                [
                                Term(
                                    [Factor_Power_FLReference_Atom(Name(["c "]))]),
                                "+ ",
                                Term(
                                    [Factor_Power_FLReference_Atom(Name(["heese"]))])
                                ])))
                    ]),
                ") "))

        self.assertCannotParse("=(5, 1", -1)
        self.assertCannotParse("=5)", 3, ")")
        self.assertCannotParse("=5, 1)", 3, ", ")


    def testSimpleGeneratorExpr(self):
        def CreateParseTree(lBracket, test1, forStr, exprList, inStr, test2, rBracket):
            return FLRoot(["=", Test_AndTest_NotTest_Comparison(
                    Expr_ConcatExpr_ShiftExpr(
                        ArithExpr_Term(
                            Factor([Power([FLReference([Atom(
                                [
                                lBracket,
                                TestListGexp(
                                    [
                                    test1,
                                    GenFor(
                                        [
                                        forStr,
                                        exprList,
                                        inStr,
                                        test2
                                        ]),
                                    ]),
                                rBracket
                                ])])])]))))])

        self.assertParsesToTree("=(1 for x in L)",
            CreateParseTree(
                "(",
                TestFromAtomChild(Number(['1 '])),
                "for ",
                ExprList(
                    [ExprFromAtomChild(Name(["x "]))]),
                "in ",
                TestFromAtomChild(Name(["L"])),
                ")"
                ))

        self.assertParsesToTree("=(lambda->x for x in L)",
            CreateParseTree(
                "(",
                Test(
                    [LambDef(
                        [
                        "lambda",
                        "->",
                        TestFromAtomChild(Name(["x "]))
                        ])])
                ,
                "for ",
                ExprList(
                    [ExprFromAtomChild(Name(["x "]))]),
                "in ",
                TestFromAtomChild(Name(["L"])),
                ")"
                ))

        self.assertParsesToTree("=(1 or 2 or 3 for x in L)",
            CreateParseTree(
                "(",
                Test(
                    [
                    AndTest([NotTest([Comparison([
                                Expr_ConcatExpr_ShiftExpr(
                                    ArithExpr_Term(
                                        Factor_Power_FLReference_Atom(Number(["1 "]))))])])]),
                    "or ",
                    AndTest([NotTest([Comparison([
                                Expr_ConcatExpr_ShiftExpr(
                                    ArithExpr_Term(
                                        Factor_Power_FLReference_Atom(Number(["2 "]))))])])]),
                    "or ",
                    AndTest([NotTest([Comparison([
                                Expr_ConcatExpr_ShiftExpr(
                                    ArithExpr_Term(
                                        Factor_Power_FLReference_Atom(Number(["3 "]))))])])]),
                    ]),
                "for ",
                ExprList(
                    [ExprFromAtomChild(Name(["x "]))]),
                "in ",
                TestFromAtomChild(Name(["L"])),
                ")"
                ))


    def testComplexGeneratorExpr(self):
        def CreateParseTree(lBracket, test1, genFor, rBracket):
            return FLRoot(["=", Test_AndTest_NotTest_Comparison(
                    Expr_ConcatExpr_ShiftExpr(
                        ArithExpr_Term(
                            Factor([Power([FLReference([Atom(
                                [
                                lBracket,
                                TestListGexp(
                                    [
                                    test1,
                                    genFor,
                                    ]),
                                rBracket
                                ])])])]))))])

        self.assertParsesToTree(
            "=(x for x in L for y in M)",
            CreateParseTree(
                "(",
                TestFromAtomChild(Name(["x "])),
                GenFor(
                    [
                    "for ",
                    ExprList(
                        [ExprFromAtomChild(Name(["x "]))]),
                    "in ",
                    TestFromAtomChild(Name(["L "])),
                    GenIter(
                        [GenFor(
                            [
                            "for ",
                            ExprList(
                                [ExprFromAtomChild(Name(["y "]))]),
                            "in ",
                            TestFromAtomChild(Name(["M"])),
                            ])])
                    ]),
                ")"))

        self.assertParsesToTree(
            "=(x for x in L if a)",
            CreateParseTree(
                "(",
                TestFromAtomChild(Name(["x "])),
                GenFor(
                    [
                    "for ",
                    ExprList(
                        [ExprFromAtomChild(Name(["x "]))]),
                    "in ",
                    TestFromAtomChild(Name(["L "])),
                    GenIter(
                        [GenIf(
                            [
                            "if ",
                            TestFromAtomChild(Name(["a"])),
                            ])])
                    ]),
                ")"))

        self.assertParsesToTree(
            "=(x for x in L if a if b for q in M)",
            CreateParseTree(
                "(",
                TestFromAtomChild(Name(["x "])),
                GenFor(
                    [
                    "for ",
                    ExprList(
                        [ExprFromAtomChild(Name(["x "]))]),
                    "in ",
                    TestFromAtomChild(Name(["L "])),
                    GenIter(
                        [GenIf(
                            [
                            "if ",
                            TestFromAtomChild(Name(["a "])),
                            GenIter(
                                [GenIf(
                                    [
                                    "if ",
                                    TestFromAtomChild(Name(["b "])),
                                    GenIter(
                                        [GenFor(
                                            [
                                            "for ",
                                            ExprList(
                                                [ExprFromAtomChild(Name(["q "]))]),
                                            "in ",
                                            TestFromAtomChild(Name(["M"])),
                                            ])])
                                    ])])
                            ])])
                    ]),
                ")"))


    def testEmptyList(self):
        def CreateParseTree(lBracket, rBracket):
            return FLRoot(["=", Test_AndTest_NotTest_Comparison(
                    Expr_ConcatExpr_ShiftExpr(
                        ArithExpr_Term(
                            Factor([Power([FLReference([Atom(
                                [
                                lBracket,
                                rBracket
                                ])])])]))))])

        self.assertParsesToTree("=[ ]", CreateParseTree('[ ', ']'))
        self.assertParsesToTree("=[ ] ", CreateParseTree('[ ', '] '))
        self.assertParsesToTree("=[]", CreateParseTree('[', ']'))
        self.assertParsesToTree("=[] ", CreateParseTree('[', '] '))

        self.assertCannotParse("=[", -1)
        self.assertCannotParse("=]", 2, "]")
        self.assertCannotParse("=[[", -1)
        self.assertCannotParse("=][", 2, "]")


    def testListWithNumbers(self):
        def CreateParseTree(lBracket, tests, rBracket):
            return FLRoot(["=", Test_AndTest_NotTest_Comparison(
                    Expr_ConcatExpr_ShiftExpr(
                        ArithExpr_Term(
                            Factor([Power([FLReference([Atom(
                                [
                                lBracket,
                                ListMaker(tests),
                                rBracket
                                ])])])]))))])

        self.assertParsesToTree("=[ 3 ]",
            CreateParseTree('[ ', [TestFromAtomChild(Number(['3 ']))], ']'))
        self.assertParsesToTree("=[ 3 ,]",
            CreateParseTree('[ ', [TestFromAtomChild(Number(['3 '])), ","], ']'))
        self.assertParsesToTree("=[ 3, 4 ]",
            CreateParseTree(
                '[ ',
                [
                    TestFromAtomChild(Number(['3'])),
                    ", ",
                    TestFromAtomChild(Number(['4 '])),
                ],
                ']'))
        self.assertParsesToTree("=[ 3, 4 ,] ",
            CreateParseTree(
                '[ ',
                [
                    TestFromAtomChild(Number(['3'])),
                    ", ",
                    TestFromAtomChild(Number(['4 '])),
                    ","
                ],
                '] '))

        self.assertCannotParse("=[3 3]", 5, "3")
        self.assertCannotParse("=[3:3]", 4, ":")


    def testListWithSimple(self):
        "test list with simple for"
        def CreateParseTree(lBracket, test, forStr, exprList, inStr, testListSafe, rBracket):
            return FLRoot(["=", Test_AndTest_NotTest_Comparison(
                    Expr_ConcatExpr_ShiftExpr(
                        ArithExpr_Term(
                            Factor([Power([FLReference([Atom(
                                [
                                lBracket,
                                ListMaker(
                                    [
                                    test,
                                    ListFor(
                                        [
                                        forStr,
                                        exprList,
                                        inStr,
                                        testListSafe
                                        ])
                                    ]),
                                rBracket
                                ])])])]))))])

        self.assertParsesToTree("=[1 for x in L]",
            CreateParseTree(
                "[",
                TestFromAtomChild(Number(['1 '])),
                "for ",
                ExprList(
                    [ExprFromAtomChild(Name(["x "]))]),
                "in ",
                TestList(
                    [Test_AndTest_NotTest_Comparison(
                        Expr_ConcatExpr_ShiftExpr(
                            ArithExpr_Term(
                                Factor_Power_FLReference_Atom(Name(["L"])))))]),
                "]"
                ))

        self.assertParsesToTree("=[1 for x, y in L]",
            CreateParseTree(
                "[",
                TestFromAtomChild(Number(['1 '])),
                "for ",
                ExprList(
                    [
                    ExprFromAtomChild(Name(["x"])),
                    ", ",
                    ExprFromAtomChild(Name(["y "]))
                    ]),
                "in ",
                TestList(
                    [Test_AndTest_NotTest_Comparison(
                        Expr_ConcatExpr_ShiftExpr(
                            ArithExpr_Term(
                                Factor_Power_FLReference_Atom(Name(["L"])))))]),
                "]"
                ))


    def testListWithParenthetical(self):
        "test list with parenthetical for"
        self.assertParsesToTree("=[1 for (x, y) in L]",
            CreateParseTree(
                "[",
                TestFromAtomChild(Number(['1 '])),
                "for ",
                ExprList(
                    [Expr_ConcatExpr_ShiftExpr(
                        ArithExpr_Term(
                            Factor([Power([FLReference([Atom(
                                [
                                "(",
                                TestListGexp(
                                    [
                                    TestFromAtomChild(Name(["x"])),
                                    ", ",
                                    TestFromAtomChild(Name(["y"]))
                                    ]),
                                ") "
                                ])])])])))]),
                "in ",
                TestList(
                    [Test_AndTest_NotTest_Comparison(
                        Expr_ConcatExpr_ShiftExpr(
                            ArithExpr_Term(
                                Factor_Power_FLReference_Atom(Name(["L"])))))]),
                "]"
                ))

        self.assertParsesToTree("=[1 for [x, y, z,], in L]",
            CreateParseTree(
                "[",
                TestFromAtomChild(Number(['1 '])),
                "for ",
                ExprList(
                    [
                    Expr_ConcatExpr_ShiftExpr(
                        ArithExpr_Term(
                            Factor([Power([FLReference([Atom(
                                [
                                "[",
                                ListMaker(
                                    [
                                    TestFromAtomChild(Name(["x"])),
                                    ", ",
                                    TestFromAtomChild(Name(["y"])),
                                    ", ",
                                    TestFromAtomChild(Name(["z"])),
                                    ","
                                    ]),
                                "]"
                                ])])])]))),
                    ", "
                    ]),
                "in ",
                TestList(
                    [Test_AndTest_NotTest_Comparison(
                        Expr_ConcatExpr_ShiftExpr(
                            ArithExpr_Term(
                                Factor_Power_FLReference_Atom(Name(["L"])))))]),
                "]"
                ))
        _level2 = Test_AndTest_NotTest_Comparison(
                    Expr_ConcatExpr_ShiftExpr(
                        ArithExpr_Term(
                            Factor([Power([FLReference([Atom(
                                [
                                "[",
                                ListMaker(
                                    [
                                    TestFromAtomChild(Name(["y"])),
                                    ", ",
                                    TestFromAtomChild(Name(["z"])),
                                    ","
                                    ]),
                                "]"
                                ])])])]))))
        self.assertParsesToTree("=[1 for (x, [y, z,]), in L]",
            CreateParseTree(
                "[",
                TestFromAtomChild(Number(['1 '])),
                "for ",
                ExprList(
                    [
                    Expr_ConcatExpr_ShiftExpr(
                        ArithExpr_Term(
                            Factor([Power([FLReference([Atom(
                                [
                                "(",
                                TestListGexp(
                                    [
                                    TestFromAtomChild(Name(["x"])),
                                    ", ",
                                    _level2
                                    ]),
                                ")"
                                ])])])]))),
                    ", "
                    ]),
                "in ",
                TestList(
                    [Test_AndTest_NotTest_Comparison(
                        Expr_ConcatExpr_ShiftExpr(
                            ArithExpr_Term(
                                Factor_Power_FLReference_Atom(Name(["L"])))))]),
                "]"
                ))

        _level2 = Expr_ConcatExpr_ShiftExpr(
                    ArithExpr_Term(
                        Factor([Power([FLReference([Atom(
                            [
                            "(",
                            TestListGexp(
                                [
                                TestFromAtomChild(Name(["x"])),
                                ", ",

                                Test_AndTest_NotTest_Comparison(
                                    Expr_ConcatExpr_ShiftExpr(
                                        ArithExpr_Term(
                                            Factor([Power([FLReference([Atom(
                                                [
                                                "[",
                                                ListMaker(
                                                    [
                                                    TestFromAtomChild(Name(["y"])),
                                                    ", ",
                                                    TestFromAtomChild(Name(["z"])),
                                                    ","
                                                    ]),
                                                "]"
                                                ])])])]))))
                                ]),
                            ")"
                            ])])])])))
        self.assertParsesToTree("=[1 for (x, [y, z,]), in L, M]",
            CreateParseTree(
                "[",
                TestFromAtomChild(Number(['1 '])),
                "for ",
                ExprList(
                    [
                    _level2,
                    ", "
                    ]),
                "in ",
                TestList(
                    [
                    Test_AndTest_NotTest_Comparison(
                        Expr_ConcatExpr_ShiftExpr(
                            ArithExpr_Term(
                                Factor_Power_FLReference_Atom(Name(["L"]))))),
                    ", ",
                    Test_AndTest_NotTest_Comparison(
                        Expr_ConcatExpr_ShiftExpr(
                            ArithExpr_Term(
                                Factor_Power_FLReference_Atom(Name(["M"])))))
                    ]),
                "]"
                ))

        _level2 = TestListGexp(
                    [
                    TestFromAtomChild(Name(["x"])),
                    ", ",

                    Test_AndTest_NotTest_Comparison(
                        Expr_ConcatExpr_ShiftExpr(
                            ArithExpr_Term(
                                Factor([Power([FLReference([Atom(
                                    [
                                    "[",
                                    ListMaker(
                                        [
                                        TestFromAtomChild(Name(["y"])),
                                        ", ",
                                        TestFromAtomChild(Name(["z"])),
                                        ","
                                        ]),
                                    "]"
                                    ])])])]))))
                    ])
        self.assertParsesToTree("=[1 for (x, [y, z,]), in L or M]",
            CreateParseTree(
                "[",
                TestFromAtomChild(Number(['1 '])),
                "for ",
                ExprList(
                    [
                    Expr_ConcatExpr_ShiftExpr(
                        ArithExpr_Term(
                            Factor([Power([FLReference([Atom(
                                [
                                "(",
                                _level2,
                                ")"
                                ])])])]))),
                    ", "
                    ]),
                "in ",
                TestList(
                    [
                    Test(
                        [
                        AndTest([NotTest([Comparison(
                            [Expr_ConcatExpr_ShiftExpr(
                                ArithExpr_Term(
                                    Factor_Power_FLReference_Atom(Name(["L "]))))])])]),
                        "or ",
                        AndTest([NotTest([Comparison(
                            [Expr_ConcatExpr_ShiftExpr(
                                ArithExpr_Term(
                                    Factor_Power_FLReference_Atom(Name(["M"]))))])])]),
                        ])
                    ]),
                "]"
                ))

        _level2 = TestListGexp(
                    [
                    TestFromAtomChild(Name(["x"])),
                    ", ",

                    Test_AndTest_NotTest_Comparison(
                        Expr_ConcatExpr_ShiftExpr(
                            ArithExpr_Term(
                                Factor([Power([FLReference([Atom(
                                    [
                                    "[",
                                    ListMaker(
                                        [
                                        TestFromAtomChild(Name(["y"])),
                                        ", ",
                                        TestFromAtomChild(Name(["z"])),
                                        ","
                                        ]),
                                    "]"
                                    ])])])]))))
                    ])
        self.assertParsesToTree("=[1 for (x, [y, z,]), in L or M or N]",
            CreateParseTree(
                "[",
                TestFromAtomChild(Number(['1 '])),
                "for ",
                ExprList(
                    [
                    Expr_ConcatExpr_ShiftExpr(
                        ArithExpr_Term(
                            Factor([Power([FLReference([Atom(
                                [
                                "(",
                                    _level2,
                                ")"
                                ])])])]))),
                    ", "
                    ]),
                "in ",
                TestList(
                    [
                    Test(
                        [
                        AndTest([NotTest([Comparison(
                            [Expr_ConcatExpr_ShiftExpr(
                                ArithExpr_Term(
                                    Factor_Power_FLReference_Atom(Name(["L "]))))])])]),
                        "or ",
                        AndTest([NotTest([Comparison(
                            [Expr_ConcatExpr_ShiftExpr(
                                ArithExpr_Term(
                                    Factor_Power_FLReference_Atom(Name(["M "]))))])])]),
                        "or ",
                        AndTest([NotTest([Comparison(
                            [Expr_ConcatExpr_ShiftExpr(
                                ArithExpr_Term(
                                    Factor_Power_FLReference_Atom(Name(["N"]))))])])]),
                        ])
                    ]),
                "]"
                ))

        _level2 = TestListGexp(
                    [
                    TestFromAtomChild(Name(["x"])),
                    ", ",

                    Test_AndTest_NotTest_Comparison(
                        Expr_ConcatExpr_ShiftExpr(
                            ArithExpr_Term(
                                Factor([Power([FLReference([Atom(
                                    [
                                    "[",
                                    ListMaker(
                                        [
                                        TestFromAtomChild(Name(["y"])),
                                        ", ",
                                        TestFromAtomChild(Name(["z"])),
                                        ","
                                        ]),
                                    "]"
                                    ])])])]))))
                    ])
        self.assertParsesToTree("=[1 for (x, [y, z,]), in lambda -> 1]",
            CreateParseTree(
                "[",
                TestFromAtomChild(Number(['1 '])),
                "for ",
                ExprList(
                    [
                    Expr_ConcatExpr_ShiftExpr(
                        ArithExpr_Term(
                            Factor([Power([FLReference([Atom(
                                [
                                "(",
                                    _level2,
                                ")"
                                ])])])]))),
                    ", "
                    ]),
                "in ",
                TestList(
                    [Test(
                        [LambDef(
                            [
                            "lambda ",
                            "-> ",
                            TestFromAtomChild(Number(["1"]))
                            ])])]),
                "]"
                ))

        self.assertCannotParse("=[1 for (x, [y, z,)], in L]", 19, ")")
        self.assertCannotParse("=[1 for (x, [y, z,]), in L or M,]", 33, "]")
        self.assertCannotParse("=[1 for (x, [y, z,]), in L, M,]", 31, "]") # deviation from Python!


    def testListWithList(self):
        "test list with list iter"
        def CreateParseTree(lBracket, test, listFor, rBracket):
            return FLRoot(["=", Test_AndTest_NotTest_Comparison(
                    Expr_ConcatExpr_ShiftExpr(
                        ArithExpr_Term(
                            Factor([Power([FLReference([Atom(
                                [
                                lBracket,
                                ListMaker(
                                    [
                                    test,
                                    listFor
                                    ]),
                                rBracket
                                ])])])]))))])

        self.assertParsesToTree(
            "=[x for x in L for y in M]",
            CreateParseTree(
                "[",
                TestFromAtomChild(Name(["x "])),
                ListFor(
                    [
                    "for ",
                    ExprList([ExprFromAtomChild(Name(["x "]))]),
                    "in ",
                    TestList(
                        [Test(
                            [AndTest(
                                [NotTest(
                                    [Comparison(
                                        [Expr_ConcatExpr_ShiftExpr(
                                            ArithExpr_Term(
                                                Factor_Power_FLReference_Atom(Name(["L "]))))])])])])]),
                    ListIter(
                        [ListFor(
                            [
                            "for ",
                            ExprList([ExprFromAtomChild(Name(["y "]))]),
                            "in ",
                            TestList(
                                [Test(
                                    [AndTest(
                                        [NotTest(
                                            [Comparison(
                                                [Expr_ConcatExpr_ShiftExpr(
                                                    ArithExpr_Term(
                                                        Factor_Power_FLReference_Atom(Name(["M"]))))])])])])]),
                            ])])
                    ]),
                "]")
            )

        self.assertParsesToTree(
            "=[x for x in L if Y]",
            CreateParseTree(
                "[",
                TestFromAtomChild(Name(["x "])),
                ListFor(
                    [
                    "for ",
                    ExprList([ExprFromAtomChild(Name(["x "]))]),
                    "in ",
                    TestList(
                        [Test(
                            [AndTest(
                                [NotTest(
                                    [Comparison(
                                        [Expr_ConcatExpr_ShiftExpr(
                                            ArithExpr_Term(
                                                Factor_Power_FLReference_Atom(Name(["L "]))))])])])])]),
                    ListIter(
                        [ListIf(
                            [
                            "if ",
                            Test(
                                [AndTest(
                                    [NotTest(
                                        [Comparison(
                                            [Expr_ConcatExpr_ShiftExpr(
                                                ArithExpr_Term(
                                                    Factor_Power_FLReference_Atom(Name(["Y"]))))])])])])
                            ])])
                    ]),
                "]")
            )

        self.assertParsesToTree(
            "=[x for x in L if Y for a in b]",
            CreateParseTree(
                "[",
                TestFromAtomChild(Name(["x "])),
                ListFor(
                    [
                    "for ",
                    ExprList([ExprFromAtomChild(Name(["x "]))]),
                    "in ",
                    TestList(
                        [Test(
                            [AndTest(
                                [NotTest(
                                    [Comparison(
                                        [Expr_ConcatExpr_ShiftExpr(
                                            ArithExpr_Term(
                                                Factor_Power_FLReference_Atom(Name(["L "]))))])])])])]),
                    ListIter(
                        [ListIf(
                            [
                            "if ",
                            Test(
                                [AndTest(
                                    [NotTest(
                                        [Comparison(
                                            [Expr_ConcatExpr_ShiftExpr(
                                                ArithExpr_Term(
                                                    Factor_Power_FLReference_Atom(Name(["Y "]))))])])])]),
                            ListIter(
                                [ListFor(
                                    [
                                    "for ",
                                    ExprList([ExprFromAtomChild(Name(["a "]))]),
                                    "in ",
                                    TestList(
                                        [Test(
                                            [AndTest(
                                                [NotTest(
                                                    [Comparison(
                                                        [Expr_ConcatExpr_ShiftExpr(
                                                            ArithExpr_Term(
                                                                Factor_Power_FLReference_Atom(Name(["b"]))))])])])])]),
                                    ])])
                            ])])
                    ]),
                "]")
            )

        self.assertParsesToTree(
            "=[x for x in L if Y if Z]",
            CreateParseTree(
                "[",
                TestFromAtomChild(Name(["x "])),
                ListFor(
                    [
                    "for ",
                    ExprList([ExprFromAtomChild(Name(["x "]))]),
                    "in ",
                    TestList(
                        [Test(
                            [AndTest(
                                [NotTest(
                                    [Comparison(
                                        [Expr_ConcatExpr_ShiftExpr(
                                            ArithExpr_Term(
                                                Factor_Power_FLReference_Atom(Name(["L "]))))])])])])]),
                    ListIter(
                        [ListIf(
                            [
                            "if ",
                            Test(
                                [AndTest(
                                    [NotTest(
                                        [Comparison(
                                            [Expr_ConcatExpr_ShiftExpr(
                                                ArithExpr_Term(
                                                    Factor_Power_FLReference_Atom(Name(["Y "]))))])])])]),
                            ListIter(
                                [ListIf(
                                    [
                                    "if ",
                                    Test(
                                        [AndTest(
                                            [NotTest(
                                                [Comparison(
                                                    [Expr_ConcatExpr_ShiftExpr(
                                                        ArithExpr_Term(
                                                            Factor_Power_FLReference_Atom(Name(["Z"]))))])])])])
                                    ])])
                            ])])
                    ]),
                "]")
            )


    def testEmptyDict(self):
        def CreateParseTree(lBrace, rBrace):
            return FLRoot(["=", Test_AndTest_NotTest_Comparison(
                    Expr_ConcatExpr_ShiftExpr(
                        ArithExpr_Term(
                            Factor([Power([FLReference([Atom(
                                [
                                lBrace,
                                rBrace
                                ])])])]))))])


        self.assertParsesToTree("={}", CreateParseTree("{", "}"))
        self.assertParsesToTree("={ }", CreateParseTree("{ ", "}"))
        self.assertParsesToTree("={} ", CreateParseTree("{", "} "))
        self.assertParsesToTree("={ } ", CreateParseTree("{ ", "} "))

        self.assertCannotParse("={", -1)
        self.assertCannotParse("=}", 2, "}")


    def testSimpleDict(self):
        def CreateParseTree(lBrace, keyAtomChild, littleArrow, valueAtomChild, rBrace):
            return FLRoot(["=", Test_AndTest_NotTest_Comparison(
                    Expr_ConcatExpr_ShiftExpr(
                        ArithExpr_Term(
                            Factor([Power([FLReference([Atom(
                                [
                                lBrace,
                                DictMaker(
                                    [
                                    TestFromAtomChild(keyAtomChild),
                                    littleArrow,
                                    TestFromAtomChild(valueAtomChild)
                                    ]),
                                rBrace
                                ])])])]))))])


        self.assertParsesToTree("={1->2}", CreateParseTree("{", Number(["1"]), "->", Number(["2"]), "}"))
        self.assertParsesToTree("={ 1 -> 'cheese' } ", CreateParseTree("{ ", Number(["1 "]), "-> ", StringLiteral(["'cheese' "]), "} "))
        self.assertParsesToTree("={ '' ->fred}  ", CreateParseTree("{ ", StringLiteral(["'' "]), "->", Name(["fred"]), "}  "))

        self.assertCannotParse("={5", -1)
        self.assertCannotParse("={5}", 4, "}")
        self.assertCannotParse("={5->}", 6, "}")
        self.assertCannotParse("={->5}", 3, "->")


    def testComplexDictDisplay(self):
        def CreateParseTree(lBrace, dictMaker, rBrace):
            return FLRoot(["=", Test_AndTest_NotTest_Comparison(
                    Expr_ConcatExpr_ShiftExpr(
                        ArithExpr_Term(
                            Factor([Power([FLReference([Atom(
                                [
                                lBrace,
                                dictMaker,
                                rBrace
                                ])])])]))))])

        self.assertParsesToTree(
            "={1->2,}",
            CreateParseTree(
                "{",
                DictMaker(
                    [
                    TestFromAtomChild(Number(["1"])),
                    "->",
                    TestFromAtomChild(Number(["2"])),
                    ",",
                    ]),
                "}"))

        self.assertParsesToTree(
            "={1->2,3->4}",
            CreateParseTree(
                "{",
                DictMaker(
                    [
                    TestFromAtomChild(Number(["1"])),
                    "->",
                    TestFromAtomChild(Number(["2"])),
                    ",",
                    TestFromAtomChild(Number(["3"])),
                    "->",
                    TestFromAtomChild(Number(["4"])),
                    ]),
                "}"))

        self.assertParsesToTree(
            "={ 1 -> 2 , 'foo' '''bar''' -> angry  ,} ",
            CreateParseTree(
                "{ ",
                DictMaker(
                    [
                    TestFromAtomChild(Number(["1 "])),
                    "-> ",
                    TestFromAtomChild(Number(["2 "])),
                    ", ",
                    TestFromAtomChild(StringLiteral(["'foo' ", "'''bar''' "])),
                    "-> ",
                    TestFromAtomChild(Name(["angry  "])),
                    ","
                    ]),
                "} "))

        self.assertParsesToTree(
            "={ 1 -> c + 'heese' , }",
            CreateParseTree(
                "{ ",
                DictMaker(
                    [
                    TestFromAtomChild(Number(["1 "])),
                    "-> ",
                    Test_AndTest_NotTest_Comparison(
                        Expr_ConcatExpr_ShiftExpr(
                            ArithExpr(
                                [
                                Term(
                                    [Factor_Power_FLReference_Atom(Name(["c "]))]),
                                "+ ",
                                Term(
                                    [Factor_Power_FLReference_Atom(StringLiteral(["'heese' "]))])
                                ]))),
                    ", "
                    ]),
                "}"))


        self.assertCannotParse("=(5, 1", -1)


    def testOtherErrors(self):
        self.assertCannotParse("=b6+'64654", 5, "'64654")
        self.assertCannotParse("=\\", 2, "\\")
        self.assertCannotParse("=hello'world'", 7, "'world'")


    def testIfFunctionCalls(self):
        def CreateParseTree(nameChild, trailers):
            return FLRoot(["=", TestFromFlReferenceChildren([Atom([Name([nameChild])]), Trailer(trailers)])])


        self.assertCannotParse("=if(a)", 6, ')')
        self.assertCannotParse("=if(a, b, c, d)", 12, ', ')
        self.assertParsesToTree(
            "=If(1, 2, 3)",
            CreateParseTree("If",
                ['(',
                 Argument([TestFromAtomChild(Number(["1"]))]),
                 ', ',
                 Argument([TestFromAtomChild(Number(["2"]))]),
                 ', ',
                 Argument([TestFromAtomChild(Number(["3"]))]),
                 ')'])
            )
        self.assertParsesToTree(
            "=if(1, 2, 3)()",
            FLRoot(
                [
                    "=",
                    TestFromFlReferenceChildren(
                        [
                            Atom([Name(["if"])]),
                            Trailer(
                                [
                                    '(',
                                    Argument([TestFromAtomChild(Number(["1"]))]),
                                    ', ',
                                    Argument([TestFromAtomChild(Number(["2"]))]),
                                    ', ',
                                    Argument([TestFromAtomChild(Number(["3"]))]),
                                    ')'
                                ]
                            ),
                            Trailer(['(', ')'])
                        ]
                    )
                ]
            )
        )

        self.assertParsesToTree(
            "=iF(A1:B1, B2, C2)",
            CreateParseTree("iF",
                ['(',
                 ArgumentFromFLReferenceChild(FLCellRange(
                    [
                    FLCellReference(["A1"]),
                    ":",
                    FLCellReference(["B1"])
                    ])),
                 ', ',
                 ArgumentFromFLReferenceChild(FLCellReference(["B2"])),
                 ', ',
                 ArgumentFromFLReferenceChild(FLCellReference(["C2"])),
                 ')'])
            )

        self.assertParsesToTree(
            "=If(a=1, 2, 3)",
            CreateParseTree("If",
                ['(',
                 Argument([CreateComparison(Name(['a']), '=', Number(['1']))]),
                 ', ',
                 Argument([TestFromAtomChild(Number(["2"]))]),
                 ', ',
                 Argument([TestFromAtomChild(Number(["3"]))]),
                 ')'])
            )
        self.assertParsesToTree(
            "=If(a=1, 2,)",
            CreateParseTree("If",
                ['(',
                 Argument([CreateComparison(Name(['a']), '=', Number(['1']))]),
                 ', ',
                 Argument([TestFromAtomChild(Number(["2"]))]),
                 ',',
                 ')'])
            )
        self.assertParsesToTree(
            "=If(a=1, 2)",
            CreateParseTree("If",
                ['(',
                 Argument([CreateComparison(Name(['a']), '=', Number(['1']))]),
                 ', ',
                 Argument([TestFromAtomChild(Number(["2"]))]),
                 ')'])
            )



        def Sum(name, lBracket, argList, rBracket):
            return Argument([CreateTest(name, lBracket, argList, rBracket)])

        self.assertParsesToTree(
            "=if(sum(A1:B1), functionCall(1, 2), sum for sum in L if sum)",
            CreateParseTree("if",
                ['(',
                 Sum(
                    "sum",
                    "(",
                    [
                        ArgumentFromFLReferenceChild(FLCellRange(
                            [
                            FLCellReference(["A1"]),
                            ":",
                            FLCellReference(["B1"])
                            ]))
                    ],
                    ")"),
                  ", ",
                  Argument([TestFromFlReferenceChildren(
                        [Atom([Name(["functionCall"])]),
                         Trailer(["(",
                                  ArgList([Argument([TestFromAtomChild(Number(["1"]))]),
                                           ", ",
                                           Argument([TestFromAtomChild(Number(["2"]))])
                                           ]),
                                  ")"
                              ])
                         ])]),
                 ", ",
                 Argument([TestFromAtomChild(Name(["sum "])),
                           GenFor(
                               [
                               "for ",
                               ExprList(
                                   [ExprFromAtomChild(Name(["sum "]))]),
                               "in ",
                               TestFromAtomChild(Name(["L "])),
                               GenIter(
                                   [GenIf(
                                       [
                                       "if ",
                                       TestFromAtomChild(Name(["sum"])),
                                       ])])

                ])]),
                 ')'
                ]
            )
        )


    def testAndOrFunctions(self):
        self.checkFunction("and")
        self.checkFunction("or")


    def testISE(self):
        "test i s e r r o r function calls"
        def CreateParseTree(nameChild, trailers):
            return FLRoot(["=", TestFromFlReferenceChildren([Atom([Name([nameChild])]), Trailer(trailers)])])


        self.assertCannotParse("=iserror()", 10, ')')
        self.assertCannotParse("=iserror(a, b)", 11, ', ')

        self.assertParsesToTree(
            "=isError(1)",
            CreateParseTree("isError",
                ['(',
                 Argument([Test_AndTest_NotTest_Comparison(ExprFromAtomChild(Number(["1"])))]),
                 ')'])
            )

        self.assertParsesToTree(
            "=iserrOR(A1)",
            CreateParseTree("iserrOR",
                ['(',
                 ArgumentFromFLReferenceChild(FLCellReference(["A1"])),
                 ')'])
            )

        self.assertParsesToTree(
            "=iserror(9 and 9)",
            CreateParseTree("iserror",
                ['(',
                 Argument([CreateAndTest(Number(["9 "]), "and ", Number(["9"]))]),
                 ')'])
            )


    def checkFunction(self, functionName):
        def CreateParseTree(nameChild, trailers):
            return FLRoot(["=", TestFromFlReferenceChildren([Atom([Name([nameChild])]), Trailer(trailers)])])

        upper = functionName.upper()
        self.assertCannotParse("=%s" % upper, -1, "")
        self.assertCannotParse("=%s()" % upper, len(upper) + 3, ")")
        self.assertParsesToTree(
            "=%s(1)" % upper,
            CreateParseTree(upper, ['(', ArgList([Argument([TestFromAtomChild(Number(["1"]))])]), ')'])
            )
        self.assertParsesToTree(
            "=%s(1, 2, 3)" % functionName,
            CreateParseTree(functionName,
                ['(', ArgList([
                    Argument([TestFromAtomChild(Number(["1"]))]),
                    ', ',
                    Argument([TestFromAtomChild(Number(["2"]))]),
                    ', ',
                    Argument([TestFromAtomChild(Number(["3"]))])
                    ]),
                 ')'])
            )

        self.assertParsesToTree(
            "=%s(A1)" % functionName.title(),
            CreateParseTree(functionName.title(),
                ['(', ArgList([
                    ArgumentFromFLReferenceChild(FLCellReference(["A1"]))]),
                 ')'])
            )

        self.assertParsesToTree(
            "=%s(A1:B1)" % upper,
            CreateParseTree(upper,
                ['(', ArgList([
                    ArgumentFromFLReferenceChild(
                        FLCellRange(
                            [
                            FLCellReference(["A1"]),
                            ":",
                            FLCellReference(["B1"])
                            ]))]),
                 ')'])
            )

        self.assertParsesToTree(
            "=%s(6 and 6, A3)" % upper,
            CreateParseTree(upper,
                ['(', ArgList([
                    Argument([
                        CreateAndTest(Number(["6 "]), "and ", Number(["6"]))
                        ]),

                    ", ",
                    ArgumentFromFLReferenceChild(FLCellReference(["A3"]))
                    ]),
                 ')'])
            )


    def testCannotUseInappropriate(self):
        "test cannot use inappropriate keywords in expressions"
        def AssertKeywordError(keyword):
            try:
                parse("=" + keyword)
                self.fail("expected failure")
            except FormulaError, e:
                self.assertEquals(str(e), "Error in formula at position 1: '%s' is a reserved word" % keyword)

        self.assertCannotParse("=and", -1)
        AssertKeywordError("assert")
        AssertKeywordError("break")
        AssertKeywordError("class")
        AssertKeywordError("continue")
        AssertKeywordError("def")
        AssertKeywordError("del")
        AssertKeywordError("elif")
        AssertKeywordError("else")
        AssertKeywordError("except")
        AssertKeywordError("exec")
        AssertKeywordError("finally")
        self.assertCannotParse("=for", 2, "for")
        AssertKeywordError("from")
        AssertKeywordError("global")
        self.assertCannotParse("=if", -1)
        AssertKeywordError("import")
        self.assertCannotParse("=in", 2, "in")
        self.assertCannotParse("=is", 2, "is")
        self.assertCannotParse("=lambda", -1)
        self.assertCannotParse("=not", -1)
        self.assertCannotParse("=or", -1)
        AssertKeywordError("pass")
        AssertKeywordError("print")
        AssertKeywordError("raise")
        AssertKeywordError("return")
        AssertKeywordError("try")
        AssertKeywordError("while")


    def testCellRefLike(self):
        "test cell ref like name atttributes"

        self.assertParsesToFLReferenceChildren("=something.A1", [
            Atom([Name(["something"])]),
            Trailer([".", Name(["A1"])])
        ])
        self.assertParsesToFLReferenceChildren("=something.AAAAAA", [
            Atom([Name(["something"])]),
            Trailer([".", Name(["AAAAAA"])])
        ])
        self.assertParsesToFLReferenceChildren("=something.A1.Top2", [
            Atom([Name(["something"])]),
            Trailer([".", Name(["A1"])]),
            Trailer([".", Name(["Top2"])])
         ])

        self.assertParsesToFLReferenceChildren("=something.A1()", [
            Atom([Name(["something"])]),
            Trailer([".", Name(["A1"])]),
            Trailer(["(", ')'])
        ])
        self.assertParsesToFLReferenceChildren("=something.  A2", [
            Atom([Name(["something"])]),
            Trailer([".  ", Name(["A2"])])
        ])
        self.assertParsesToFLReferenceChildren("=something.\tA3", [
            Atom([Name(["something"])]),
            Trailer([".\t", Name(["A3"])])
        ])



    def testMissingParametersIn(self):
        "test missing parameters in arg list"
        def TestFromName(name):
            return TestFromAtomChild(Name([name]))
        x = TestFromName('x')
        empty = TestFromName('')
        def CreateParseTree(argList):
            return FLRoot(["=", CreateTest('foo', '(', argList,')')])

        self.assertParsesToTree('=foo(,)', CreateParseTree([empty, ',']))
        self.assertParsesToTree('=foo(, ,)', CreateParseTree([empty, ', ', empty, ',']))
        self.assertParsesToTree('=foo(,, ,)', CreateParseTree([empty, ',', empty, ', ', empty, ',']))
        self.assertParsesToTree('=foo(x,)', CreateParseTree([x, ',']))
        self.assertParsesToTree('=foo(, x)', CreateParseTree([empty, ', ', x]))
        self.assertParsesToTree('=foo(x, , x)', CreateParseTree([x, ', ', empty, ', ', x]))
        self.assertParsesToTree('=foo(x, x, )', CreateParseTree([x, ', ', x, ', ']))
        self.assertParsesToTree('=foo(, x, x)', CreateParseTree([empty, ', ', x, ', ', x]))
        self.assertParsesToTree('=foo(, x, )', CreateParseTree([empty, ', ', x, ', ']))


    def testMissingParametersIn2(self):
        "test missing parameters in arg list with args and kwargs"
        empty = Argument([TestFromAtomChild(Name(['']))])

        def CreateParseTree(argListChildren):
            return FLRoot(["=", Test_AndTest_NotTest_Comparison(
                Expr_ConcatExpr_ShiftExpr(
                        ArithExpr_Term(
                            Factor(
                                [Power(
                                    [FLReference(
                                        [
                                        Atom([Name(['foo'])]),
                                        Trailer(
                                            [
                                            '(',
                                            ArgList(argListChildren),
                                            ')'
                                            ])
                                        ])])]))))])



        self.assertParsesToTree('=foo(, *x)', CreateParseTree([empty, ', ', '*', TestFromAtomChild(Name(["x"]))]))
        self.assertParsesToTree('=foo(, **x)', CreateParseTree([empty, ', ', '**', TestFromAtomChild(Name(["x"]))]))
        keyword = Argument([TestFromAtomChild(Name(["c"])),
                            ":=",
                            TestFromAtomChild(Number(["1"]))
                            ])
        self.assertParsesToTree('=foo(, c:=1)', CreateParseTree([empty, ', ', keyword]))

        self.assertCannotParse('=foo(*args, , )', 13, ', ')
        self.assertCannotParse('=foo(bar, *args, **kwargs, , )', 26, ', ')
        self.assertCannotParse('=foo(bar, *args, , **kwargs)', 18, ', ')



class ParserModuleTest(unittest.TestCase):

    def test_reloading_module_should_not_regenerate_parsetab(self):
        # NB the parser reads the file parsetab.py, but writes to the filename below.  This
        # means that if you want it to not regenerate the parsetab every time the module is
        # loaded, having updated the grammar since parsetab.py was written and thus made a
        # regeneration necessary, you need to copy the written file on top of the one that is
        # read.
        parseTabWriteTime = os.path.getmtime("sheet/parser/parsetab.py")

        import dirigible.sheet.parser.parser as ParserModule
        reload(ParserModule)
        self.assertEquals(os.path.getmtime("sheet/parser/parsetab.py"),
                          parseTabWriteTime,
                          "ParseTab was written to by reload")

    def test_multithreaded_parsing_works(self):
        def hammer_parser(errors):
            start = time.clock()
            while time.clock() - start < 1:
                try:
                    parse("=a1 + a2 + a3")
                except Exception, e:
                    errors.append(e)

        thread_count = 2
        threads = []
        for t in range(thread_count):
            errors = []
            thread = Thread(target=lambda: hammer_parser(errors))
            thread.errors = errors
            thread.start()
            threads.append(thread)

        # Join to all of the threads but just raise the first error
        first_error = None
        for thread in threads:
            thread.join()
            if thread.errors:
                first_error = thread.errors[1]
        if first_error:
            raise first_error
