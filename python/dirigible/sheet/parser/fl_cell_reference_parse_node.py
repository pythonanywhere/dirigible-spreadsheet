# Copyright (c) 2005-2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

from sheet.parser.parse_node import ParseNode
from sheet.parser.fl_reference_parse_node import FLReferenceParseNode
from sheet.utils.cell_name_utils import cell_name_to_coordinates, coordinates_to_cell_name

class FLCellReferenceParseNode(FLReferenceParseNode):

    def __init__(self, children):
        FLReferenceParseNode.__init__(self, ParseNode.FL_CELL_REFERENCE, children)


    @property
    def colAbsolute(self):
        return self.localReference.startswith("$")


    @property
    def rowAbsolute(self):
        return '$' in self.localReference[1:]


    @property
    def plainCellName(self):
        return self.localReference.replace('$', '')


    def __getLocalReference(self):
        return self.children[-1]

    def __setLocalReference(self, cellRef):
        self.children[-1] = cellRef

    localReference = property(__getLocalReference, __setLocalReference)


    @property
    def coords(self):
        return cell_name_to_coordinates(self.plainCellName)


    def offset(self, dx, dy, move_absolute=False):
        (col, row) = cell_name_to_coordinates(self.plainCellName)

        if move_absolute or not self.colAbsolute:
            col += dx
        if move_absolute or not self.rowAbsolute:
            row += dy

        newName = coordinates_to_cell_name(col, row, colAbsolute=self.colAbsolute, rowAbsolute=self.rowAbsolute)
        if newName is None:
            newName = "#Invalid!"

        self.localReference = newName + self.whitespace


    def canonicalise(self, wsNames):
        self.localReference = self.localReference.upper()
        FLReferenceParseNode.canonicalise(self, wsNames)


ParseNode.register_node_type(ParseNode.FL_CELL_REFERENCE, FLCellReferenceParseNode)
