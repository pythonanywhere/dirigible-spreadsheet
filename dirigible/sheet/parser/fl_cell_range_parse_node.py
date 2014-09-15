# Copyright (c) 2005-2009 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

from sheet.parser.parse_node import ParseNode

class FLCellRangeParseNode(ParseNode):

    def __init__(self, children):
        assert len(children) == 3
        ParseNode.__init__(self, ParseNode.FL_CELL_RANGE, children)

    def __get_first_cell_reference(self):
        return self.children[0]
    def __set_first_cell_reference(self, cellRef):
        self.children[0] = cellRef

    first_cell_reference = property(__get_first_cell_reference, __set_first_cell_reference)

    def __get_second_cell_reference(self):
        return self.children[2]

    def __set_second_cell_reference(self, cellRef):
        self.children[2] = cellRef

    second_cell_reference = property(__get_second_cell_reference, __set_second_cell_reference)

    @property
    def colon(self):
        return self.children[1]

ParseNode.register_node_type(ParseNode.FL_CELL_RANGE, FLCellRangeParseNode)
