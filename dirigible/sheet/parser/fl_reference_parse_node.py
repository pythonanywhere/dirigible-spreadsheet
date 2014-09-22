# Copyright (c) 2005-2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#
import re

from sheet.parser.parse_node import ParseNode
from sheet.utils.string_utils import correct_case, get_rstripped_part


_worksheetNameRegex = re.compile(r"^[A-Za-z]\w*$")
def quote_fl_worksheet_name(name):
    if re.match(_worksheetNameRegex, name) is not None:
        return name
    return "'%s'" % name.replace("'", "''")


def unquote_fl_worksheet_name(name):
    name = name.replace("''", "'")
    if name.startswith("'"):
        return name[1:-1]
    return name


class FLReferenceParseNode(ParseNode):

    def __init__(self, nodeType, children):
        assert len(children) in (1, 3)
        ParseNode.__init__(self, nodeType, children)


    @property
    def whitespace(self):
        return get_rstripped_part(self.children[-1])


    def __getWorksheet(self):
        if len(self.children) == 3:
            return unquote_fl_worksheet_name(self.children[0].rstrip())
        return None

    def __setWorksheet(self, ws):
        if ws is None:
            self.children = [self.children[-1]]
            return

        ws = quote_fl_worksheet_name(ws)
        if self.worksheetReference:
            self.children[0] = ws + get_rstripped_part(self.children[0])
        else:
            self.children = [ws, '!', self.children[-1]]

    worksheetReference = property(__getWorksheet, __setWorksheet)


    def canonicalise(self, wsNames):
        if self.worksheetReference:
            self.worksheetReference = correct_case(self.worksheetReference, wsNames)
