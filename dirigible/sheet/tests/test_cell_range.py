# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

from __future__ import with_statement

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from mock import Mock

from sheet.cell import Cell, undefined
from sheet.worksheet import Worksheet
from sheet.cell_range import CellRange
from dirigible.test_utils import ResolverTestCase



class TestCellRanges(ResolverTestCase):
    def setUp(self):
        self.ws = ws = Worksheet()
        ws[1, 1].value = 'foist'
        ws[10, 100].value = 'second'
        ws[2, 3].value = 'middle1'
        ws[3, 3].value = 'middle2'
        ws[2, 4].value = 'raster test'
        ws[100, 100].value = 'way down here'

    def test_constructor_with_only_worksheet_fails(self):
        self.assertRaises(TypeError, lambda : CellRange(self.ws))

    def test_constructor_with_start_and_end(self):
        cell_range = CellRange(self.ws, (2, 3), (4, 5))
        self.assertEquals(cell_range.left, 2)
        self.assertEquals(cell_range.top, 3)
        self.assertEquals(cell_range.right, 4)
        self.assertEquals(cell_range.bottom, 5)
        self.assertEquals(cell_range.worksheet, self.ws)

    def test_constructor_inverted(self):
        cell_range = CellRange(self.ws, (4, 5), (2, 3))
        self.assertEquals(cell_range.left, 2)
        self.assertEquals(cell_range.top, 3)
        self.assertEquals(cell_range.right, 4)
        self.assertEquals(cell_range.bottom, 5)

        cell_range = CellRange(self.ws, (4, 3), (2, 5))
        self.assertEquals(cell_range.left, 2)
        self.assertEquals(cell_range.top, 3)
        self.assertEquals(cell_range.right, 4)
        self.assertEquals(cell_range.bottom, 5)

    def test_equality(self):
        cr1 = CellRange(self.ws, (2, 3), (4, 5))
        cr2 = CellRange(self.ws, (2, 3), (4, 5))

        self.assertTrue(cr1 == cr2)
        self.assertFalse(cr1 != cr2)

        cr_diff_sheet = CellRange(Worksheet(), (2, 3), (4, 5))
        self.assertFalse(cr1 == cr_diff_sheet)
        self.assertTrue(cr1 != cr_diff_sheet)

        cr_diff_start = CellRange(self.ws, (2, 33), (4, 5))
        self.assertFalse(cr1 == cr_diff_start)
        self.assertTrue(cr1 != cr_diff_start)

        cr_diff_end = CellRange(self.ws, (2, 3), (4, 55))
        self.assertFalse(cr1 == cr_diff_end)
        self.assertTrue(cr1 != cr_diff_end)

        self.assertFalse(cr1 == 15)
        self.assertTrue(cr1 != 15)

    def test_repr(self):
        self.ws.name = 'AWESOME-SHEET'
        cr1 = CellRange(self.ws, (2, 3), (4, 5))
        self.assertEquals(str(cr1), '<CellRange B3 to D5 in <Worksheet AWESOME-SHEET>>')

    def test_edges(self):
        cell_range = CellRange(self.ws, (2, 4), (3, 5))
        self.assertEquals(cell_range.left, 2)
        self.assertEquals(cell_range.right, 3)
        self.assertEquals(cell_range.top, 4)
        self.assertEquals(cell_range.bottom, 5)

    def test_len(self):
        cell_range = CellRange(self.ws, (2, 3), (3, 5))
        self.assertEquals(len(cell_range), 6)


    def test_iterators_with_start_and_end(self):
        cell_range = CellRange(self.ws, (2, 3), (3, 5))
        expected_locs = [(2, 3), (3, 3), (2, 4), (3, 4), (2, 5), (3, 5)]
        self.assertEquals(len(list(cell_range.cells)), 6)
        self.assertEquals(list(cell_range.cells), [self.ws[loc] for loc in expected_locs])
        self.assertEquals(list(cell_range), [self.ws[loc].value for loc in expected_locs])


    def test_iterators_with_start_and_end_inverted(self):
        cell_range = CellRange(self.ws, (3, 5), (2, 3))
        expected_cells = [self.ws[loc] for loc in [(2, 3), (3, 3), (2, 4), (3, 4),(2, 5),(3, 5),]]
        self.assertEquals(list(cell_range), [c.value for c in expected_cells])
        self.assertEquals(list(cell_range.cells), expected_cells)


    def test_indexing_by_tuple(self):
        cell_range = CellRange(self.ws, (2, 3), (10, 10))

        existing_cell = self.ws[3, 3]
        self.assertEquals(cell_range[2, 1], existing_cell)

        blank_cell_from_range = cell_range[4, 4]
        self.assertEquals(blank_cell_from_range.value, undefined)

        blank_cell_from_range.value = "new cell's value"
        self.assertEquals(self.ws[5, 6].value, "new cell's value")

        overly_large_offset = (100, 100)
        self.assertRaises(IndexError, lambda : cell_range[overly_large_offset])

    def test_indexing_edge_cases(self):
        cell_range = CellRange(self.ws, (2, 2), (10, 9))

        self.assertEquals(cell_range[1, 1], self.ws[2, 2])
        self.assertEquals(cell_range[9, 8], self.ws[10, 9])

        try:
            cell_range[10, 8]
            self.fail('should have raised error')
        except IndexError, e:
            self.assertEquals(str(e), 'Cell range only has 9 columns')

        try:
            cell_range[9, 9]
            self.fail('should have raised error')
        except IndexError, e:
            self.assertEquals(str(e), 'Cell range only has 8 rows')

        try:
            cell_range[0, 0]
            self.fail('should have raised error')
        except IndexError, e:
            self.assertEquals(str(e), 'Cell ranges are 1-indexed')

    def test_indexing_backwards(self):
        cell_range = CellRange(self.ws, (2, 2), (10, 9))

        self.assertEquals(cell_range[-1, -1], self.ws[10, 9])
        self.assertEquals(cell_range[-4, 2], self.ws[7, 3])

        try:
            cell_range[-10, -9]
            self.fail('should have raised error')
        except IndexError, e:
            self.assertEquals(str(e), 'Cell range only has 9 columns')

    def test_setitem_on_nonexistent_cell(self):
        cell_range = CellRange(self.ws, (2, 2), (10, 9))
        cell_range[2, 2].value = 'new val'
        self.assertEquals(self.ws[3, 3].value, 'new val')

        new_cell = Cell()
        cell_range[2, 3] = new_cell
        self.assertEquals(self.ws[3, 4], new_cell)


    def test_iterator_with_locations(self):
        cell_range = CellRange(self.ws, (1, 2), (3, 4))
        self.assertEquals(len(list(cell_range.cells)),
                          len(list(cell_range.locations_and_cells)))
        for (loc, cell), actual_cell in zip(
                cell_range.locations_and_cells,
                cell_range.cells):
            self.assertTrue(cell is self.ws[loc])
            self.assertTrue(cell is actual_cell)


    def test_clear_should_call_clear_on_member_cells(self):
        cell_range = CellRange(self.ws, (1, 2), (2, 3))
        for cell in cell_range.cells:
            cell.clear = Mock()
        cell_range.clear()
        for cell in cell_range.cells:
            self.assertCalledOnce(cell.clear)



