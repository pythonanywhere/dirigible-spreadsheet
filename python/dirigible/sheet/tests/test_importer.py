# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

from __future__ import with_statement

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from mock import Mock, patch
from StringIO import StringIO
import xlrd

from dirigible.test_utils import ResolverTestCase
from dirigible.sheet.importer import (
        DirigibleImportError, worksheet_from_csv, worksheet_from_excel
)
from dirigible.sheet.worksheet import Worksheet



class WorksheetFromCSVTest(ResolverTestCase):

    def test_should_put_data_into_existing_worksheet_with_offset_for_excel_and_auto(self):
        for excel_encoding in [True, False]:
            csv = StringIO()
            csv.write('abc,123\n')
            csv.write('def, \n')
            csv.size = 10
            csv.seek(0)

            existing_worksheet = Worksheet()
            for row in range(1, 6):
                for col in range(1, 5):
                    existing_worksheet[col, row].formula = 'old'

            worksheet = worksheet_from_csv(existing_worksheet, csv, 2, 3, excel_encoding)

            self.assertEquals(worksheet.A1.formula, 'old')
            self.assertEquals(worksheet.B1.formula, 'old')
            self.assertEquals(worksheet.A2.formula, 'old')
            self.assertEquals(worksheet.B3.formula, 'abc')
            self.assertEquals(worksheet.C3.formula, '123')
            self.assertEquals(worksheet.B4.formula, 'def')
            self.assertEquals(worksheet.C4.formula, ' ')
            self.assertEquals(worksheet.C5.formula, 'old')
            self.assertEquals(worksheet.D3.formula, 'old')
            self.assertEquals(worksheet.B5.formula, 'old')


    def test_excel_csv_import_recognises_accents_and_currency_symbols(self):
        excel_csv = StringIO()
        excel_csv.write(u"\xe9".encode('windows-1252'))
        excel_csv.write(u"\xa3".encode('windows-1252'))
        excel_csv.write(u"\u20ac".encode('windows-1252'))
        excel_csv.name = 'filename'
        excel_csv.size = 10
        excel_csv.seek(0)

        worksheet = worksheet_from_csv(Worksheet(), excel_csv, 3, 4, True)

        self.assertEquals(worksheet.C4.formula, u"\xe9\xa3\u20ac")



    def test_excel_csv_import_handles_carriage_returns_in_cells(self):
        excel_csv = StringIO()
        excel_csv.write(u'"carriage\nreturn!"\r\n'.encode('windows-1252'))
        excel_csv.write(u"normal line\r\n".encode('windows-1252'))
        excel_csv.name = 'filename'
        excel_csv.size = 10
        excel_csv.seek(0)

        worksheet = worksheet_from_csv(Worksheet(), excel_csv, 2, 3, True)

        self.assertEquals(worksheet.B3.formula, "carriage\nreturn!")
        self.assertEquals(worksheet.B4.formula, "normal line")


    def test_autodetect_csv_import_handles_carriage_returns_in_cells(self):
        excel_csv = StringIO()
        excel_csv.write(u'"carriage\nreturn!"\r\n'.encode('utf-8'))
        excel_csv.write(u"normal line\r\n".encode('utf-8'))
        excel_csv.name = 'filename'
        excel_csv.size = 10
        excel_csv.seek(0)

        worksheet = worksheet_from_csv(Worksheet(), excel_csv, 2, 3, False)

        self.assertEquals(worksheet.B3.formula, "carriage\nreturn!")
        self.assertEquals(worksheet.B4.formula, "normal line")


    def test_autodetect_can_handle_japanese_utf8(self):
        some_kanji = u'\u65b0\u4e16\u7d00\u30a8\u30f4\u30a1\u30f3\u30b2\u30ea\u30aa\u30f3'
        japanese_file = StringIO()
        japanese_file.write(some_kanji.encode('utf-8'))
        japanese_file.name = 'filename'
        japanese_file.size = 10
        japanese_file.seek(0)

        worksheet = worksheet_from_csv(Worksheet(), japanese_file, 1, 1, False)

        self.assertEquals(worksheet.A1.formula, some_kanji)


    def test_excel_csv_import_survives_japanes_utf8(self):
        some_kanji = u'\u65b0\u4e16\u7d00\u30a8\u30f4\u30a1\u30f3\u30b2\u30ea\u30aa\u30f3'
        japanese_file = StringIO()
        japanese_file.write(some_kanji.encode('utf-8'))
        japanese_file.name = 'filename'
        japanese_file.size = 10
        japanese_file.seek(0)

        worksheet_from_csv(Worksheet(), japanese_file, 1, 1, True)
        #should not raise


    def test_import_excel_csv_raises_on_null_bytes(self):
        bin_file = StringIO()
        bin_file.write("\xFF\x00\xFF")
        bin_file.name = 'filename'
        bin_file.size = 10
        bin_file.seek(0)

        self.assertRaises(DirigibleImportError,
                lambda : worksheet_from_csv(Worksheet(), bin_file, 2, 1, True)
        )

    def test_autodetect_import_csv_raises_on_null_bytes(self):
        bin_file = StringIO()
        bin_file.write("\xFF\x00\xFF")
        bin_file.name = 'filename'
        bin_file.size = 10
        bin_file.seek(0)

        self.assertRaises(DirigibleImportError,
                lambda : worksheet_from_csv(Worksheet(), bin_file, 1, 1, False)
        )


    @patch('dirigible.sheet.importer.UniversalDetector')
    def test_autodetect_import_csv_raises_on_failure_to_detect_encoding(
            self, mock_UniversalDetector
    ):
        mock_detector = Mock()
        mock_UniversalDetector.return_value = mock_detector
        mock_detector.result = {'encoding':None}

        mock_file = StringIO()
        mock_file.write("\xFF\x00\xFF")
        mock_file.name = 'filename'
        mock_file.size = 10

        self.assertRaises(DirigibleImportError,
                lambda : worksheet_from_csv(Worksheet(), mock_file, 1, 1, False)
        )



