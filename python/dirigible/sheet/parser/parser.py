# Copyright (c) 2005-2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

import os
from ply import lex
from ply import yacc
from threading import Lock

from . import grammar, tokens


_parser = yacc.yacc(
    module=grammar,
    outputdir=os.path.dirname(__file__),
    method="LALR",
    debug=0,
    tabmodule='sheet.parser.parsetab'
)
_lexer = lex.lex(tokens)

_parser_lock = Lock()


def parse(string):
    _parser_lock.acquire()
    try:
        return _parser.parse(string, _lexer)
    finally:
        _parser_lock.release()

