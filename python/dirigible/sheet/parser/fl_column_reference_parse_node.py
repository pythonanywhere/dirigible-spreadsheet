# Copyright (c) 2005-2009 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

from sheet.parser.parse_node import ParseNode
from sheet.parser.fl_reference_parse_node import FLReferenceParseNode
from sheet.utils.cell_name_utils import column_name_to_index, column_index_to_name


class FLColumnReferenceParseNode(FLReferenceParseNode):

    def __init__(self, children):
        FLReferenceParseNode.__init__(self, ParseNode.FL_COLUMN_REFERENCE, children)


    @property
    def isAbsolute(self):
        return self.localReference.lstrip().startswith("$")


    def __getPlainColumnName(self):
        return self.localReference.strip().replace('$', '').replace('_', '')
    def __setPlainColumnName(self, newName):
        self.children[-1] = self.localReference.replace(self.plainColumnName, newName)
    plainColumnName = property(__getPlainColumnName, __setPlainColumnName)


    @property
    def colIndex(self):
        return column_name_to_index(self.plainColumnName)

    @property
    def coords(self):
        return self.colIndex, 0


    def offset(self, count, _, moveAbsolute=False):
        if not moveAbsolute and self.isAbsolute:
            return
        newName = column_index_to_name(self.colIndex + count)
        if newName:
            self.plainColumnName = newName
        else:
            self.localReference = '#Invalid!' + self.whitespace

    def __getLocalReference(self):
        return self.children[-1]
    def __setLocalReference(self, newCol):
        self.children[-1] = newCol

    localReference = property(__getLocalReference, __setLocalReference)


    def canonicalise(self, wsNames):
        self.localReference = self.localReference.upper()
        FLReferenceParseNode.canonicalise(self, wsNames)

ParseNode.register_node_type(ParseNode.FL_COLUMN_REFERENCE, FLColumnReferenceParseNode)
