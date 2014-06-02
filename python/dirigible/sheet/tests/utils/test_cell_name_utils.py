# Copyright (c) 2005-2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import sys

from dirigible.sheet.utils.cell_name_utils import (
    cell_name_to_coordinates, cell_range_as_string_to_coordinates,
    cell_ref_as_string_to_coordinates, _col_row_names_to_coordinates,
    column_index_to_name, column_name_to_index, coordinates_to_cell_name,
    MAX_COL)


class CellNameUtilsTest(unittest.TestCase):

    def testColumnNameTo(self):
        "test column_name_to_index"
        self.assertEquals(column_name_to_index("A"), 1, "incorrect conversion"  )
        self.assertEquals(column_name_to_index("S"), 19, "incorrect conversion"  )
        self.assertEquals(column_name_to_index("Z"), 26, "incorrect conversion"  )
        self.assertEquals(column_name_to_index("AA"), 27, "incorrect conversion"  )
        self.assertEquals(column_name_to_index("aa"), 27, "incorrect conversion"  )
        self.assertEquals(column_name_to_index("AZ"), 52, "incorrect conversion"  )
        self.assertEquals(column_name_to_index("aZ"), 52, "incorrect conversion"  )
        self.assertEquals(column_name_to_index("BA"), 53, "incorrect conversion"  )
        self.assertEquals(column_name_to_index("Ba"), 53, "incorrect conversion"  )
        self.assertEquals(column_name_to_index("mjJ"), 9058, "incorrect conversion"  )
        self.assertEquals(column_name_to_index("MJJ"), 9058, "incorrect conversion"  )
        self.assertEquals(column_name_to_index("ZZZ"), 18278, "incorrect conversion")

        self.assertIsNone(column_name_to_index("AAAA"), "invalid column not None")
        self.assertIsNone(column_name_to_index("HELLO3"), "invalid column not None")
        self.assertIsNone(column_name_to_index("SHEET"), "invalid column not None")
        self.assertIsNone(column_name_to_index("@"), "invalid column not None")
        self.assertIsNone(column_name_to_index("33"), "invalid column not None")
        self.assertIsNone(column_name_to_index("FXSHRXX"), "invalid column not None (column too large for 32 bit int)")


    def testColumnIndexTo(self):
        "test column_index_to_name"
        self.assertEquals(column_index_to_name(1), "A", "incorrect conversion")
        self.assertEquals(column_index_to_name(19), "S", "incorrect conversion")
        self.assertEquals(column_index_to_name(26), "Z", "incorrect conversion")
        self.assertEquals(column_index_to_name(27), "AA", "incorrect conversion")
        self.assertEquals(column_index_to_name(52), "AZ", "incorrect conversion")
        self.assertEquals(column_index_to_name(9058), "MJJ", "incorrect conversion")
        self.assertEquals(column_index_to_name(18278), "ZZZ", "incorrect conversion")
        self.assertIsNone(column_index_to_name(18279), "invalid column not None")
        self.assertIsNone(column_index_to_name(8826682), "invalid column not None")
        self.assertIsNone(column_index_to_name(sys.maxint+1), "column too large for 32 bit int not None")


    def testColRowNames(self):
        "test col row names to coordinates"
        self.assertEquals(_col_row_names_to_coordinates("A", "1"), (1, 1), "To coordinates test 1 failed")
        self.assertEquals(_col_row_names_to_coordinates("B", "1"), (2, 1), "To coordinates test 2 failed")
        self.assertEquals(_col_row_names_to_coordinates("C", "5"), (3, 5), "To coordinates test 3 failed")
        self.assertEquals(_col_row_names_to_coordinates("aC", "100"), (29, 100), "To coordinates test 4 failed")
        self.assertIsNone(_col_row_names_to_coordinates("A", None), "Invalid coordinates")
        self.assertIsNone(_col_row_names_to_coordinates("FXSHRXX", None), "Invalid coordinates")
        self.assertIsNone(_col_row_names_to_coordinates(None, None), "Invalid coordinates")


    def testCoordinatesToCell(self):
        "test coordinates_to_cell_name"
        self.assertEquals(coordinates_to_cell_name(1, 1), "A1", "To name test 1 failed")
        self.assertEquals(coordinates_to_cell_name(2, 1), "B1", "To name test 2 failed")
        self.assertEquals(coordinates_to_cell_name(3, 5), "C5", "To name test 3 failed")
        self.assertEquals(coordinates_to_cell_name(29, 100), "AC100", "To name test 4 failed")
        self.assertEquals(coordinates_to_cell_name(13057, 1), "SHE1", "To name test 4 failed")


    def testCoordinatesToCell2(self):
        "test coordinates_to_cell_name with absolution"
        self.assertEquals(coordinates_to_cell_name(1, 1, colAbsolute=True), "$A1", "To name test 1 failed")
        self.assertEquals(coordinates_to_cell_name(2, 1, rowAbsolute=True), "B$1", "To name test 2 failed")
        self.assertEquals(coordinates_to_cell_name(3, 5, colAbsolute=True, rowAbsolute=True), "$C$5",
                          "To name test 3 failed")


    def test_coordinates_to_cell_name_bad(self):
        self.assertIsNone(coordinates_to_cell_name(0, 1), "bad")
        self.assertIsNone(coordinates_to_cell_name(1, 0), "bad")
        self.assertIsNone(coordinates_to_cell_name(0, 0), "bad")
        self.assertIsNone(coordinates_to_cell_name(1, -1), "bad")
        self.assertIsNone(coordinates_to_cell_name(-1, 1), "bad")
        self.assertIsNone(coordinates_to_cell_name(MAX_COL + 1, 1), "bad")


    def testCellNameTo(self):
        "test cell_name_to_coordinates"
        self.assertEquals(cell_name_to_coordinates("A1"), (1, 1), "To coordinates test 1 failed")
        self.assertEquals(cell_name_to_coordinates("b1"), (2, 1), "To coordinates test 2 failed")
        self.assertEquals(cell_name_to_coordinates("C5"), (3, 5), "To coordinates test 3 failed")
        self.assertEquals(cell_name_to_coordinates("ac100"), (29, 100), "To coordinates test 4 failed")
        self.assertEquals(cell_name_to_coordinates("A1   "), (1, 1), "To coordinates test 5 failed")
        self.assertEquals(cell_name_to_coordinates("She1"), (13057, 1), "To coordinates test 5 failed")

        self.assertIsNone(cell_name_to_coordinates("56G"), "To coordinates test 5 failed")
        self.assertIsNone(cell_name_to_coordinates("YTGDCJK"), "To coordinates test 6 failed")
        self.assertIsNone(cell_name_to_coordinates("54688"), "To coordinates test 7 failed")
        self.assertIsNone(cell_name_to_coordinates(""), "To coordinates test 8 failed")
        self.assertIsNone(cell_name_to_coordinates("W0mbat"), "To coordinates test 9 failed")
        self.assertIsNone(cell_name_to_coordinates("    "), "To coordinates test 10 failed")
        self.assertIsNone(cell_name_to_coordinates(";-)"), "To coordinates test 11 failed")
        self.assertIsNone(cell_name_to_coordinates(None), "To coordinates test 12 failed")
        self.assertIsNone(cell_name_to_coordinates("FXSHRXX1"), "Invalid column name")
        self.assertIsNone(cell_name_to_coordinates("A9223372036854775808"), "Invalid row number")


    def testAbsoluteCellName(self):
        "test absolute cell_name_to_coordinates"
        self.assertEquals(cell_name_to_coordinates("$A1"), (1, 1), "To coordinates test 1 failed")
        self.assertEquals(cell_name_to_coordinates("A$1"), (1, 1), "To coordinates test 1 failed")
        self.assertEquals(cell_name_to_coordinates("$A$1"), (1, 1), "To coordinates test 1 failed")

        self.assertEquals(cell_name_to_coordinates("$b1"), (2, 1), "To coordinates test 2 failed")
        self.assertEquals(cell_name_to_coordinates("b$1"), (2, 1), "To coordinates test 2 failed")
        self.assertEquals(cell_name_to_coordinates("$b$1"), (2, 1), "To coordinates test 2 failed")

        self.assertEquals(cell_name_to_coordinates("$C5"), (3, 5), "To coordinates test 3 failed")
        self.assertEquals(cell_name_to_coordinates("C$5"), (3, 5), "To coordinates test 3 failed")
        self.assertEquals(cell_name_to_coordinates("$C$5"), (3, 5), "To coordinates test 3 failed")

        self.assertEquals(cell_name_to_coordinates("$ac100"), (29, 100), "To coordinates test 4 failed")
        self.assertEquals(cell_name_to_coordinates("ac$100"), (29, 100), "To coordinates test 4 failed")
        self.assertEquals(cell_name_to_coordinates("$ac$100"), (29, 100), "To coordinates test 4 failed")

        self.assertEquals(cell_name_to_coordinates("$A1   "), (1, 1), "To coordinates test 5 failed")
        self.assertEquals(cell_name_to_coordinates("A$1   "), (1, 1), "To coordinates test 5 failed")
        self.assertEquals(cell_name_to_coordinates("$A$1   "), (1, 1), "To coordinates test 5 failed")

        self.assertEquals(cell_name_to_coordinates("$She1"), (13057, 1), "To coordinates test 5 failed")
        self.assertEquals(cell_name_to_coordinates("She$1"), (13057, 1), "To coordinates test 5 failed")
        self.assertEquals(cell_name_to_coordinates("$She$1"), (13057, 1), "To coordinates test 5 failed")

        self.assertIsNone(cell_name_to_coordinates("$56G"), "To coordinates test 5 failed")
        self.assertIsNone(cell_name_to_coordinates("56$G"), "To coordinates test 5 failed")
        self.assertIsNone(cell_name_to_coordinates("$56$G"), "To coordinates test 5 failed")

        self.assertIsNone(cell_name_to_coordinates("$$A1"), "To coordinates test 6 failed")
        self.assertIsNone(cell_name_to_coordinates("A$$1"), "To coordinates test 6 failed")
        self.assertIsNone(cell_name_to_coordinates("$YTGDCJK"), "To coordinates test 6 failed")
        self.assertIsNone(cell_name_to_coordinates("546$88"), "To coordinates test 7 failed")
        self.assertIsNone(cell_name_to_coordinates(""), "To coordinates test 8 failed")
        self.assertIsNone(cell_name_to_coordinates("W0m$bat"), "To coordinates test 9 failed")
        self.assertIsNone(cell_name_to_coordinates(" $   "), "To coordinates test 10 failed")
        self.assertIsNone(cell_name_to_coordinates(";-$)"), "To coordinates test 11 failed")
        self.assertIsNone(cell_name_to_coordinates(None), "To coordinates test 12 failed")
        self.assertIsNone(cell_name_to_coordinates("$FXSHRXX$1"), "Invalid column name")
        self.assertIsNone(cell_name_to_coordinates("FXSHR$XX1"), "Invalid column name")
        self.assertIsNone(cell_name_to_coordinates("A$9223372036854775808"), "Invalid row number")


    def test_cell_ref_as_string_to_coordinates(self):
        self.assertEquals(cell_ref_as_string_to_coordinates('1, 2'), (1, 2))
        self.assertEquals(cell_ref_as_string_to_coordinates(' 10 , 2'), (10, 2))
        self.assertEquals(cell_ref_as_string_to_coordinates('(1, 2)'), (1, 2))
        self.assertEquals(cell_ref_as_string_to_coordinates(' (10 , 2)'), (10, 2))
        self.assertEquals(cell_ref_as_string_to_coordinates('J11'), (10, 11))
        self.assertIsNone(cell_ref_as_string_to_coordinates('J, 11'))
        self.assertIsNone(cell_ref_as_string_to_coordinates('blurgle'))


    def test_cell_range_as_string_to_coordinates(self):
        self.assertEquals(cell_range_as_string_to_coordinates('A2:C4'), ((1, 2), (3, 4)))
        self.assertEquals(cell_range_as_string_to_coordinates('AA10000:ZZ99999'),
                          ((27, 10000), (26 * 27, 99999)) )

        self.assertEquals(cell_range_as_string_to_coordinates('C4:A2'), ((3, 4), (1, 2)))

        self.assertIsNone(cell_range_as_string_to_coordinates('A0:C4'))
        self.assertIsNone(cell_range_as_string_to_coordinates('A2:C0'))
        self.assertIsNone(cell_range_as_string_to_coordinates('A2::C4'))
        self.assertIsNone(cell_range_as_string_to_coordinates(':A2:C4'))
        self.assertIsNone(cell_range_as_string_to_coordinates('AA:C4:'))
        self.assertIsNone(cell_range_as_string_to_coordinates('22:C4'))
        self.assertIsNone(cell_range_as_string_to_coordinates('A2:CC'))
        self.assertIsNone(cell_range_as_string_to_coordinates('A2:44'))


