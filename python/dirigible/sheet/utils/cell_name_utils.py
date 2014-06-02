# Copyright (c) 2005-2009 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

import sys

# We allow 3 letter column names
MAX_COL = (26 ** 3) + (26 ** 2) + 26

def column_name_to_index(colName):
    if not colName.isalpha():
        return None

    result = 0
    for letter in colName.upper():
        result *= 26
        result += ord(letter) - ord("A") + 1
    if result > MAX_COL:
        return None
    return result

def column_index_to_name(index):
    if index > MAX_COL:
        return None

    result = ""
    while index > 0:
        thisChar = chr((index - 1) % 26 + ord("A"))
        index = (index - 1) // 26
        result = thisChar + result

    return result


def _col_row_names_to_coordinates(col, row):
    if not row or row == "0" or not col:
        return None
    colIndex = column_name_to_index(col)
    rowIndex = int(row)
    if not colIndex or rowIndex > sys.maxint:
        return None
    return (colIndex, rowIndex)


def coordinates_to_cell_name(col, row, colAbsolute=False, rowAbsolute=False):
    if col < 1 or col > MAX_COL or row < 1:
        return None
    colPrefix = '$' * colAbsolute
    rowPrefix = '$' * rowAbsolute
    return colPrefix + column_index_to_name(col) + rowPrefix + str(row)


def cell_name_to_coordinates(cellName):
    if not cellName:
        return None

    if cellName.startswith("$"):
        cellName = cellName[1:]

    row = ""
    col = ""

    dollarSeen = False

    for c in cellName.rstrip():
        if c.isalpha():
            if row:
                return None
            else:
                col += c
        elif c == "$":
            if dollarSeen or not col or row:
                return None
            dollarSeen = True
        elif c.isdigit():
            if not col:
                return None
            else:
                row += c
        else:
            return None

    return _col_row_names_to_coordinates(col, row)


def cell_ref_as_string_to_coordinates(cell_ref):
    cell_ref = cell_ref.replace('(', '').replace(')', '')
    if ',' in cell_ref:
        try:
            return tuple(map(int, cell_ref.split(',')))
        except ValueError:
            return None
    else:
        return cell_name_to_coordinates(cell_ref)



def cell_range_as_string_to_coordinates(cell_range_string):
    parts = cell_range_string.split(':')
    if len(parts) != 2:
        return None
    str_start, str_end = parts
    start = cell_name_to_coordinates(str_start)
    end = cell_name_to_coordinates(str_end)
    if start is None or end is None:
        return None
    else:
        return start, end