class WorksheetFromExcelTest(ResolverTestCase):

    def test_populates_worksheet_formulae_from_excel_values(self):
        mock_excel_worksheet = Mock()
        def mock_cell(row, col):
            mock_cell = Mock()
            mock_cell.value = '%s, %s' % (col, row)
            return mock_cell
        mock_excel_worksheet.cell.side_effect = mock_cell
        mock_excel_worksheet.nrows = 4
        mock_excel_worksheet.ncols = 3

        worksheet = worksheet_from_excel(mock_excel_worksheet)

        for col in range(mock_excel_worksheet.ncols):
            for row in range(mock_excel_worksheet.nrows):
                self.assertEquals(worksheet[col + 1, row + 1].formula, '%s, %s' % (col, row))


    def test_populates_worksheet_handles_float_source_values(self):
        mock_excel_worksheet = Mock()
        def mock_cell(row, col):
            mock_cell = Mock()
            mock_cell.value = col + row + 0.1
            return mock_cell
        mock_excel_worksheet.cell.side_effect = mock_cell
        mock_excel_worksheet.nrows = 4
        mock_excel_worksheet.ncols = 3

        worksheet = worksheet_from_excel(mock_excel_worksheet)

        for col in range(mock_excel_worksheet.ncols):
            for row in range(mock_excel_worksheet.nrows):
                self.assertEquals(worksheet[col + 1, row + 1].formula, '%s' % (col + row + 0.1, ))


    @patch('dirigible.sheet.importer.xldate_as_tuple')
    def test_converts_excel_dates_to_python_datetime(self, mock_xlrd_date_as_tuple):
        mock_excel_worksheet = Mock()
        def mock_cell(row, col):
            mock_cell = Mock()
            mock_cell.ctype = xlrd.XL_CELL_DATE
            mock_cell.value = (row, col)
            return mock_cell
        mock_excel_worksheet.cell.side_effect = mock_cell
        mock_excel_worksheet.nrows = 4
        mock_excel_worksheet.ncols = 3

        def mock_xlrd_date_as_tuple_function(cell_value, datemode):
            row, col = cell_value
            self.assertEquals(datemode, mock_excel_worksheet.book.datemode)
            return (2011, row, col, 1, 2, 3)
        mock_xlrd_date_as_tuple.side_effect = mock_xlrd_date_as_tuple_function

        worksheet = worksheet_from_excel(mock_excel_worksheet)

        for col in range(mock_excel_worksheet.ncols):
            for row in range(mock_excel_worksheet.nrows):
                self.assertEquals(
                        worksheet[col + 1, row + 1].formula,
                        '=DateTime(2011, %s, %s, 1, 2, 3)' % (row, col)
                )


    @patch('dirigible.sheet.importer.xldate_as_tuple')
    def test_handles_excel_errors(self, mock_xlrd_date_as_tuple):
        mock_excel_worksheet = Mock()
        errors = {
                (0,0) : (0x0, '=#NULL!'),
                (1,0) : (0x7, '=#DIV/0!'),
                (2,0) : (0xf, '=#VALUE!'),
                (3,0) : (0x17, '=#REF!'),
                (4,0) : (0x1d, '=#NAME?'),
                (5,0) : (0x24, '=#NUM!'),
                (6,0) : (0x2a, '=#N/A'),

        }
        def mock_cell(row, col):
            mock_cell = Mock()
            mock_cell.ctype = xlrd.XL_CELL_ERROR
            mock_cell.value = errors[row, col][0]
            return mock_cell
        mock_excel_worksheet.cell.side_effect = mock_cell
        mock_excel_worksheet.nrows = 7
        mock_excel_worksheet.ncols = 1

        worksheet = worksheet_from_excel(mock_excel_worksheet)

        for col in range(mock_excel_worksheet.ncols):
            for row in range(mock_excel_worksheet.nrows):
                self.assertEquals(
                        worksheet[col + 1, row + 1].formula,
                        errors[row, col][1]
                )

