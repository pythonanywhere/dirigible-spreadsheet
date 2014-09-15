# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from sheet.worksheet import Worksheet
from sheet.rewrite_formula_offset_cell_references import (
    rewrite_formula, rewrite_source_sheet_formulae_for_cut,
)

class TestRewriteFormulaOffsetCellReferences(unittest.TestCase):

    def test_dont_rewrite_constants(self):
        result = rewrite_formula(
            "B3", 3, 5, False, (1, 2, 3, 4)
        )
        self.assertEquals(result, 'B3')


    def test_safely_handle_none(self):
        self.assertIsNone( rewrite_formula(None, 3, 5, False, (1, 2, 3, 4)) )


    def test_safely_handle_nonsense(self):
        unparseable_nonsense = '=!:booA1:A2'
        self.assertEquals(
                rewrite_formula(unparseable_nonsense, 3, 5, False, (1, 2, 3, 4)),
                unparseable_nonsense
        )


    def test_cut_cell_reference_to_cut_cell_is_rewritten(self):
        result = rewrite_formula(
            "=A2", 2, 1, True, (1, 1, 1, 2)
        )
        self.assertEquals(result, '=C3')


    def test_cut_cell_reference_to_uncut_cell_is_not_rewritten(self):
        result = rewrite_formula(
            "=B3", 2, 1, True, (1, 1, 1, 1)
        )
        self.assertEquals(result, '=B3')


    def test_absolute_cut_cell_reference_to_uncut_cell_is_not_rewritten(self):
        result = rewrite_formula(
            "=$B$3", 2, 1, True, (1, 1, 1, 1)
        )
        self.assertEquals(result, '=$B$3')


    def test_absolute_cut_cell_reference_to_cut_cell_is_rewritten(self):
        result = rewrite_formula(
            "=$A$2", 2, 1, True, (1, 1, 1, 2)
        )
        self.assertEquals(result, '=$C$3')


    def test_copied_cell_reference_to_copied_cell_is_rewritten(self):
        result = rewrite_formula(
            "=A2", 2, 1, False, (1, 1, 1, 2)
        )
        self.assertEquals(result, '=C3')


    def test_copied_cell_reference_to_uncopied_cell_is_rewritten(self):
        result = rewrite_formula(
            "=B3", 2, 1, False, (1, 1, 1, 1)
        )
        self.assertEquals(result, '=D4')


    def test_absolute_copied_cell_reference_to_copied_cell_is_not_rewritten(self):
        result = rewrite_formula(
            "=$A$2", 2, 1, False, (1, 1, 1, 2)
        )
        self.assertEquals(result, '=$A$2')


    def test_absolute_copied_cell_reference_to_uncopied_cell_is_not_rewritten(self):
        result = rewrite_formula(
            "=$B$3", 2, 1, False, (1, 1, 1, 1)
        )
        self.assertEquals(result, '=$B$3')


    def test_copied_cell_reference_that_moves_off_grid_marked_invalid(self):
        result = rewrite_formula(
            "=A1", 1, -1, False, (1, 2, 1, 2)
        )
        self.assertEquals(result, '=#Invalid!')


    def test_cut_cellrange_reference_to_completely_cut_cellrange_is_rewritten(self):
        result = rewrite_formula(
            "=A2:A3", 2, 1, True, (1, 1, 1, 3)
        )
        self.assertEquals(result, '=C3:C4')


    def test_cut_cellrange_reference_to_partially_cut_cellrange_is_not_rewritten(self):
        result = rewrite_formula(
            "=A2:A3", 2, 1, True, (1, 1, 1, 2)
        )
        self.assertEquals(result, '=A2:A3')


    def test_cut_absolute_cellrange_reference_to_completely_cut_cellrange_is_rewritten(self):
        result = rewrite_formula(
            "=$A$2:$A$3", 2, 1, True, (1, 1, 1, 3)
        )
        self.assertEquals(result, '=$C$3:$C$4')


    def test_cut_absolute_cellrange_reference_to_partially_cut_cellrange_is_not_rewritten(self):
        result = rewrite_formula(
            "=$A$2:$A$3", 2, 1, True, (1, 1, 1, 2)
        )
        self.assertEquals(result, '=$A$2:$A$3')


    def test_cut_cellrange_reference_to_partially_cut_cellrange_is_not_rewritten_even_if_its_not_obviously_overlapping(self):
        cut_region_left = 2
        cut_region_right = 3
        cut_region_top = 1
        cut_region_bottom = 2

        cell_range_topleft = "A2"
        cell_range_bottomright = "B3"

        result = rewrite_formula(
            "=%s:%s" % (cell_range_topleft, cell_range_bottomright),
            2, 1,
            True,
            (cut_region_left, cut_region_top, cut_region_right, cut_region_bottom)
        )
        self.assertEquals(result, '=A2:B3')


    def test_cut_absolute_cellrange_reference_to_partially_cut_cellrange_is_not_rewritten_even_if_its_not_obviously_overlapping(self):
        cut_region_left = 2
        cut_region_right = 3
        cut_region_top = 1
        cut_region_bottom = 2

        cell_range_topleft = "$A$2"
        cell_range_bottomright = "$B$3"

        result = rewrite_formula(
            "=%s:%s" % (cell_range_topleft, cell_range_bottomright),
            2, 1,
            True,
            (cut_region_left, cut_region_top, cut_region_right, cut_region_bottom)
        )
        self.assertEquals(result, '=$A$2:$B$3')


    def test_cut_cellrange_reference_to_uncut_cellrange_is_not_rewritten(self):
        result = rewrite_formula(
            "=A2:A3", 2, 1, True, (1, 1, 1, 1)
        )
        self.assertEquals(result, '=A2:A3')


    def test_cut_absolute_cellrange_reference_to_uncut_cellrange_is_not_rewritten(self):
        result = rewrite_formula(
            "=$A$2:$A$3", 2, 1, True, (1, 1, 1, 1)
        )
        self.assertEquals(result, '=$A$2:$A$3')


    def test_copied_cellrange_reference_to_completely_copied_cellrange_is_rewritten(self):
        result = rewrite_formula(
            "=A2:A3", 2, 1, False, (1, 1, 1, 3)
        )
        self.assertEquals(result, '=C3:C4')


    def test_copied_absolute_cellrange_reference_to_completely_copied_cellrange_is_not_rewritten(self):
        result = rewrite_formula(
            "=$A$2:$A$3", 2, 1, False, (1, 1, 1, 3)
        )
        self.assertEquals(result, '=$A$2:$A$3')


    def test_copied_cellrange_reference_to_partially_copied_cellrange_is_rewritten(self):
        result = rewrite_formula(
            "=A2:A3", 2, 1, False, (1, 1, 1, 2)
        )
        self.assertEquals(result, '=C3:C4')


    def test_copied_absolute_cellrange_reference_to_partially_copied_cellrange_is_not_rewritten(self):
        result = rewrite_formula(
            "=$A$2:$A$3", 2, 1, False, (1, 1, 1, 2)
        )
        self.assertEquals(result, '=$A$2:$A$3')


    def test_copied_cellrange_reference_to_uncopied_cellrange_is_rewritten(self):
        result = rewrite_formula(
            "=A2:A3", 2, 1, False, (1, 1, 1, 1)
        )
        self.assertEquals(result, '=C3:C4')


    def test_copied_absolute_cellrange_reference_to_uncopied_cellrange_is_not_rewritten(self):
        result = rewrite_formula(
            "=$A$2:$A$3", 2, 1, False, (1, 1, 1, 1)
        )
        self.assertEquals(result, '=$A$2:$A$3')


    def test_copied_cellrange_reference_that_moves_off_grid_marked_invalid(self):
        result = rewrite_formula(
            "=A1:A2", 1, -1, False, (1, 3, 1, 3)
        )
        self.assertEquals(result, '=#Invalid!:B1')


    def test_source_sheet_cell_references_to_cut_range_are_rewritten(self):
        worksheet = Worksheet()
        worksheet.A1.formula = '=B1'
        worksheet.A2.formula = '=B2'
        worksheet.A3.formula = '=B3'
        worksheet.A4.formula = 'B1'
        worksheet.A5.formula = '=$B$1'

        rewrite_source_sheet_formulae_for_cut(worksheet, (2, 1, 2, 2), 3, 4)

        self.assertEquals(worksheet.A1.formula, '=C4')
        self.assertEquals(worksheet.A2.formula, '=C5')
        self.assertEquals(worksheet.A3.formula, '=B3')
        self.assertEquals(worksheet.A4.formula, 'B1')
        self.assertEquals(worksheet.A5.formula, '=$C$4')


    def test_source_sheet_cell_ranges_inside_cut_range_are_rewritten(self):
        worksheet = Worksheet()
        worksheet.A1.formula = '=B1:B2'
        worksheet.A2.formula = '=sum(B1:B2)'
        worksheet.A3.formula = '=B3:B4'
        worksheet.A4.formula = 'B1:B2'
        worksheet.A5.formula = '=$B$1:$B$2'

        rewrite_source_sheet_formulae_for_cut(worksheet, (2, 1, 2, 2), 3, 4)

        self.assertEquals(worksheet.A1.formula, '=C4:C5')
        self.assertEquals(worksheet.A2.formula, '=sum(C4:C5)')
        self.assertEquals(worksheet.A3.formula, '=B3:B4')
        self.assertEquals(worksheet.A4.formula, 'B1:B2')
        self.assertEquals(worksheet.A5.formula, '=$C$4:$C$5')

