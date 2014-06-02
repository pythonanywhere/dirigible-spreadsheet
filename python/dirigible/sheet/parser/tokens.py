# Copyright (c) 2005-2009 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

import re

from dirigible.sheet.parser import FormulaError



# Precedence:
#  http://www.dabeaz.com/ply/ply.html#ply_nn4
#  1. All tokens defined by functions are added in the same order as they appear in the lexer file.
#  2. Tokens defined by strings are added next by sorting them in order of decreasing regular expression length (longer expressions are added first).
#  i.e function at lower line number > function at higher line number > long regexp string > short regexp string


## LEX rules

tokens = (
    "AMPERSAND",
    "AND",
    "BACKWARDQUOTE",
    "CIRCUMFLEX",
    "COLON",
    "COLONEQUALS",
    "COMMA",
    "DECINTEGER",
    "DLONGSTRING",
    "DOT",
    "DOUBLESLASH",
    "DOUBLESTAR",
    "DSHORTSTRING",
    "ELLIPSIS",
    "EXCLAMATION",
    "EQUALS",
    "EQUALTO",
    "FLCELLREFLIKENAME",
    "FLCOLUMNREFLIKENAME",
    "FLROWREFLIKENAME",
    "FLDELETEDREFERENCE",
    "FLINVALIDREFERENCE",
    "FLNAKEDWORKSHEETREFERENCE",
    "FLNAMEDCOLUMNREFERENCE",
    "FLNAMEDROWREFERENCE",
    "FLOATNUMBER",
    "FOR",
    "GREATEREQUAL",
    "GREATERTHAN",
    "HEXINTEGER",
    "IF",
    "IMAGINARY",
    "IN",
    "IS",
    "ISERR",
    "ISERROR",
    "LAMBDA",
    "LEFTBRACE",
    "LEFTBRACKET",
    "LEFTPAREN",
    "LEFTSHIFT",
    "LESSEQUAL",
    "LESSTHAN",
    "LITTLEARROW",
    "LONGCELLREFERENCE",
    "LONGCOLUMNREFERENCE",
    "LONGNAMEDCOLUMNREFERENCE",
    "LONGNAMEDROWREFERENCE",
    "LONGROWREFERENCE",
    "LONGDELETEDREFERENCE",
    "LONGINVALIDREFERENCE",
    "MINUS",
    "MOD_ITERP",
    "NAME",
    "NOT",
    "OBSOLETEUNEQUAL",
    "OCTINTEGER",
    "OR",
    "PERCENT",
    "PLUS",
    "RIGHTBRACE",
    "RIGHTBRACKET",
    "RIGHTPAREN",
    "RIGHTSHIFT",
    "SLASH",
    "SLONGSTRING",
    "SSHORTSTRING",
    "STAR",
    "TILDE",
    "UNEQUAL",
    "VERTICALBAR",
)


# Utility regexps
WHITESPACE    = r'[ \t]*'
STRINGPREFIX  = r'(?:[uUrR]|[uU][rR])?'
POINTFLOAT    = r'(?:[0-9]*\.[0-9]+|[0-9]+\.[0-9]*)'
EXPONENTFLOAT = r'(?:[0-9]+|' + POINTFLOAT + ')[eE][+-]?[0-9]+'
FLOATNUMBER   = r'(?:' + EXPONENTFLOAT + '|' + POINTFLOAT + ')'
WORKSHEETNAME = r"'(?:[^']|'')*'" + WHITESPACE + '!' + WHITESPACE
CELLREFLIKENAME = r'\$?[A-Za-z]+\$?[1-9][0-9]*'
COLUMNREFLIKENAME = r'\$?[A-Za-z]+_'
NAMEDCOLUMNREFERENCE = r'\#(?:[^\#]|\#\#)+\#_'
NAMEDROWREFERENCE = r'_\#(?:[^\#]|\#\#)+\#'
ROWREFLIKENAME = r'_\$?[1-9][0-9]*'

