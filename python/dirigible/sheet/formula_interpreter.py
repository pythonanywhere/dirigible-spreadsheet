# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

import re

from sheet.parser import FormulaError
from sheet.parser.tokens import t_LITTLEARROW
from sheet.parser.parse_node import ParseNode
from sheet.parser.parse_node_constructors import (
    Atom, ArgList, Name, Number, SubscriptList, Subscript, Trailer,
)

LITTLE_ARROW_RE = re.compile(t_LITTLEARROW)


def transform_arrow(child):
    if isinstance(child, basestring) and LITTLE_ARROW_RE.match(child):
        return ':'
    else:
        return child


def rewrite_cell_reference_as_tuple(cell_reference_node):
    if cell_reference_node.type == ParseNode.FL_INVALID_REFERENCE:
        raise FormulaError("#Invalid! cell reference in formula")
    if cell_reference_node.type == ParseNode.FL_DELETED_REFERENCE:
        raise FormulaError("#Deleted! cell reference in formula")

    column, row = cell_reference_node.coords
    return Atom([
                 '(',
                 Number(str(column)),
                 ',',
                 Number(str(row)),
                 ')'
                ])


def rewrite_cell_reference(cell_reference_node):
    return Atom([
        Name(["worksheet"]),
        Trailer([
            "[",
            SubscriptList([
                Subscript([ rewrite_cell_reference_as_tuple(cell_reference_node) ])
            ]),
            "]"
            ]),
        Trailer([
            ".value",
        ]),
        Name([" "])
    ])


def rewrite_cell_range(node):
    return Atom([
        Name(["CellRange"]),
        Trailer([
            "(",
            ArgList([
                Name(["worksheet"]),
                ",",
                rewrite_cell_reference_as_tuple(node.first_cell_reference),
                ",",
                rewrite_cell_reference_as_tuple(node.second_cell_reference),
            ]),
            ")",
        ]),
        Name([" "])
    ])


CELL_REFERENCES = (
    ParseNode.FL_CELL_REFERENCE, ParseNode.FL_INVALID_REFERENCE,
    ParseNode.FL_DELETED_REFERENCE
)
CONTAIN_COLONS = (
    ParseNode.LAMBDEF, ParseNode.DICT_MAKER, ParseNode.SUBSCRIPT,
    ParseNode.SLICE_OP
)

def rewrite(parse_node):
    if isinstance(parse_node, ParseNode):
        if parse_node.type == ParseNode.FL_CELL_RANGE:
            return rewrite_cell_range(parse_node)

        elif parse_node.type in CELL_REFERENCES:
            return rewrite_cell_reference(parse_node)

        elif parse_node.type in CONTAIN_COLONS:
            parse_node.children = map(
                rewrite,
                [transform_arrow(child) for child in parse_node.children]
            )

        else:
            parse_node.children = map(rewrite, parse_node.children)

    return parse_node


def get_python_formula_from_parse_tree(parse_node):
    return rewrite(parse_node).flatten()[1:]


def get_dependencies_from_parse_tree(parse_node):
    if not isinstance(parse_node, ParseNode):
        return []

    if parse_node.type == ParseNode.FL_CELL_REFERENCE:
        return [parse_node.coords]

    elif parse_node.type == ParseNode.FL_CELL_RANGE:
        if parse_node.first_cell_reference.type in (ParseNode.FL_INVALID_REFERENCE, ParseNode.FL_DELETED_REFERENCE):
            return []
        if parse_node.second_cell_reference.type in (ParseNode.FL_INVALID_REFERENCE, ParseNode.FL_DELETED_REFERENCE):
            return []
        topleft = parse_node.first_cell_reference.coords
        bottomright = parse_node.second_cell_reference.coords
        left, right = sorted([topleft[0], bottomright[0]])
        top, bottom = sorted([topleft[1], bottomright[1]])
        return [
            (c,r)
            for c in xrange(left, right + 1)
            for r in xrange(top, bottom + 1)
        ]

    elif parse_node.children:
        return sum((get_dependencies_from_parse_tree(child) for child in parse_node.children), [])

    else:
        return []

