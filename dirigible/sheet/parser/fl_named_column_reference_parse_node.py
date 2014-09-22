# Copyright (c) 2005-2009 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

from sheet.parser.parse_node import ParseNode
from sheet.parser.fl_reference_parse_node import FLReferenceParseNode


class FLNamedColumnReferenceParseNode(FLReferenceParseNode):

    def __init__(self, children):
        FLReferenceParseNode.__init__(self, ParseNode.FL_NAMED_COLUMN_REFERENCE, children)


    @property
    def header(self):
        return self.children[-1].rstrip().replace("##", "#")[1:-2]


ParseNode.register_node_type(ParseNode.FL_NAMED_COLUMN_REFERENCE, FLNamedColumnReferenceParseNode)