# Regexps for lower=precedence tokens
t_EXCLAMATION      = r'!' + WHITESPACE
t_PLUS             = r'\+' + WHITESPACE
t_MINUS            = r'-' + WHITESPACE
t_TILDE            = r'~' + WHITESPACE
t_DOUBLESTAR       = r'\*\*' + WHITESPACE
t_STAR             = r'\*' + WHITESPACE
t_SLASH            = r'/' + WHITESPACE
t_DOUBLESLASH      = r'//' + WHITESPACE
t_PERCENT          = r'\%' + WHITESPACE
t_MOD_ITERP        = r'\%\%' + WHITESPACE
t_LEFTSHIFT        = r'<<' + WHITESPACE
t_RIGHTSHIFT       = r'>>' + WHITESPACE
t_AMPERSAND        = r'&' + WHITESPACE
t_CIRCUMFLEX       = r'\^' + WHITESPACE
t_VERTICALBAR      = r'\|' + WHITESPACE
t_LESSTHAN         = r'<' + WHITESPACE
t_GREATERTHAN      = r'>' + WHITESPACE
t_EQUALTO          = r'==' + WHITESPACE
t_COLONEQUALS      = r':=' + WHITESPACE
t_GREATEREQUAL     = r'>=' + WHITESPACE
t_LESSEQUAL        = r'<=' + WHITESPACE
t_UNEQUAL          = r'!=' + WHITESPACE
t_OBSOLETEUNEQUAL  = r'<>' + WHITESPACE
t_LITTLEARROW      = r'->' + WHITESPACE
t_COLON            = r':' + WHITESPACE
t_LEFTPAREN        = r'\(' + WHITESPACE
t_RIGHTPAREN       = r'\)' + WHITESPACE
t_LEFTBRACE        = r'{' + WHITESPACE
t_RIGHTBRACE       = r'}' + WHITESPACE
t_LEFTBRACKET      = r'\[' + WHITESPACE
t_RIGHTBRACKET     = r'\]' + WHITESPACE
t_COMMA            = r',' + WHITESPACE
t_EQUALS           = r'=' + WHITESPACE
t_BACKWARDQUOTE    = r'`' + WHITESPACE
t_DOT              = r'\.' + WHITESPACE
t_ELLIPSIS         = r'\.\.\.' + WHITESPACE

t_FLNAMEDCOLUMNREFERENCE = NAMEDCOLUMNREFERENCE + WHITESPACE
t_FLDELETEDREFERENCE = r'\#Deleted!' + WHITESPACE
t_FLINVALIDREFERENCE = r'\#Invalid!' + WHITESPACE


def TokenRule(docstring):
    def decorator(f):
        f.__doc__ = docstring
        return f
    return decorator

# Functions for tokens (which get higher precedence)

@TokenRule(r"<'(?:[^']|'')*'>" + WHITESPACE)
def t_FLNAKEDWORKSHEETREFERENCE(t) : return t

@TokenRule(WORKSHEETNAME + CELLREFLIKENAME + WHITESPACE)
def t_LONGCELLREFERENCE(t): return t

@TokenRule(WORKSHEETNAME + COLUMNREFLIKENAME + WHITESPACE)
def t_LONGCOLUMNREFERENCE(t): return t

@TokenRule(WORKSHEETNAME + NAMEDCOLUMNREFERENCE + WHITESPACE)
def t_LONGNAMEDCOLUMNREFERENCE(t): return t

@TokenRule(WORKSHEETNAME + NAMEDROWREFERENCE + WHITESPACE)
def t_LONGNAMEDROWREFERENCE(t): return t

@TokenRule(WORKSHEETNAME + ROWREFLIKENAME + WHITESPACE)
def t_LONGROWREFERENCE(t): return t

@TokenRule(WORKSHEETNAME + t_FLDELETEDREFERENCE)
def t_LONGDELETEDREFERENCE(t): return t

@TokenRule(WORKSHEETNAME + t_FLINVALIDREFERENCE)
def t_LONGINVALIDREFERENCE(t): return t

