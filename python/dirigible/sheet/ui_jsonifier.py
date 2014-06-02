# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#

import simplejson as json


def sheet_to_ui_json_meta_data(sheet, worksheet):
    result = {
        'name':sheet.name,
        'width':sheet.width,
        'height':sheet.height,
    }
    if sheet.column_widths:
        result['column_widths'] = sheet.column_widths
    if worksheet._console_text:
        result['console_text'] = worksheet._console_text
    if worksheet._usercode_error:
        result['usercode_error'] = {
            'message' : worksheet._usercode_error['message'],
            'line' : str(worksheet._usercode_error['line'])
        }
    return json.dumps(result)


def sheet_to_ui_json_grid_data(worksheet, rnge):
    result = {}
    left, topmost, right, bottom = rnge
    result['left'] = left
    result['topmost'] = topmost
    result['right'] = right
    result['bottom'] = bottom
    for (col, row), cell in worksheet.items():
        if rnge is not None:
            if (
                col < left or col > right or
                row < topmost or row > bottom
            ):
                continue
        cell_content = {}
        if cell.formula is not None:
            cell_content['formula'] = cell.formula
        if cell.formatted_value and not cell.error:
            cell_content['formatted_value'] = cell.formatted_value
        if cell.error:
            cell_content['error'] = cell.error
        if cell_content != {}:
            row_dict = result.setdefault(row, {})
            row_dict[col] = cell_content
    return json.dumps(result)
