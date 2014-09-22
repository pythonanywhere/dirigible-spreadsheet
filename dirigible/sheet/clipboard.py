# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#


import json
import StringIO

from django.db import models
from django.contrib.auth.models import User

from .cell import Cell
from .rewrite_formula_offset_cell_references import (
    rewrite_formula, rewrite_source_sheet_formulae_for_cut
)
from .sheet import Sheet
from .worksheet import (
    CellRange, dump_cell_to_json_stream,
)


class Clipboard(models.Model):
    owner = models.ForeignKey(User)
    contents_json = models.TextField(default='{}')
    is_cut = models.BooleanField(default=False)
    source_left = models.IntegerField(null=True)
    source_top = models.IntegerField(null=True)
    source_right = models.IntegerField(null=True)
    source_bottom = models.IntegerField(null=True)
    source_sheet = models.ForeignKey(Sheet, null=True)

    @property
    def source_range(self):
        return (
            self.source_left, self.source_top,
            self.source_right, self.source_bottom
        )

    @property
    def width(self):
        return self.source_right - self.source_left + 1

    @property
    def height(self):
        return self.source_bottom - self.source_top + 1


    def copy(self, sheet, start, end):
        self.is_cut = False
        self.worksheet = sheet.unjsonify_worksheet()
        self.cellrange = CellRange(self.worksheet, start, end)
        cols_offset = self.cellrange.left
        rows_offset = self.cellrange.top

        stream = StringIO.StringIO()
        stream.write("{ ")
        first = True
        for (col, row), cell in self.cellrange.locations_and_cells:
            if not first:
                stream.write(',')
            first = False
            if not cell.formula:
                cell.formula = cell.formatted_value
            dump_cell_to_json_stream(stream, col-cols_offset, row-rows_offset, cell)
        stream.write(" }")

        self.source_left = self.cellrange.left
        self.source_right = self.cellrange.right
        self.source_top = self.cellrange.top
        self.source_bottom = self.cellrange.bottom

        self.contents_json = stream.getvalue()
        stream.close()


    def cut(self, sheet, start, end):
        self.copy(sheet, start, end)

        for location in self.cellrange.locations:
            if location in self.worksheet:
                del self.worksheet[location]
        sheet.jsonify_worksheet(self.worksheet)

        self.is_cut = True
        self.source_sheet = sheet


    def _get_offset(self, col, row, start_col, start_row):
        tile_offset_col = col // self.width * self.width
        tile_offset_row = row // self.height * self.height
        column_offset = start_col - self.source_left + tile_offset_col
        row_offset = start_row - self.source_top + tile_offset_row
        return column_offset, row_offset


    def to_cells(self, start, end):
        start_col, start_row = start
        end_col, end_row = end

        strings_dict = json.loads(self.contents_json)

        for col in xrange(0, end_col - start_col + 1):
            for row in xrange(0, end_row - start_row + 1):

                clip_loc = col % self.width, row % self.height

                clip_cell = strings_dict['%s,%s' % clip_loc]
                dest_cell = Cell()
                if clip_cell['formula']:
                    column_offset, row_offset = self._get_offset(col, row, start_col, start_row)
                    dest_cell.formula = rewrite_formula(
                        clip_cell['formula'], column_offset, row_offset,
                        self.is_cut, self.source_range
                    )

                dest_cell.formatted_value = clip_cell['formatted_value']
                dest_loc = col + start_col, row + start_row
                yield (dest_loc, dest_cell)


    def paste_to(self, to_sheet, start, end):
        start_col, start_row = start
        if end == start:
            end =  start_col + self.width - 1, start_row + self.height - 1

        to_worksheet = to_sheet.unjsonify_worksheet()
        if self.is_cut and to_sheet == self.source_sheet:
            rewrite_source_sheet_formulae_for_cut(
                to_worksheet,
                self.source_range,
                start_col, start_row
            )

        cells = self.to_cells(start, end)
        for loc, cell in cells:
            to_worksheet[loc] = cell

        to_sheet.jsonify_worksheet(to_worksheet)

        if self.is_cut:
            self.source_left, self.source_top = start
            self.source_right, self.source_bottom = end
            self.is_cut = False
            self.source_sheet = None