@TokenRule(r'(?:' + FLOATNUMBER + '|[0-9]+)[Jj]' + WHITESPACE)
def t_IMAGINARY(t): return t

@TokenRule(FLOATNUMBER + WHITESPACE)
def t_FLOATNUMBER(t): return t

@TokenRule(r'0[xX][0-9a-fA-F]+[Ll]?' + WHITESPACE)
def t_HEXINTEGER(t): return t

@TokenRule(r'0[0-7]+[Ll]?' + WHITESPACE)
def t_OCTINTEGER(t): return t

@TokenRule(r'(?:0|[1-9][0-9]*)[Ll]?' + WHITESPACE)
def t_DECINTEGER(t): return t

@TokenRule(STRINGPREFIX + r"'''(?:[^\\]|\\.)*'''" + WHITESPACE)
def t_SLONGSTRING(t): return t

@TokenRule(STRINGPREFIX + r'"""(?:[^\\]|\\.)*"""' + WHITESPACE)
def t_DLONGSTRING(t): return t

@TokenRule(STRINGPREFIX + r"'(?:[^\\'\n]|\\.)*'" + WHITESPACE)
def t_SSHORTSTRING(t): return t

@TokenRule(STRINGPREFIX + r'"(?:[^\\"\n]|\\.)*"' + WHITESPACE)
def t_DSHORTSTRING(t): return t


reserved = {
    "for"    :   "FOR",
    "in"     :   "IN",
    "is"     :   "IS",
    "lambda" :   "LAMBDA",
    "not"    :   "NOT",
}

case_insensitive_reserved = {
    "and"    :   "AND",
    "if"     :   "IF",
    "or"     :   "OR",
    "iserror": "ISERROR",
    "iserr"  : "ISERR",
}

unimplemented_python_keywords = (
    "assert", "break", "class", "continue", "def", "del", "elif", "else", "except", "exec",
    "finally", "from", "global", "import", "pass", "print", "raise", "return", "try", "while"
)

DOT_RE = re.compile(t_DOT)
FLCELLREFLIKENAME_RE = re.compile(r'^%s$' % CELLREFLIKENAME)
FLCOLUMNREFLIKENAME_RE = re.compile(r'^%s$' % COLUMNREFLIKENAME)
FLROWREFLIKENAME_RE = re.compile(r'^%s$' % ROWREFLIKENAME)



@TokenRule(NAMEDROWREFERENCE + WHITESPACE)
def t_FLNAMEDROWREFERENCE(t):
    # this must come before t_TEXT, otherwise t_TEXT will eat the leading underscore
    return t


@TokenRule(r'\$?[a-zA-Z_][a-zA-Z_0-9\$]*' + WHITESPACE)
def t_TEXT(t):
    text = t.value.rstrip()
    if FLCELLREFLIKENAME_RE.match(text):
        t.type = "FLCELLREFLIKENAME"
    elif FLCOLUMNREFLIKENAME_RE.match(text):
        t.type = "FLCOLUMNREFLIKENAME"
    elif FLROWREFLIKENAME_RE.match(text):
        t.type = "FLROWREFLIKENAME"
    elif '$' in text:
        dollarError(t)
    elif text.lower() in case_insensitive_reserved:
        t.type = case_insensitive_reserved[text.lower()]
    elif text.lower() in unimplemented_python_keywords:
        keywordError(t)
    else:
        t.type = reserved.get(text, "NAME")
    return t


def dollarError(t):
    raise FormulaError("Error in formula at position %d: unexpected '%s'"
                       % (t.lexer.lexpos - len(t.value), t.value))

def keywordError(t):
    raise FormulaError("Error in formula at position %d: '%s' is a reserved word"
                       % (t.lexer.lexpos - len(t.value), t.value))

def t_error(t):
    raise FormulaError("Error in formula at position %d: unexpected '%s'" % (t.lexer.lexpos + 1, t.value))
