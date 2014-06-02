# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

try:
    import simplejson as json
except ImportError:
    import json

try:
    import unittest2 as unittest
except ImportError:
    import sys
    assert sys.version.startswith('2.7')
    import unittest


from dirigible.sheet.ui_jsonifier import sheet_to_ui_json_grid_data, sheet_to_ui_json_meta_data

from dirigible.sheet.cell import Cell
from dirigible.sheet.models import Sheet
from dirigible.sheet.worksheet import Worksheet


class TestSheetToUIJsonGridData(unittest.TestCase):

    def test_to_ui_json_grid_zero_size(self):
        expected = {
            'bottom': 10000,
            'left': 0,
            'right': 10000,
            'topmost': 0
        }
        self.assertEquals(json.loads(sheet_to_ui_json_grid_data(Worksheet(), (0, 0, 10000, 10000))), expected)


    def test_to_ui_json_grid_ten_by_five_with_content_and_large_range(self):
        worksheet = Worksheet()
        worksheet[2, 1].formula = 'Row 1, col 2 formula'
        worksheet[2, 1].value = 'Row 1, col 2 value'
        worksheet[2, 1].formatted_value = 'Row 1, col 2 formatted value'
        worksheet[10, 1].formula = 'Row 1, col 10 formula'
        worksheet[10, 1].value = 'Row 1, col 10 value'
        worksheet[10, 1].formatted_value = 'Row 1, col 10 formatted value'
        worksheet[1, 5].formula = 'Row 5, col 1 formula'
        worksheet[1, 5].value = 'Row 5, col 1 value'
        worksheet[1, 5].formatted_value = 'Row 5, col 1 formatted value'
        worksheet[10, 5].formula = 'Row 5, col 10 formula'
        worksheet[10, 5].value = 'Row 5, col 10 value'
        worksheet[10, 5].formatted_value = 'Row 5, col 10 formatted value'
        expected_json_contents = {
            '1' : {
                '2' : {
                    "formula": 'Row 1, col 2 formula',
                    "formatted_value": "Row 1, col 2 formatted value"
                },
                '10' : {
                    "formula": 'Row 1, col 10 formula',
                    "formatted_value": "Row 1, col 10 formatted value"
                }
            },
            '5' : {
                '1' : {
                    "formula": 'Row 5, col 1 formula',
                    "formatted_value": "Row 5, col 1 formatted value"
                },
                '10' : {
                    "formula": 'Row 5, col 10 formula',
                    "formatted_value": "Row 5, col 10 formatted value"
                }
            },
            'bottom': 10000,
            'left': 0,
            'right': 10000,
            'topmost': 0
        }
        self.assertEquals(
            json.loads(sheet_to_ui_json_grid_data(worksheet, (0, 0, 10000, 10000))),
            expected_json_contents
        )


    def test_to_ui_json_grid_ten_by_five_with_content_and_small_range(self):
        worksheet = Worksheet()
        worksheet[2, 1].formula = 'Row 1, col 2 formula'
        worksheet[2, 1].value = 'Row 1, col 2 value'
        worksheet[2, 1].formatted_value = 'Row 1, col 2 formatted value'
        worksheet[10, 2].formula = 'Row 2, col 10 formula'
        worksheet[10, 2].value = 'Row 2, col 10 value'
        worksheet[10, 2].formatted_value = 'Row 2, col 10 formatted value'
        worksheet[1, 9].formula = 'Row 9, col 1 formula'
        worksheet[1, 9].value = 'Row 9, col 1 value'
        worksheet[1, 9].formatted_value = 'Row 9, col 1 formatted value'
        worksheet[10, 10].formula = 'Row 10, col 10 formula'
        worksheet[10, 10].value = 'Row 10, col 10 value'
        worksheet[10, 10].formatted_value = 'Row 10, col 10 formatted value'
        left, topmost, right, bottom = 1, 2, 10, 9
        expected_json_contents = {
            'left': left,
            'topmost': topmost,
            'right': right,
            'bottom': bottom,
            '2' : {
                '10' : {
                    "formula": 'Row 2, col 10 formula',
                    "formatted_value": "Row 2, col 10 formatted value"
                }
            },
            '9' : {
                '1' : {
                    "formula": 'Row 9, col 1 formula',
                    "formatted_value": "Row 9, col 1 formatted value"
                },
            },
        }
        self.assertEquals(
            json.loads(
                sheet_to_ui_json_grid_data(
                    worksheet, (left, topmost, right, bottom)
                )
            ),
            expected_json_contents
        )


    def test_to_ui_json_grid(self):
        self.maxDiff = None
        worksheet = Worksheet()
        left, topmost, right, bottom = 3, 4, 6, 8
        expected = {
            'left': left,
            'topmost': topmost,
            'right': right,
            'bottom': bottom,
        }
        for col in range(1, 11):
            for row in range(1, 11):
                cell_value = '(%d, %d)' % (col, row)
                worksheet[col, row].formatted_value = cell_value
                if 3 <= col <= 6  and 4 <= row <= 8:
                    if str(row) not in expected:
                        expected[str(row)] = {}
                    expected[str(row)][str(col)] = {
                        'formatted_value': cell_value
                    }
        actual = json.loads(
            sheet_to_ui_json_grid_data(worksheet, (left, topmost, right, bottom))
        )
        self.assertEquals(actual, expected)


    def test_sheet_to_ui_json_grid_data_should_not_contain_undefined_cell_values_or_empty_formatted_values(self):
        worksheet = Worksheet()
        worksheet.A1.formula = 'abc'

        expected_json_contents = {
            '1' : {
                '1' : { "formula": 'abc' },
            },
            'bottom': 10,
            'left': 0,
            'right': 10,
            'topmost': 0
        }
        self.assertEquals(json.loads(sheet_to_ui_json_grid_data(worksheet, (0, 0, 10, 10))), expected_json_contents)


    def test_sheet_to_ui_json_grid_data_should_not_contain_none_cell_formulae(self):
        worksheet = Worksheet()
        worksheet.A1.value = 123

        expected_json_contents = {
            '1' : {
                '1' : { "formatted_value": "123" },
            },
            'bottom': 10,
            'left': 0,
            'right': 10,
            'topmost': 0
        }
        self.assertEquals(json.loads(sheet_to_ui_json_grid_data(worksheet, (0, 0, 10, 10))), expected_json_contents)


    def test_sheet_to_ui_json_grid_data_should_not_include_totally_empty_cells(self):
        worksheet = Worksheet()
        worksheet.A1 = Cell()

        expected_json_contents = {
            'bottom': 10,
            'left': 0,
            'right': 10,
            'topmost': 0
        }
        self.assertEquals(json.loads(sheet_to_ui_json_grid_data(worksheet, (0, 0, 10, 10))), expected_json_contents)


    def test_to_ui_json_grid_includes_cell_errors(self):
        self.maxDiff = None
        worksheet = Worksheet()
        worksheet.A1.formula = 'an int'
        worksheet.A1.value = 123
        worksheet.A1.error = 'TestingError1'
        worksheet.B1.formula = 'an int'
        worksheet.B1.error = 'TestingError2'
        worksheet.C1.value = 123
        worksheet.C1.error = 'TestingError3'
        worksheet.D1.error = 'TestingError4'

        expected_json_contents = {
            '1' : {
                '1' : { "formula": 'an int', "error": "TestingError1" },
                '2' : { "formula": 'an int', "error": "TestingError2" },
                '3' : { "error": "TestingError3" },
                '4' : { "error": "TestingError4" },
            },
            'bottom': 10,
            'left': 0,
            'right': 10,
            'topmost': 0
        }
        self.assertEquals(json.loads(sheet_to_ui_json_grid_data(worksheet, (0, 0, 10, 10))), expected_json_contents)


