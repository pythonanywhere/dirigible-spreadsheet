# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

from __future__ import division

from .parser import FormulaError
from .parser.parse_node import ParseNode
from .parser.parse_node_constructors import FLCellReference, FLCellRange
from .parser.parser import parse


def rewrite_source_sheet_formulae_for_cut(worksheet, source_range, dest_col, dest_row):
    column_offset = dest_col - source_range[0]
    row_offset = dest_row - source_range[1]
    for location, cell in worksheet.iteritems():
        worksheet[location].formula = rewrite_formula(
            cell.formula, column_offset, row_offset, True, source_range)


def rewrite_formula(
    formula, column_offset, row_offset, is_cut, orig_bounds
):
    if formula is None or not formula.startswith('='):
        return formula

    def cell_in_original_bounds(column, row):
        return (
            orig_bounds[0] <= column <= orig_bounds[2] and
            orig_bounds[1] <= row <= orig_bounds[3]
        )

    def range_in_original_bounds(left, top, right, bottom):
        return (
            cell_in_original_bounds(left, top) and
            cell_in_original_bounds(right, bottom)
        )

    def offset_cell_reference(node):
        orig_column, orig_row = node.coords

        if is_cut and not cell_in_original_bounds(orig_column, orig_row):
            return node
        node.offset(column_offset, row_offset, move_absolute=is_cut)
        return node


    def offset_cell_range(node):
        corner1_col, corner1_row = node.first_cell_reference.coords
        corner2_col, corner2_row = node.second_cell_reference.coords

        if is_cut and not range_in_original_bounds(
            corner1_col, corner1_row, corner2_col, corner2_row
        ):
            return node

        node.first_cell_reference.offset(column_offset, row_offset, move_absolute=is_cut)
        node.second_cell_reference.offset(column_offset, row_offset, move_absolute=is_cut)
        return node


    def rewrite(node):
        if isinstance(node, ParseNode):
            if isinstance(node, FLCellRange):
                return offset_cell_range(node)
            if isinstance(node, FLCellReference):
                return offset_cell_reference(node)
            else:
                node.children = [
                    rewrite(child)
                    for child in node.children
                ]
        return node

    try:
        return rewrite(parse(formula)).flatten()
    except FormulaError:
        return formula

