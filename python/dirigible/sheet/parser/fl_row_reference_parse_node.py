# Copyright (c) 2005-2009 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

from dirigible.sheet.parser.parse_node import ParseNode
from dirigible.sheet.parser.fl_reference_parse_node import FLReferenceParseNode

class FLRowReferenceParseNode(FLReferenceParseNode):

    def __init__(self, children):
        ParseNode.__init__(self, ParseNode.FL_ROW_REFERENCE, children)

    @property
    def isAbsolute(self):
        return '$' in self.children[-1]

    def __getPlainRowName(self):
        return self.children[-1][1:].strip().replace('$', '')
    def __setPlainRowName(self, newName):
        self.children[-1] = self.localReference.replace(self.plainRowName, newName)
    plainRowName = property(__getPlainRowName, __setPlainRowName)

    @property
    def rowIndex(self):
        return int(self.plainRowName)


    @property
    def coords(self):
        return 0, self.rowIndex


    def offset(self, _, count, moveAbsolute=False):
        if not moveAbsolute and self.isAbsolute:
            return
        newIndex = self.rowIndex + count
        if newIndex > 0:
            self.plainRowName = str(newIndex)
        else:
            self.localReference = '#Invalid!' + self.whitespace


    def __getLocalReference(self):
        return self.children[-1]
    def __setLocalReference(self, newRow):
        self.children[-1] = newRow
    localReference = property(__getLocalReference, __setLocalReference)


ParseNode.register_node_type(ParseNode.FL_ROW_REFERENCE, FLRowReferenceParseNode)