class TestSheetToUIJsonMetaData(unittest.TestCase):

    def test_to_ui_json_meta_data_zero_size(self):
        sheet = Sheet(width=0, height=0)
        expected = dict(width=sheet.width, height=sheet.height, name='Untitled')
        self.assertEquals(json.loads(sheet_to_ui_json_meta_data(sheet, Worksheet())), expected)


    def test_to_ui_json_meta_data_ten_by_five_empty(self):
        sheet = Sheet(width=10, height=5)
        expected = dict(width=sheet.width, height=sheet.height, name='Untitled')
        self.assertEquals(json.loads(sheet_to_ui_json_meta_data(sheet, Worksheet())), expected)


    def test_to_ui_json_meta_data_includes_worksheet_console_text(self):
        sheet = Sheet(width=10, height=5)
        worksheet = Worksheet()
        worksheet._console_text = ['error1', 'error2']
        expected = dict(
            width=sheet.width,
            height=sheet.height,
            name='Untitled',
            console_text=worksheet._console_text)
        self.assertEquals(json.loads(sheet_to_ui_json_meta_data(sheet, worksheet)), expected)


    def test_to_ui_json_meta_data_includes_columns_widths(self):
        sheet = Sheet(width=10, height=5)
        sheet.column_widths = {u'1': 1, u'2': 22, u'3': 333}
        expected = dict(
            width=sheet.width,
            height=sheet.height,
            name='Untitled',
            column_widths=sheet.column_widths,
        )
        self.assertEquals(json.loads(sheet_to_ui_json_meta_data(sheet, Worksheet())), expected)


    def test_to_ui_json_meta_data_includes_usercode_errors(self):
        sheet = Sheet(width=10, height=5)
        worksheet = Worksheet()
        worksheet._usercode_error = {
            'message' : 'ABC',
            'line' : 123
        }
        expected_json_contents = {
            'width': sheet.width,
            'height': sheet.height,
            'name': sheet.name,
            'usercode_error' : {
                'message' : 'ABC',
                'line' : '123'
            }
        }
        self.assertEquals(json.loads(sheet_to_ui_json_meta_data(sheet, worksheet)), expected_json_contents)

