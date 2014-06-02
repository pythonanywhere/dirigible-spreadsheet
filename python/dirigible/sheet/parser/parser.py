# Copyright (c) 2005-2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

import os
from ply import lex
from ply import yacc
from threading import Lock

import dirigible.sheet.parser.grammar


_parser = yacc.yacc(
    module=dirigible.sheet.parser.grammar,
    outputdir=os.path.dirname(__file__),
    method="LALR",
    debug=0,
    tabmodule='dirigible.sheet.parser.parsetab'
)
_lexer = lex.lex(dirigible.sheet.parser.tokens)

_parser_lock = Lock()


def parse(string):
    _parser_lock.acquire()
    try:
        return _parser.parse(string, _lexer)
    finally:
        _parser_lock.release()

