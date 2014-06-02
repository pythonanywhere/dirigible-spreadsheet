# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

from chardet.universaldetector import UniversalDetector
from codecs import getreader
import csv
from xlrd import (
    error_text_from_code, xldate_as_tuple, XL_CELL_DATE, XL_CELL_ERROR,
)
from worksheet import Worksheet

class DirigibleImportError(Exception):
    pass


def worksheet_from_csv(
    worksheet, csv_file, start_column, start_row, excel_encoding
):

    def autodetect_encoding(csv_file):
        detector = UniversalDetector()
        for line in csv_file.readlines():
            detector.feed(line)
            if detector.done: break
        detector.close()
        csv_file.seek(0)
        encoding = detector.result['encoding']

        if not encoding:
            raise DirigibleImportError('could not recognise encoding')

        return encoding

    def unicode_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):
        # csv.py doesn't do Unicode; encode temporarily as UTF-8:
        csv_reader = csv.reader(utf_8_encoder(unicode_csv_data),
                                dialect=dialect, **kwargs)
        for row in csv_reader:
            # decode UTF-8 back to Unicode, cell by cell:
            yield [unicode(cell, 'utf-8') for cell in row]

    def utf_8_encoder(unicode_csv_data):
        for line in unicode_csv_data:
            yield line.encode('utf-8')


    if excel_encoding:
        encoding = 'windows-1252'
    else:
        encoding = autodetect_encoding(csv_file)
    unicode_translated_csv_file = getreader(encoding)(csv_file)

    row = start_row
    try:
        for csv_row in unicode_csv_reader(unicode_translated_csv_file):
            column = start_column
            for csv_cell in csv_row:
                worksheet[column, row].formula = unicode(csv_cell)
                column += 1
            row += 1
    except Exception, e:
        raise DirigibleImportError(unicode(e))

    return worksheet


def worksheet_from_excel(excel_sheet):
    worksheet = Worksheet()
    for col in range(excel_sheet.ncols):
        for row in range(excel_sheet.nrows):
            cell = excel_sheet.cell(row, col)
            if cell.ctype == XL_CELL_ERROR:
                formula = '=%s' % (error_text_from_code[cell.value], )
            elif cell.ctype == XL_CELL_DATE:
                formula = '=DateTime(%s, %s, %s, %s, %s, %s)' % xldate_as_tuple(
                    cell.value, excel_sheet.book.datemode)
            else:
                formula = unicode(excel_sheet.cell(row, col).value)
            worksheet[col + 1, row + 1].formula = formula
    return worksheet

